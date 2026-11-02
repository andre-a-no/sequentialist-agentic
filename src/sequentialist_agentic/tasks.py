# SPDX-License-Identifier: AGPL-3.0-only
"""Small application tasks: cited retrieval and a trusted geometry rule set.

Retrieval establishes what a source says, not that the source is correct. The
geometry checker validates applications of the explicitly supplied rules, not
the soundness of Euclidean geometry or arbitrary natural-language arguments.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # The upstream distribution does not yet include a py.typed marker.
    from sequential_search.reasoning import Problem  # type: ignore[import-untyped]


@dataclass(frozen=True)
class Document:
    source: str
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source:
            raise ValueError("document source must be a non-empty string")
        if not isinstance(self.text, str):
            raise TypeError("document text must be a string")


@dataclass(frozen=True)
class RetrievalResult:
    answer: str | None
    sources: tuple[str, ...]
    inspected: int
    stop_reason: str


def retrieve(
    documents: Iterable[Document],
    extract: Callable[[Document], str | None],
    *,
    max_documents: int = 100,
) -> RetrievalResult:
    """Inspect distinct sources until a caller-validated answer is found.

    This finite baseline accounts for unique in-memory source inspections;
    network acquisition and model inference are not represented by that cost.
    Conflicting repeated source IDs are rejected when encountered. The caller
    owns extraction and acceptance semantics; no statistical claim is made.
    """
    if type(max_documents) is not int or max_documents < 0:
        raise ValueError("max_documents must be a non-negative integer")
    seen: dict[str, str] = {}
    inspected = 0
    for document in documents:
        if document.source in seen:
            if seen[document.source] != document.text:
                raise ValueError(f"conflicting content for source {document.source!r}")
            continue
        if inspected >= max_documents:
            return RetrievalResult(None, (), inspected, "budget_limit")
        seen[document.source] = document.text
        inspected += 1
        answer = extract(document)
        if answer is not None:
            if not isinstance(answer, str) or not answer:
                raise ValueError("extract must return a non-empty answer or None")
            return RetrievalResult(answer, (document.source,), inspected, "answered")
    return RetrievalResult(None, (), inspected, "sources_exhausted")


def geometry_problem(*, midpoint_known: bool = True) -> Problem:
    """Median of a nondegenerate isosceles triangle is an altitude.

    Facts are symbolic atoms. Geometric implications are a trusted,
    application-supplied rule set; no formula parser or geometry prover is
    implied. The declared upstream revision includes the required reasoning API.
    """
    try:
        from sequential_search.reasoning import Problem, Rule
    except ModuleNotFoundError as exc:
        if exc.name != "sequential_search.reasoning":
            raise
        raise ImportError(
            "geometry_problem requires the pinned sequential-search-core reasoning API; "
            "reinstall declared dependencies; see README.md"
        ) from exc

    facts = {"AB=AC", "AD=AD", "D between B and C", "A not on BC"}
    if midpoint_known:
        facts.add("BD=DC")
    rules = (
        Rule("SSS", frozenset({"AB=AC", "BD=DC", "AD=AD", "D between B and C", "A not on BC"}),
             "triangles ABD and ACD congruent"),
        Rule("corresponding angles", frozenset({"triangles ABD and ACD congruent"}),
             "angle BDA = angle ADC"),
        Rule("straight angle", frozenset({"D between B and C"}),
             "angle BDA + angle ADC = 180"),
        Rule("equal supplementary angles", frozenset({"angle BDA = angle ADC",
                                                      "angle BDA + angle ADC = 180"}),
             "angle BDA = 90"),
        Rule("perpendicular lines", frozenset({"angle BDA = 90", "A not on BC"}), "AD perpendicular BC"),
    )
    return Problem(frozenset(facts), "AD perpendicular BC", rules, context="euclidean/isosceles-median/1")
