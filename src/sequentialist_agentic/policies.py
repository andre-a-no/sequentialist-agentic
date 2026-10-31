"""Политики обхода (guarantee-invariant): влияют на ПОРЯДОК, но не на решения.

Согласно ADR-003 (слой 4) ядра sequential-search политика обязана вызывать
эксперименты и читать edge.decide(), но не имеет права порождать решения сама.
Ниже — две стартовые политики для агентов:

* CostFirstPolicy — жадный выбор самого дешёвого доступного узла из frontier
  (экономия токенов/API-вызовов при сохранении гарантии α);
* RoundRobinPolicy — честное ротирование открытых веток (полезно при
  cooperative search, чтобы ни одна ветка не голодала).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sequential_search.core.graph import SearchGraph
from sequential_search.policy.base import Budgets


@dataclass
class CostFirstPolicy:
    """Жадная cost-aware политика: следующий узел — самый дешёвый из affordable.

    Инвариант B1: узел, стоимость которого превышает cost_left, в выборку не
    попадает (его судьба — WITHDRAW на уровне traversal, не здесь).
    """

    graph: SearchGraph

    def next_node(self, frontier: Sequence[str], budgets: Budgets) -> str | None:
        affordable = [k for k in frontier if budgets.can_afford(self.graph.node(k).cost())]
        if not affordable:
            return None  # остановка по бюджету — НЕ вывод о данных
        return min(affordable, key=lambda k: self.graph.node(k).cost())


@dataclass
class RoundRobinPolicy:
    """FIFO-ротация frontier: первый незанятый узел."""

    graph: SearchGraph

    def next_node(self, frontier: Sequence[str], budgets: Budgets) -> str | None:
        for k in frontier:
            if budgets.can_afford(self.graph.node(k).cost()):
                return k
        return None
