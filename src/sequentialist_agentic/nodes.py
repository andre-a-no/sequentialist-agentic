from typing import Protocol, Any
from pydantic import BaseModel

# Эти импорты будут реальными, когда мы подключим sequential-search
# from sequential_search.core.node import Node, Observation, EvidenceState


class SearchObservation(BaseModel):
    """Результат одного шага информационного поиска."""

    query: str
    snippets: list[str]
    metadata: dict[str, Any]
    cost_tokens: int


class LLMSearchNode:
    """
    Пример узла, адаптирующего вызов поискового инструмента или LLM
    под онтологию sequential-search.
    """

    def __init__(self, tool_name: str, base_cost: int = 100):
        self.tool_name = tool_name
        self.base_cost = base_cost
        self._state = "initial"

    @property
    def cost(self) -> int:
        """Стоимость эксперимента (например, в токенах или миллисекундах)."""
        return self.base_cost

    def step(self, context: Any = None) -> SearchObservation:
        """
        Выполняет один шаг эксперимента (например, вызов API поиска).
        Возвращает Observation для последующей оценки на ребре (Edge).
        """
        # TODO: Здесь будет реальный вызов инструмента
        # observation = call_search_api(context)

        return SearchObservation(
            query="пример запроса",
            snippets=["результат 1", "результат 2"],
            metadata={"source": "mock"},
            cost_tokens=self.base_cost,
        )

    def state(self) -> str:
        """Возвращает текущее состояние накопленных улик (EvidenceState)."""
        return self._state
