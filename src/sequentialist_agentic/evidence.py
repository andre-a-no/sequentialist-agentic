"""Оценка наблюдений ИИ-агента в улики (e-values) для рёбер ядра.

Здесь живёт единственное место проекта, где субъективная оценка LLM или
метрик релевантности превращается в статистическую валюту `EvidenceState`.

Дискриминатор (discriminator) — функция, возвращающая правдоподобие
наблюдения при гипотезе H1 ("ветка перспективна") и H0 ("ветка бесполезна").
Отношение likelihood-правдоподобий логарифмируется и накапливается; e-value =
exp(накопленного logLR), калиброванного порогом ребра (Ville: при H0
супермартингейл e даёт P(sup e >= 1/α) <= α).

Внимание: доверие к дискриминатору — отдельная проблема (калибровка LLM).
Модуль даёт интерфейс и честную документированную семантику, а не гарантию
того, что конкретный промпт-оценщик хорошо откалиброван.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol, Sequence

from sequential_search.core.edge import EvidenceState


class ObservationLike(Protocol):
    """Минимальный интерфейс наблюдения агента (см. nodes.SearchObservation)."""

    def as_mapping(self) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class LogLRRollup:
    """Накопитель log-likelihood-ratio по потоку наблюдений одного узла.

    Чистый: каждый `feed` возвращает НОВОЕ состояние (immutable value,
    инвариант N1 ядра), ничего не мутирует на месте.
    """

    log_lr_total: float = 0.0
    n: int = 0

    def feed(self, loglr_increment: float) -> "LogLRRollup":
        if not math.isfinite(loglr_increment):
            raise ValueError(f"loglr increment must be finite, got {loglr_increment}")
        return LogLRRollup(log_lr_total=self.log_lr_total + loglr_increment, n=self.n + 1)

    def evidence(self) -> EvidenceState:
        """Сконвертировать накопленный logLR в e-value (валюта ребра ядра)."""
        return EvidenceState(e=math.exp(self.log_lr_total), stat=self.log_lr_total, n=self.n)


#: Тип дискриминатора: (наблюдение, контекст) -> (loglr, метаданные оценки)
Discriminator = Callable[[Mapping[str, Any], Any], tuple[float, dict[str, Any]]]


def heuristic_relevance_discriminator(
    *, h1: float = 0.8, h0: float = 0.3, threshold: float = 0.5
) -> Discriminator:
    """Детерминированный mock-дискриминатор для тестов и примеров.

    Считает долю «полезных» сниппетов (score >= threshold) и выдаёт фиксированный
    logLR на наблюдение в зависимости от того, выше ли средняя релевантность
    порога. НЕ является настоящей оценкой — это заглушка с корректной сигнатурой,
    чтобы сквозной пример запускался без LLM и сети.
    """
    lr = math.log(h1 / h0) - math.log((1 - h1) / (1 - h0))  # бернуллиевский logLR

    def discriminate(values: Mapping[str, Any], context: Any = None) -> tuple[float, dict[str, Any]]:
        scores = values.get("scores") or []
        if not scores:
            return 0.0, {"reason": "no-scores"}
        mean_rel = sum(scores) / len(scores)
        if mean_rel >= threshold:
            return lr, {"mean_relevance": mean_rel, "direction": "+"}
        return -lr, {"mean_relevance": mean_rel, "direction": "-"}

    return discriminate


class LLMDiscriminator:
    """Каркас дискриминатора на базе LLM-оценщика.

    Ожидает от `judge(query, snippet)` числовую оценку уверенности [0, 1]
    (например, через structured output). Оценка конвертируется в logLR
    относительно базового курса p0 (неинформированное ожидание).

    TODO(ADR): зафиксировать протокол калибровки judge (proper scoring rule,
    temperature, выбор p0) — без него гарантия α держится только относительно
    заявленной модели оценки.
    """

    def __init__(self, judge: Callable[[str, str], float], *, p0: float = 0.5, p1: float = 0.9):
        if not 0 < p0 < p1 < 1:
            raise ValueError("require 0 < p0 < p1 < 1")
        self._judge = judge
        self._p0 = p0
        self._p1 = p1

    def __call__(self, values: Mapping[str, Any], context: Any = None) -> tuple[float, dict[str, Any]]:
        query = values.get("query", "")
        total = 0.0
        judged: list[dict[str, Any]] = []
        for snippet in values.get("snippets", []):
            q = max(min(self._judge(query, snippet), 1 - 1e-9), 1e-9)
            # log LR одного «подрешётного» наблюдения против базового курса
            inc = q * math.log(self._p1 / self._p0) + (1 - q) * math.log(
                (1 - self._p1) / (1 - self._p0)
            )
            total += inc
            judged.append({"snippet": snippet[:80], "confidence": q})
        return total, {"judged": judged}
