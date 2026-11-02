# SPDX-License-Identifier: AGPL-3.0-only
"""Application examples exercise the generic engine and citation boundaries."""
from dataclasses import replace

import pytest
from sequential_search.reasoning import (
    solve_backward,
    solve_bidirectional,
    solve_forward,
    verify_proof,
)

from sequentialist_agentic.tasks import Document, geometry_problem, retrieve


@pytest.mark.parametrize("solver", [solve_forward, solve_backward, solve_bidirectional])
def test_geometry_goal_has_a_checked_derivation(solver):
    problem = geometry_problem()
    result = solver(problem)
    assert result.status == "proved"
    assert result.proof is not None
    assert verify_proof(problem, result.proof)
    assert "SSS" in result.proof.steps
    assert "equal supplementary angles" in result.proof.steps
    assert not verify_proof(replace(problem, context="other-context"), result.proof)


def test_missing_midpoint_is_not_an_unconditional_proof():
    problem = geometry_problem(midpoint_known=False)
    assert solve_forward(problem).status != "proved"
    result = solve_backward(problem)
    assert result.status == "conditional"
    assert result.proof is not None
    assert "BD=DC" in result.missing
    assert not verify_proof(problem, result.proof)
    assert verify_proof(problem, result.proof, allow_assumptions=True)


def test_retrieval_returns_an_actual_source_and_deduplicates_inspections():
    documents = [Document("a", "irrelevant"), Document("a", "irrelevant"), Document("b", "answer: 42")]
    visited = []

    def extract(doc):
        visited.append(doc.source)
        return "42" if doc.text == "answer: 42" else None

    result = retrieve(documents, extract, max_documents=2)
    assert result.answer == "42" and result.sources == ("b",)
    assert result.inspected == 2 and visited == ["a", "b"]
    assert result.stop_reason == "answered"


def test_retrieval_budget_limit_is_distinct_from_finite_source_exhaustion():
    documents = [Document("a", "nothing"), Document("b", "answer")]
    limited = retrieve(documents, lambda doc: None, max_documents=1)
    exhausted = retrieve(documents[:1], lambda doc: None, max_documents=1)
    assert limited.stop_reason == "budget_limit"
    assert exhausted.stop_reason == "sources_exhausted"
    assert limited.answer is exhausted.answer is None


def test_conflicting_source_identity_is_rejected():
    with pytest.raises(ValueError, match="conflicting content"):
        retrieve([Document("same", "old"), Document("same", "new")], lambda doc: None)


def test_retrieval_zero_budget_never_runs_extraction():
    def forbidden(doc):
        pytest.fail("no inspection authorized")

    result = retrieve([Document("a", "answer")], forbidden, max_documents=0)
    assert result.stop_reason == "budget_limit" and result.inspected == 0
