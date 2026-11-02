# Sequentialist Agentic

Математически обоснованное управление решениями ИИ-агентов на базе ядра [sequential-search](https://github.com/andre-a-no/sequential-search).

## 🎯 Идея
Современные фреймворки ИИ-агентов (ReAct, Tree of Thoughts, RAG) часто полагаются на эвристики для остановки: лимиты шагов (`max_steps`) или ненадёжную самооценку LLM.

Этот проект адаптирует строгое статистическое ядро `sequential-search` для управления агентами:

- **Node (Узел)** = вызов инструмента (поиск, чтение документа, запрос к LLM) с известной стоимостью (`cost`).
- **Edge (Ребро)** = статистическое правило остановки (на основе e-values или likelihood ratios), решающее: `accept` (ответ найден), `reject` (ветка тупиковая) или `pending` (нужен ещё шаг).
- **Условия гарантии**: контроль ошибок требует валидных статистических улик и обоснованного учёта бюджета по всему поиску. Текущий mock-дискриминатор и произвольные оценки LLM не устанавливают FWER/FDR ≤ α.

## 🚀 Быстрый старт

```bash
pip install -e .          # потянет ядро sequential-search-core из GitHub
python examples/search_agent_demo.py
```

## 🏗 Архитектура
Проект является надстройкой над `sequential-search` и фокусируется на:

1. `nodes.py`: реализация протоколов `Node` и `Observation` для инструментов ИИ.
2. `policies.py`: стратегии обхода, оптимизированные под стоимость токенов и время API.

## Reasoning and retrieval examples

The application layer now includes two finite, offline baselines in `tasks.py`:

- `geometry_problem()` expresses the isosceles-triangle median/altitude argument
  through explicit trusted geometric implications. Forward, backward and checked
  bidirectional solvers live in `sequential_search.reasoning`. Their verifier
  checks rule applications and premises; it does not certify arbitrary geometry
  rules or solve general olympiad problems. Missing midpoint information yields
  a conditional argument rather than an unconditional proof.
- `retrieve()` inspects a bounded set of distinct sources and returns the source
  of a caller-validated answer. Duplicate source IDs are not counted as new
  inspections. Source exhaustion and an inspection-budget limit are distinct.
  A cited claim is not automatically true or statistically calibrated.

These examples require the new reasoning API in the **development checkout** of
sequential-search. The existing published Git dependency pin predates that API;
the package is not release-ready until the pin is coordinated with an upstream
release/commit. For local development, install the adjacent working trees:

```bash
python -m pip install -e .
python -m pip install --no-deps -e ../sequential-search
python examples/reasoning_demo.py
python -m pytest -q tests
```

For an optional read-only HTML view, install the adjacent visuals package and run:

```bash
python -m pip install -e ../sequentialist-visuals
python examples/reasoning_demo.py --html /tmp/geometry-proof.html
```

`sequentialist-agentic` is application software. Search algorithms remain in
`sequential-search`; generic rendering remains in the engineering package
`sequentialist-visuals`. Existing tool nodes and the original search demo remain
available. No live LLM or external search service is needed for these examples.

## Find the documentation

- [Overview and FAQ](docs/overview.md): tasks, inputs/outputs, noncoder workflow,
  current limitations and the development dependency requirement.
- [Обзор и частые вопросы на русском](docs/overview.ru.md).
- [Repository guidance](AGENTS.md): source map and proportionate check commands.
- [Curated reading index](llms.txt): a concise entry point for readers and
  assistants. Automatic discovery and web indexing depend on the client/service.
