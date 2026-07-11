"""Corpus health domain models for the Nelson Knowledge System."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthDimension:
    id: str
    title: str
    score: int
    max_score: int = 5
    notes: str = ""


@dataclass(frozen=True)
class CorpusHealthReport:
    dimensions: list[HealthDimension]

    @property
    def total_score(self) -> int:
        return sum(d.score for d in self.dimensions)

    @property
    def max_score(self) -> int:
        return sum(d.max_score for d in self.dimensions)

    def percentage(self) -> float:
        if self.max_score == 0:
            return 0.0
        return round(self.total_score / self.max_score * 100, 1)
