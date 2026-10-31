"""Сквозной пример: ИИ-агент информационного поиска на ядре sequential-search.

Граф: root -> два поисковых узла (разные запросы), каждое ребро — пороговое
правило остановки над накопленным logLR (e-value). Бюджет: α и стоимость
двумерны (Budgets ядра) и не конвертируются друг в друга.

Запуск:  python examples/search_agent_demo.py
"""
from __future__ import annotations

import math

from sequential_search.core.edge import Edge, threshold_rule
from sequential_search.core.graph import SearchGraph
from sequential_search.policy.base import Budgets

from sequentialist_agentic import (
    AgentTraversal,
    CostFirstPolicy,
    LLMSearchNode,
    heuristic_relevance_discriminator,
)

# --- mock-инструменты (замените на реальные API/LLM) -----------------------
# (snippets, exhausted) — узел терминален, когда выдачи исчерпаны
CORPUS = {
    "квантовые вычисления": (
        [
            "Квантовые компьютеры используют суперпозицию...",
            "Адиабатические квантовые вычисления решают оптимизацию...",
        ],
        True,  # второй вызов того же запроса больше ничего не даст
    ),
    "нейросети трансформеры": (["Трансформеры — архитектура на self-attention..."], True),
}


def mock_search(query: str) -> tuple[list[str], bool]:
    """Пагинация: каждый вызов выдаёт СЛЕДУЮЩИЙ документ; exhausted на последнем."""
    for topic, (docs, _) in CORPUS.items():
        if any(word in query.lower() for word in topic.split()):
            i = _CALLS[topic] = _CALLS.get(topic, -1) + 1
            if i >= len(docs):
                return [], True
            return [docs[i]], i == len(docs) - 1
    return [], True


_CALLS: dict[str, int] = {}


def mock_scorer(query: str, snippet: str) -> float:
    return 0.9 if "квантов" in snippet.lower() else 0.2


def build_graph() -> tuple[SearchGraph, dict[str, str]]:
    graph = SearchGraph(root="root")

    # корневой узел — фиктивный «план» (нулевая стоимость, всегда terminal=False)
    class RootNode:
        name = "root"

        def step(self):
            from sequential_search.core.node import Observation

            return Observation(t=1, values={})

        def state(self):
            return {}

        def cost(self):
            return 0.0

        def canonical_key(self):
            return "root"

        def is_terminal(self):
            return False

    graph.add_node(RootNode())

    n1 = LLMSearchNode(
        "web-search", mock_search, scorer=mock_scorer, cost_per_step=150.0
    )
    n1.set_query("квантовые вычисления обзор")
    k1 = graph.add_node(n1)

    n2 = LLMSearchNode(
        "web-search", mock_search, scorer=mock_scorer, cost_per_step=150.0
    )
    n2.set_query("нейросети трансформеры")
    k2 = graph.add_node(n2)

    # Порог accept: e >= 20  (~ α_edge <= 0.05 по неравенству Вилля)
    accept_threshold = 20.0
    graph.add_edge(Edge(source="root", target=k1, rule=threshold_rule(accept_threshold, None),
                        label="branch: quantum"))
    graph.add_edge(Edge(source="root", target=k2, rule=threshold_rule(accept_threshold, None),
                        label="branch: transformers"))
    return graph, {k1: "квантовые вычисления обзор", k2: "нейросети трансформеры"}


def main() -> None:
    graph, queries = build_graph()
    budgets = Budgets(alpha_left=0.05, cost_left=600.0)
    traversal = AgentTraversal(
        graph,
        discriminator=heuristic_relevance_discriminator(),
        budgets=budgets,
        policy=CostFirstPolicy(graph),
    )
    result = traversal.run(start_queries=queries)

    print(f"Итог:      {result.decision.value if result.decision else '—'} ({result.label})")
    print(f"Шагов:     {result.steps}, стоимость: {result.spent_cost:.0f}, "
          f"остаток бюджета: {traversal.budgets.cost_left:.0f}")
    stat = result.evidence.stat
print(f"Улики:     e-value={result.evidence.e:.3f}" + (f" (logLR={stat:.3f})" if stat is not None else ""))
    for h in result.history:
        print(f"  - {h['edge']}: t={h['t']} e={h['e_value']} -> {h['decision']}")


if __name__ == "__main__":
    main()
