"""Узлы ИИ-агента, реализующие протокол `sequential_search.core.node.Node`.

Node (ADR-001 ядра) = эксперимент: шаг порождает Observation, состояние
неизменяемо, стоимость следующего шага известна заранее. Здесь этот контракт
реализуют инструменты агента: веб-поиск, чтение документа, вызов LLM.

Инварианты ядра, проверяемые здесь:
  N1 step() возвращает новый Observation; состояние — immutable value.
  N2 cost() >= 0 и конечна (стоимость следующего шага).
  N3 canonical_key() уникален для эксперимента (no double counting): два
     запроса с одинаковой канонической формой запроса — ОДИН эксперимент.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Callable, Sequence

from pydantic import BaseModel, Field
from sequential_search.core.node import Observation, check_node


class SearchObservation(BaseModel):
    """Результат одного шага информационного поиска (данные до оценки)."""

    query: str
    snippets: list[str] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)  # релевантность [0..1], если есть
    metadata: dict[str, Any] = Field(default_factory=dict)
    cost_tokens: int = 0

    def as_mapping(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "snippets": list(self.snippets),
            "scores": list(self.scores),
            "metadata": dict(self.metadata),
        }


def canonicalize_query(query: str) -> str:
    """Нормализация запроса для canonical_key (N3): lowercase, whitespace, пункты."""
    q = re.sub(r"[^\w\s]", "", query.lower())
    return re.sub(r"\s+", " ", q).strip()


SearchTool = Callable[[str], Sequence[str]]
ScoreTool = Callable[[str, str], float]


class LLMSearchNode:
    """Узел = вызов поискового инструмента поверх протокола Node ядра.

    Параметры
    ---------
    name: имя эксперимента (например "web-search").
    tool: callable(query) -> список сниппетов (заглушка или реальный API).
    scorer: необязательная функция (query, snippet) -> relevance [0..1].
    cost_per_step: стоимость следующего шага в токенах/у.е. (N2).
    key: канонический ключ; по умолчанию вычисляется из нормализованного
        последнего запроса — повторный вход с тем же запросом дедуплицируется
        графом (инвариант no double counting).
    """

    def __init__(
        self,
        name: str,
        tool: SearchTool | Callable[[str], tuple[Sequence[str], bool]],
        *,
        scorer: ScoreTool | None = None,
        cost_per_step: float = 150.0,
        key: str | None = None,
    ) -> None:
        if cost_per_step < 0:
            raise ValueError("cost_per_step must be non-negative (N2)")
        self.name = name
        self._raw_tool = tool
        self._scorer = scorer
        self._cost = float(cost_per_step)
        self._explicit_key = key
        self._t = 0
        self._last: SearchObservation | None = None
        self._pending_query: str | None = None
        self._exhausted = False

    # --- управление планом (внешний источник данных шага) --------------
    def set_query(self, query: str) -> None:
        """Задать запрос для СЛЕДУЮЩЕГО шага (политика планирует, узел исполняет)."""
        self._pending_query = query
        self._exhausted = False

    # --- протокол Node ---------------------------------------------------
    def step(self) -> Observation:
        if self._pending_query is None:
            raise RuntimeError(f"node '{self.name}': no pending query; call set_query() first")
        if self._exhausted:
            raise RuntimeError(f"node '{self.name}': terminal, further steps forbidden")
        result = self._raw_tool(self._pending_query)
        if isinstance(result, tuple):
            snippets, exhausted = result
        else:
            snippets, exhausted = result, False
        scores = (
            [max(0.0, min(1.0, self._scorer(self._pending_query, s))) for s in snippets]
            if self._scorer is not None
            else []
        )
        obs = SearchObservation(
            query=self._pending_query,
            snippets=list(snippets),
            scores=scores,
            metadata={"source": self.name},
            cost_tokens=int(self._cost),
        )
        self._t += 1
        self._last = obs
        self._exhausted = bool(exhausted)
        return Observation(t=self._t, values=obs.as_mapping())

    def state(self) -> dict[str, Any] | None:
        """Текущее состояние как immutable value (для чекпоинтинга)."""
        if self._last is None:
            return None
        return self._last.model_dump()

    def cost(self) -> float:
        return self._cost

    def canonical_key(self) -> str:
        if self._explicit_key is not None:
            return self._explicit_key
        basis = self._last.query if self._last else (self._pending_query or self.name)
        digest = hashlib.sha256(canonicalize_query(basis).encode()).hexdigest()[:16]
        return f"{self.name}:{digest}"

    def is_terminal(self) -> bool:
        return self._exhausted

    # --- convenience ------------------------------------------------------
    @property
    def last_observation(self) -> SearchObservation | None:
        return self._last


class ReadDocumentNode(LLMSearchNode):
    """Чтение конкретного документа: key фиксирован doc_id, стоимость выше."""

    def __init__(self, doc_id: str, reader: Callable[[str], Sequence[str]], **kw: Any) -> None:
        kw.setdefault("cost_per_step", 400.0)
        super().__init__(name=f"read:{doc_id}", tool=reader, key=f"doc:{doc_id}", **kw)


def assert_contract(node: Any) -> None:
    """Проверить инварианты N1–N3 ядра на узле (бросает ValueError)."""
    check_node(node)
