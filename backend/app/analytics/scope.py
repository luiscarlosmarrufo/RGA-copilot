"""Dataset scope guard (ADR-0012).

Every NAMA analytics function must call ``assert_nama_only(df)`` before
computing. A DataFrame that mixes scopes raises ``DatasetScopeError`` — there
is no path through analytics that silently aggregates reference data with
NAMA data.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from app.core.errors import DatasetScopeError
from app.parsers.data_parser import DATASET_SCOPE_COLUMN, DEFAULT_DATASET_SCOPE


def assert_nama_only(df: pd.DataFrame) -> None:
    """Shortcut for the common case: only ``nama_2026`` rows allowed."""
    assert_scope(df, allowed={DEFAULT_DATASET_SCOPE})


def assert_scope(df: pd.DataFrame, *, allowed: Iterable[str]) -> None:
    """Raise if the DataFrame contains any row whose scope is not in ``allowed``."""
    allowed_set = set(allowed)
    if DATASET_SCOPE_COLUMN not in df.columns:
        raise DatasetScopeError(
            f"DataFrame is missing required column '{DATASET_SCOPE_COLUMN}'",
            details={"allowed": sorted(allowed_set)},
        )
    found = {str(v) for v in df[DATASET_SCOPE_COLUMN].dropna().unique().tolist()}
    forbidden = found - allowed_set
    if forbidden:
        raise DatasetScopeError(
            f"DataFrame contains forbidden dataset_scope value(s): {sorted(forbidden)}",
            details={
                "found": sorted(found),
                "allowed": sorted(allowed_set),
                "forbidden": sorted(forbidden),
            },
        )
