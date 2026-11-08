# Sequentialist Agentic

Application workflows for tools and agent decisions using
[sequential-search](https://github.com/andre-a-no/sequential-search).

## Conceptual framework: the Sequentialist ecosystem

The ecosystem studies sequential decisions: observations arrive, evidence
changes, and a policy chooses whether to continue, act, wait or stop. It separates
three questions within the mathematical and cybernetic methods layer:

| Library | Central question | Responsibility |
|---|---|---|
| [sequential-analysis](https://github.com/andre-a-no/sequential-analysis) | What can we infer from the observations available so far? | Statistical tests, estimation, filtering, prediction and procedure-specific uncertainty guarantees. |
| [sequential-search](https://github.com/andre-a-no/sequential-search) | Which step should we explore next to reach an answer or a goal? | Search and reasoning over alternatives, experiments and rules, with explicit evidence, provenance and resource costs. |
| [sequential-games](https://github.com/andre-a-no/sequential-games) | How do participants pursue their own goals while their actions change a shared environment? | Interaction models for cooperation, competition and partially aligned interests, including asynchronous actions, local information and deliberate waiting. |

These are complementary responsibilities. A participant's policy can use search
to plan and statistical analysis to interpret observations; other participants
continue to act according to their own objectives. This describes how the
methods can be composed. Each package's implementation status is stated
separately below.

The naming convention expresses a further separation into three layers:

| Layer | Packages | Responsibility |
|---|---|---|
| Mathematical and cybernetic methods | `sequential-*`: analysis, search, games | Models, algorithms, explicit state and the assumptions under which a result holds. |
| Reusable engineering platform | `sequentialist-*`, including [core](https://github.com/andre-a-no/sequentialist-core) and [visuals](https://github.com/andre-a-no/sequentialist-visuals) | Durable application execution, storage, recovery, audit and presentation, according to each package's implemented scope. |
| Domain applications | `sequentialist-*`, including [ab](https://github.com/andre-a-no/sequentialist-ab), [quality](https://github.com/andre-a-no/sequentialist-quality), [monitor](https://github.com/andre-a-no/sequentialist-monitor), [clinical](https://github.com/andre-a-no/sequentialist-clinical) and [agentic](https://github.com/andre-a-no/sequentialist-agentic) | Subject-specific goals, workflows, adapters and user-facing decisions built from the methods and engineering components they need. |

Both the engineering platform and applications use the `sequentialist-*`
prefix. The platform is an open family of reusable packages; `core` currently
provides durable tasks built around `sequential-analysis` runs. This organization
does not imply that every combination already has an integration.

Across the ecosystem, state, information available to a decision, randomness,
costs and stopping reasons should be explicit. Evidence, resource expenditure
and real-world effects have separate meanings. Statistical validity, derivability
under supplied rules, properties of an interaction model and reliable execution
each require their own justification; a guarantee in one layer does not
automatically establish a guarantee in another.

### This package's role

**Layer: domain application.** Agentic supplies tool adapters, task meanings,
candidate generation and result checks around search methods. Reusable search
algorithms belong to `sequential-search`; reusable presentation belongs to
`sequentialist-visuals`. A multi-participant interaction model would belong to
`sequential-games`, with a separate application adapter. LLMs are optional;
a tool result or judge score does not by itself establish a statistical guarantee.

## 🎯 Идея
Современные фреймворки ИИ-агентов (ReAct, Tree of Thoughts, RAG) часто полагаются на эвристики для остановки: лимиты шагов (`max_steps`) или ненадёжную самооценку LLM.

Этот проект использует контракты `sequential-search` для прикладных задач агентов:

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

The declared Git dependency pins sequential-search to the tested commit
`45fbe4cdba647b59ec3fd528cad94019cece3ba9`, which includes the reasoning API.
This commit is available on an upstream review branch, not yet a merged release.
Installing this checkout and its declared dependencies supports both offline demos:

```bash
python -m pip install -e '.[dev]'
python examples/search_agent_demo.py
python examples/reasoning_demo.py
python -m pytest -q tests
```

For coordinated local development only, an adjacent editable checkout can
replace the pinned installation:

```bash
python -m pip install --no-deps -e ../sequential-search
```

Recheck compatibility after such an override.

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
  current limitations and the exact upstream revision.
- [Обзор и частые вопросы на русском](docs/overview.ru.md).
- [Repository guidance](AGENTS.md): source map and proportionate check commands.
- [Curated reading index](llms.txt): a concise entry point for readers and
  assistants. Automatic discovery and web indexing depend on the client/service.
