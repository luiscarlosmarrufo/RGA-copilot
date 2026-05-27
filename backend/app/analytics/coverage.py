"""Period coverage (ADR-0013).

The declared study window is the full set of months the consulting brief
covers. Actual is what the data contains. Missing is the difference. When
``missing`` is non-empty, downstream callers attach a ``missing_periods``
warning to their result; the UI / report / LLM prompt all surface it.

The parser does not impute missing months. Analytics never extrapolate.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

import pandas as pd

# Default declared window for the current Grupo NAMA study (ADR-0013).
DEFAULT_DECLARED_WINDOW: tuple[str, ...] = (
    "ENERO 2026",
    "FEBRERO 2026",
    "MARZO 2026",
    "ABRIL 2026",
)


@dataclass(frozen=True)
class PeriodCoverage:
    declared: tuple[str, ...]
    actual: tuple[str, ...]
    missing: tuple[str, ...]
    unexpected: tuple[str, ...] = field(default=())

    @property
    def has_missing(self) -> bool:
        return bool(self.missing)

    def to_dict(self) -> dict[str, list[str]]:
        d: dict[str, list[str]] = {
            "declared": list(self.declared),
            "actual": list(self.actual),
            "missing": list(self.missing),
        }
        if self.unexpected:
            d["unexpected"] = list(self.unexpected)
        return d


def compute_period_coverage(
    df: pd.DataFrame,
    *,
    declared: Iterable[str] = DEFAULT_DECLARED_WINDOW,
    column: str = "MES",
) -> PeriodCoverage:
    """Compare the declared window against the months present in ``df[column]``.

    Preserves declared order in ``actual`` and ``missing``. Months found in
    the data but **not** declared are surfaced separately as ``unexpected``
    (e.g. an early stray ``MAYO 2026`` row) — they don't move into ``missing``.
    """
    declared_tuple = tuple(declared)
    if column not in df.columns:
        # Nothing to compare against; treat every declared month as missing.
        return PeriodCoverage(
            declared=declared_tuple,
            actual=(),
            missing=declared_tuple,
            unexpected=(),
        )
    present = {str(v) for v in df[column].dropna().unique().tolist() if str(v).strip()}
    actual = tuple(m for m in declared_tuple if m in present)
    missing = tuple(m for m in declared_tuple if m not in present)
    unexpected = tuple(sorted(present - set(declared_tuple)))
    return PeriodCoverage(
        declared=declared_tuple,
        actual=actual,
        missing=missing,
        unexpected=unexpected,
    )


def missing_period_warning(coverage: PeriodCoverage) -> dict | None:
    """Return the warning payload for the LLM/UI when ``missing`` is non-empty.

    The shape matches the ``warnings`` array in the deterministic JSON contract
    (see docs/DATA_CONTRACTS.md § 6).
    """
    if not coverage.has_missing:
        return None
    return {
        "code": "missing_periods",
        "missing": list(coverage.missing),
        "declared": list(coverage.declared),
        "actual": list(coverage.actual),
    }
