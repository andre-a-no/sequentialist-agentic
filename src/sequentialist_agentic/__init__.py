"""Sequentialist Agentic: Statistically guaranteed AI agent decisions.

Надстройка над ядром sequential-search (пакет `sequential_search`): узлы =
инструменты агента, рёбра = статистические правила остановки, обход =
cost-aware стратегия с глобальным бюджетом α.
"""

from sequentialist_agentic.evidence import (
    LLMDiscriminator,
    LogLRRollup,
    heuristic_relevance_discriminator,
)
from sequentialist_agentic.nodes import (
    LLMSearchNode,
    ReadDocumentNode,
    SearchObservation,
    canonicalize_query,
)
from sequentialist_agentic.policies import CostFirstPolicy, RoundRobinPolicy
from sequentialist_agentic.traversal import AgentTraversal, TraversalResult

__version__ = "0.1.0"

__all__ = [
    "AgentTraversal",
    "CostFirstPolicy",
    "LLMDiscriminator",
    "LLMSearchNode",
    "LogLRRollup",
    "ReadDocumentNode",
    "RoundRobinPolicy",
    "SearchObservation",
    "TraversalResult",
    "canonicalize_query",
    "heuristic_relevance_discriminator",
]
