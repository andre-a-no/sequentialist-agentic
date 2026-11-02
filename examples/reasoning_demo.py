# SPDX-License-Identifier: AGPL-3.0-only
"""Run two application baselines; optionally write a portable proof visualization."""
from __future__ import annotations

import argparse
from pathlib import Path

from sequential_search.reasoning import (
    solve_backward,
    solve_bidirectional,
    solve_forward,
    verify_proof,
)

from sequentialist_agentic.tasks import Document, geometry_problem, retrieve


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, help="optional standalone HTML proof view (requires visuals)")
    args = parser.parse_args()
    problem = geometry_problem()
    last = None
    for name, solver in (("forward", solve_forward), ("backward", solve_backward),
                         ("bidirectional", solve_bidirectional)):
        result = solver(problem)
        assert result.proof is not None and verify_proof(problem, result.proof)
        print(f"{name}: {result.status}; rules: {', '.join(result.proof.steps)}")
        last = result

    documents = [Document("notes", "No release information here."),
                 Document("notes", "No release information here."),
                 Document("release", "The sample release is v1.2.")]
    answer = retrieve(documents, lambda doc: "v1.2" if "release is v1.2" in doc.text else None)
    print(f"retrieval: {answer.answer}; sources={answer.sources}; inspected={answer.inspected}")

    if args.html:
        from sequentialist.visuals import render_search

        assert last is not None and last.proof is not None
        used = set(last.proof.steps)
        atoms = set(problem.facts) | {problem.goal}
        for rule in problem.rules:
            if rule.name in used:
                atoms.update(rule.premises)
                atoms.add(rule.conclusion)
        graph = {
            "nodes": [{"id": atom, "label": atom,
                       "status": "given" if atom in problem.facts else "derived"} for atom in sorted(atoms)],
            "rules": [{"id": rule.name, "label": rule.name, "premises": sorted(rule.premises),
                       "conclusion": rule.conclusion} for rule in problem.rules if rule.name in used],
        }
        args.html.write_text(render_search(graph, title="Isosceles median: checked rule applications"),
                             encoding="utf-8")
        print(f"proof view: {args.html}")


if __name__ == "__main__":
    main()
