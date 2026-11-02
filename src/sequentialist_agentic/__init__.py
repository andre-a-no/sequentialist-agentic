"""Sequentialist Agentic: application tools and decision policies for agents.

Надстройка над ядром sequential-search (пакет `sequentialist_agentic`): узлы =
инструменты агента, рёбра = статистические правила остановки, обход =
cost-aware стратегия. Статистические гарантии требуют валидного процесса улик
и обоснованного учёта бюджета; mock-оценщик таких гарантий не предоставляет.
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
