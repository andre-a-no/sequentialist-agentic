"""
Пример агента, который ищет информацию, используя статистические гарантии остановки.
"""

from sequentialist_agentic.nodes import LLMSearchNode


def main():
    print("Инициализация ИИ-агента с последовательным статистическим контролем...")

    # 1. Создаём узел (инструмент)
    search_node = LLMSearchNode(tool_name="web_search", base_cost=150)

    # 2. (В будущем) Добавляем его в SearchGraph из sequential-search
    # 3. (В будущем) Запускаем Traversal с бюджетом alpha=0.05

    print(f"Узел создан. Стоимость шага: {search_node.cost} токенов.")
    print("Ожидание интеграции с ядром sequential-search...")


if __name__ == "__main__":
    main()
