# Repository guidance

This is `sequentialist-agentic`, the **application** layer for tools, retrieval,
finite reasoning examples and agent policies. Mathematical search algorithms
belong in sequential-search; generic rendering belongs in sequentialist-visuals.

## Read first

- [README.md](README.md): current examples, installation and development-pin warning.
- [docs/overview.md](docs/overview.md): use cases, limits, inputs/outputs and FAQ.
- [llms.txt](llms.txt): curated reading index; client discovery behavior varies.

## Source map

- [tasks.py](src/sequentialist_agentic/tasks.py): `Document`, `retrieve`, and the
  explicit trusted geometry rule set returned by `geometry_problem`.
- [reasoning_demo.py](examples/reasoning_demo.py): finite forward/backward/
  bidirectional examples and optional read-only HTML rendering.
- [nodes.py](src/sequentialist_agentic/nodes.py),
  [policies.py](src/sequentialist_agentic/policies.py) and
  [traversal.py](src/sequentialist_agentic/traversal.py): original tool-agent baseline.
- [evidence.py](src/sequentialist_agentic/evidence.py): evaluator interfaces and
  mock scoring; arbitrary LLM scores do not establish valid e-processes.
- [search_agent_demo.py](examples/search_agent_demo.py): original offline mock demo.
- [test_tasks.py](tests/test_tasks.py): task behavior and application-level boundaries.
- [pyproject.toml](pyproject.toml): actual metadata and pinned upstream dependency.

Use the existing checkout and preserve unrelated changes. Do not turn a mock
score into an unconditional FWER/FDR claim. A finite checked derivation verifies
applications of supplied rules, not their subject soundness or arbitrary math.
Retrieval citations identify sources, not truth. Keep domain semantics here and
reuse the upstream algorithms instead of copying them.

## Development dependency caveat

The current upstream Git pin predates `sequential_search.reasoning`. The new
reasoning example needs the matching development checkout of sequential-search;
an ordinary installation of this repository alone does not supply that API.
Follow the adjacent-checkout installation commands in [README.md](README.md).
Do not silently update dependency pins or rename the distribution: current
metadata names the distribution `sequential-search`, while Python imports are
`sequentialist_agentic`.

## Checks

From this repository's root, after installing the matching development sources:

```bash
python examples/search_agent_demo.py
python examples/reasoning_demo.py
python -m pytest -q tests
python -m ruff check src/sequentialist_agentic/tasks.py examples/reasoning_demo.py tests/test_tasks.py
python -m mypy --follow-imports=silent src/sequentialist_agentic/tasks.py
git diff --check
```

The scoped static checks cover the new task/example layer; they are not a claim
that every legacy module has been type/lint cleaned. Commands were exercised
against the current development sources. For docs-only changes, use
`git diff --check`, validate changed relative links and check statements against
the source. Rerun examples if their usage changes; do not run unrelated expensive
suites merely for a spelling change.

No publication, push, live LLM call or external message is implied by maintenance.
