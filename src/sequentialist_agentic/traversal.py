"""Traversal: обход графа агентом поверх примитивов ядра sequential-search.

Ядро даёт онтологию (Node/Edge/SearchGraph/Budgets), но не готовый цикл —
здесь собирается минимальный исполнительный контур агента:

    edge = frontier-ребро                     # политика выбирает ПОРЯДОК
      -> node.step()                          # эксперимент (узел-инструмент)
      -> discriminator(values)                # оценка -> инкремент logLR
      -> rollup.feed(...).evidence()          # накопленные улики (immutable)
      -> edge.decide(evidence)                # accept / reject / pending (E1)

Соответствия инвариантам README ядра:
  * guarantee-invariant: решения принимает только Edge.decide от улик ребра;
    политика влияет лишь на порядок накопления (ADR-003, слой 4);
  * no double counting: улики хранятся в rollup'ах под canonical_key узла —
    повторный вход в тот же эксперимент переиспользует накопленное;
  * учёт стоимости: каждый шаг резервируется и списывается через Budgets
    (B1 — непревышение), но стоимость никогда не влияет на decide();
  * WITHDRAW порождается только здесь (cost-to-go), а не правилом (E4):
    если следующий шаг не влезает в бюджет — ветка приостанавливается;
  * возврат α (ADR-005 следствие 2): ребро, закрытое БЕЗ вынесения
    reject/accept (pending по исчерпанному ресурсу или terminal-узел),
    возвращает свой α-резерв в пул; REJECT резерв расходует (это ошибка),
    ACCEPT — тоже (вывод вынесен).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sequential_search.core.edge import Decision, EvidenceState
from sequential_search.core.graph import SearchGraph
from sequential_search.policy.base import Budgets, Policy

from sequentialist_agentic.evidence import Discriminator, LogLRRollup


@dataclass
class TraversalResult:
    decision: Decision | None          # терминальное решение (None = стоп по бюджету)
    label: str                         # человекочитаемая метка исхода
    evidence: EvidenceState            # накопленные улики финального ребра
    steps: int                         # сколько наблюдений собрано
    spent_cost: float                  # израсходованный ресурс
    alpha_spent: float                 # суммарно использованный α (без refund'ов)
    history: list[dict[str, Any]] = field(default_factory=list)


class AgentTraversal:
    """Обход root -> уровень рёбер-кандидатов с углублением до терминации.

    MVP обслуживает каскад фильтров и дерево гипотез первого уровня
    (branch-and-bound): все out-рёбра корня проверяются по очереди, каждое
    углубляется accumulation'ом улик пока pending. Multi-frontier/DFS-BFS
    произвольной глубины — следующая итерация.
    """

    def __init__(
        self,
        graph: SearchGraph,
        *,
        discriminator: Discriminator,
        budgets: Budgets,
        policy: Policy | None = None,
        max_steps: int = 32,
    ) -> None:
        self._graph = graph
        self._disc = discriminator
        self._budgets = budgets
        self._policy = policy
        self._max_steps = max_steps
        #: canonical_key -> накопитель улик (один rollup на эксперимент, no double counting)
        self._rollups: dict[str, LogLRRollup] = {}
        self._spent = 0.0
        self._alpha_spent = 0.0
        self._history: list[dict[str, Any]] = []

    @property
    def budgets(self) -> Budgets:
        return self._budgets

    @property
    def alpha_spent(self) -> float:
        return self._alpha_spent

    def _rollup(self, key: str) -> LogLRRollup:
        return self._rollups.setdefault(key, LogLRRollup())

    def run(self, start_queries: dict[str, str] | None = None) -> TraversalResult:
        """Выполнить обход от корня графа.

        start_queries: canonical_key -> query для узлов, которым нужен план
        (LLMSearchNode.set_query).
        """
        root = self._graph.root
        edges_out = list(self._graph.out_edges(root))
        if not edges_out:
            return TraversalResult(None, "dead-end", EvidenceState(e=1.0), 0, 0.0, 0.0)

        # α резервируется поровну на открытые рёбра (упрощение MVP; корректная
        # калибровка e-values по Bonferroni/Hedged-max — отдельный модуль stats).
        share = self._budgets.alpha_left / len(edges_out)

        if self._policy is not None:
            frontier = [e.target for e in edges_out]
            ordered: list[Any] = []
            remaining = {e.target: e for e in edges_out}
            while remaining:
                nxt = self._policy.next_node(list(remaining), self._budgets)
                if nxt is None:
                    break  # остановка по бюджету — НЕ вывод о данных
                ordered.append(remaining.pop(nxt))
            # недоступные политикой рёбра остаются непроверенными (withdrawn)
            for k in remaining:
                self._record(root, k, "withdraw", {"reason": "policy-stop"})
        else:
            ordered = edges_out

        step = 0
        for edge in ordered:
            target_key = edge.target
            node = self._graph.node(target_key)

            if start_queries and hasattr(node, "set_query") and target_key in start_queries:
                node.set_query(start_queries[target_key])

            # --- cost-to-go: WITHDRAW вне правила остановки (E4) ---------
            next_cost = node.cost()
            if not self._budgets.can_afford(next_cost):
                self._record(edge.source, target_key, "withdraw", {"reason": "cost-to-go"})
                continue

            # резерв α под ребро и стоимости шага (B1 проверяет reserve сам)
            self._budgets = self._budgets.reserve(share, next_cost)

            # --- накопление улик до терминации ребра ---------------------
            decision = Decision.PENDING
            evidence = self._rollup(target_key).evidence()
            stopped_by_resource = False
            while True:
                if node.is_terminal():
                    # данных больше нет: финальное решение по накопленным уликам
                    decision = edge.decide(evidence)
                    self._record(edge.source, target_key, decision.value,
                                 {"reason": "node-terminal"}, evidence=evidence)
                    break
                obs = node.step()
                step += 1
                self._spent += next_cost
                # стоимость шага потреблена: снимаем с резерва (left не менялся)
                self._budgets = Budgets(
                    alpha_left=self._budgets.alpha_left,
                    cost_left=self._budgets.cost_left,
                    alpha_reserved=self._budgets.alpha_reserved,
                    cost_reserved=max(0.0, self._budgets.cost_reserved - next_cost),
                )
                increment, meta = self._disc(obs.values, context=None)
                evidence = self._rollup(target_key).feed(increment).evidence()
                decision = edge.decide(evidence)  # только Edge решает (E1)!
                self._record(edge.source, target_key, decision.value, meta,
                             evidence=evidence, t=obs.t)
                if decision is not Decision.PENDING:
                    break
                # ещё один шаг? нужны бюджет и глубина
                next_cost = node.cost()
                if step >= self._max_steps or not self._budgets.can_afford(next_cost):
                    # pending по исчерпанному ресурсу — НЕ вывод о данных
                    stopped_by_resource = True
                    break
                self._budgets = self._budgets.reserve(0.0, next_cost)

            # --- закрытие ребра: α либо расходуется, либо возвращается ----
            if decision is Decision.ACCEPT:
                self._consume_alpha(share)
                self._release_cost_reserve()
                return TraversalResult(
                    decision, f"answer found via {edge.label or target_key}",
                    evidence, step, self._spent, self._alpha_spent, self.history_list(),
                )
            if decision is Decision.REJECT:
                self._consume_alpha(share)
                self._release_cost_reserve()
                continue  # след. кандидат на том же уровне (branch-and-bound)

            # PENDING без решения: остановка по бюджету — НЕ reject.
            # Возвращаем в пул α-резерв ребра и незатраченную стоимость (ADR-005/006).
            self._budgets = self._budgets.refund(share, self._budgets.cost_reserved)
            if stopped_by_resource:
                # одно продолжение этой ветки позже (RESUME) возможно: улики
                # сохранены в rollup, резерв возвращён — выходим в глобальный стоп
                return TraversalResult(
                    None, "pending: budget exhausted, branch resumable", evidence,
                    step, self._spent, self._alpha_spent, self.history_list(),
                )
            continue  # terminal-узел с pending: переходим к следующему ребру

        # все рёбра закрыты reject/withdraw без accept
        any_reject = any(h.get("decision") == "reject" for h in self._history)
        return TraversalResult(
            Decision.REJECT if any_reject else None,
            "no branch produced sufficient evidence",
            EvidenceState(e=1.0), step, self._spent, self._alpha_spent,
            self.history_list(),
        )

    # --- вспомогательное ---------------------------------------------------
    def _consume_alpha(self, share: float) -> None:
        """Резерв α превращается в невозвратный расход (вывод вынесен)."""
        self._budgets = Budgets(
            alpha_left=self._budgets.alpha_left,
            cost_left=self._budgets.cost_left,
            alpha_reserved=max(0.0, self._budgets.alpha_reserved - share),
            cost_reserved=self._budgets.cost_reserved,
        )
        self._alpha_spent += share

    def _release_cost_reserve(self) -> None:
        """Освобождает зарезервированную, но не потреблённую стоимость шага."""
        reserved = self._budgets.cost_reserved
        if reserved > 0:
            self._budgets = Budgets(
                alpha_left=self._budgets.alpha_left,
                cost_left=self._budgets.cost_left + reserved,
                alpha_reserved=self._budgets.alpha_reserved,
                cost_reserved=0.0,
            )

    def _record(self, source: str, target: str, decision: str, meta: dict[str, Any],
                *, evidence: EvidenceState | None = None, t: int = 0) -> None:
        self._history.append({
            "edge": f"{source}->{target}",
            "t": t,
            "loglr": evidence.stat if evidence else None,
            "e_value": round(evidence.e, 4) if evidence else 1.0,
            "decision": decision,
            "meta": meta,
        })

    def history_list(self) -> list[dict[str, Any]]:
        return list(self._history)
