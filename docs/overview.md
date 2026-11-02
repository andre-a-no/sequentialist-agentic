# Understand sequentialist-agentic

English · [Русский](overview.ru.md)

## What problem does it address?

`sequentialist-agentic` is application software that connects tool actions,
retrieval and reasoning tasks to the family's search algorithms. A task can ask
for an answer from sources or for a conclusion derived from known premises.
The application supplies what the facts, actions, goals and result checks mean.

| Choose this example | Inputs | Outputs |
|---|---|---|
| Original tool-agent demo | Mock search queries, snippets, scores and resource limits | Steps, resource use and an agent traversal outcome |
| Finite geometry reasoning | Explicit symbolic facts and trusted implication rules | A checked rule-application trace, a conditional result or a search stop reason |
| Bounded source retrieval | Documents with source IDs and a caller-defined extractor | An answer with source IDs, inspection count and stop reason |

The mathematical algorithms are in `sequential-search`. Read-only graph
rendering is in `sequentialist-visuals`. This application is not mandatory for
other subject packages to use search or games.

## What a person who does not program can do

Start with a concrete question and the material already known. Decide what
would count as an acceptable result: a quotation from a source, a checked rule
application, or a subject-specific decision. An assistant or developer can map
that task to the examples, run it and explain the returned result.

For the current geometry example, the application explicitly states facts about
an isosceles triangle and a midpoint, then applies a small trusted rule set to
show that its median is perpendicular to the base. Removing the midpoint fact
leaves a missing-premise condition. This illustrates the mechanics of reasoning;
it does not parse arbitrary diagrams or automatically solve olympiad problems.

For retrieval, provide documents with distinct source IDs and specify what text
counts as an answer. The example reports which source supplied a matching claim.
Checking that the source is reliable or that the claim is true is a separate task.

There is no no-code user interface or hosted search service in this version.
The shipped examples are offline and need no LLM key. You can read their source
and expected behavior here without installing Python; executing them requires
Python and the documented development dependencies.

## Run the current examples

The current [package metadata](../pyproject.toml) pins `sequential-search-core`
to the tested commit `45fbe4cdba647b59ec3fd528cad94019cece3ba9`, which contains
`sequential_search.reasoning`. This commit is published on a review branch and
is not yet a merged upstream release. From the agentic repository root:

```bash
python -m pip install -e '.[dev]'
python examples/search_agent_demo.py
python examples/reasoning_demo.py
python -m pytest -q tests
```

For coordinated local development, an adjacent checkout can optionally replace
the pinned package: `python -m pip install --no-deps -e ../sequential-search`.
Validate the examples again after changing that override.

The demo prints the forward, backward and bidirectional reasoning results and a
retrieved answer with source IDs and an inspection count. It verifies its finite
proof traces through the upstream checker. Exact printed output can change with
the supported development revision; inspect the result status and its premises.

For optional offline HTML output:

```bash
python -m pip install -e ../sequentialist-visuals
python examples/reasoning_demo.py --html reasoning-proof.html
```

Open `reasoning-proof.html` in a browser. The page visualizes supplied records;
it does not add a new correctness or statistical guarantee.

The original [search_agent_demo.py](../examples/search_agent_demo.py) remains
separate from the new [reasoning_demo.py](../examples/reasoning_demo.py). Both
use the declared dependency revision; no adjacent source checkout is required
for their offline execution. Release/tag status is separate from commit availability.

## Current capabilities and limits

Implemented in the current development sources:

- Tool/node adapters and an offline mock traversal baseline.
- An application-supplied finite geometry rule set.
- Integration with forward/backward/checked bidirectional reasoning algorithms.
- Bounded, source-identified in-memory retrieval with duplicate-source handling.
- Optional read-only HTML proof inspection through visuals.

A general theorem prover, natural-language mathematical verifier, production
web retrieval service, universally calibrated LLM judge and complete adaptive
whole-search error-control scheme are not implemented. Live tool orchestration
and production operation require additional engineering adapters and explicit
execution/recovery contracts. No delivery date is implied.

## FAQ

**Why not put all algorithms here?**
This is the application layer. Reusable mathematics and cybernetics belong in
`sequential-*`; engineering and subject semantics belong in `sequentialist-*`.

**Does a successful finite derivation prove an arbitrary mathematical claim?**
No. The checker validates rule applications under the supplied facts, rules and
context. Soundness of the subject rules and truth of premises remain explicit
assumptions. Conditional and budget-limited outcomes are not unconditional proofs.

**Are LLM confidence scores e-values with error guarantees?**
Not automatically. A valid e-process requires the stated statistical model or
calibration conditions. Whole-search FWER/FDR control also needs justified
adaptive selection, dependence and budget accounting. The mock discriminator
and arbitrary scores do not establish those conditions.

**Does a cited answer establish truth?**
It establishes what the accepted source record said. The caller defines the
extractor/acceptance criterion. Source exhaustion and a document-budget limit
are distinct from proving that no answer exists.

**Why do installation and import names differ?**
The repository is `sequentialist-agentic`, the current distribution metadata
names it `sequential-search`, and Python imports use `sequentialist_agentic`.
These are current metadata facts; this document does not rename the package.

**Can Codex, Claude, Qwen, Gemini, Grok or Perplexity use these docs?**
They can use sources they are able and permitted to access. Coding clients vary
in whether they discover `AGENTS.md` or provider-specific pointer files. Give
the assistant this overview, the [README](../README.md) or [reading index](../llms.txt)
explicitly when needed. Web assistants such as Grok or Perplexity may read
accessible repository pages; indexing, ranking, citation and automatic file
support are not promised by this repository.

## Source of truth

- [README](../README.md): development setup and examples.
- [Task implementation](../src/sequentialist_agentic/tasks.py): exact input/output behavior.
- [Reasoning demo](../examples/reasoning_demo.py): a complete executable workflow.
- [Task tests](../tests/test_tasks.py): regressions and checked boundaries.
- [Evaluator interfaces](../src/sequentialist_agentic/evidence.py): statistical caveats.
- [Metadata](../pyproject.toml): actual dependencies and distribution identity.
- [Repository guidance](../AGENTS.md): source map and verification commands.
