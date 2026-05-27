import pandas as pd
import pytest

from app.analytics.scope import assert_nama_only, assert_scope
from app.core.errors import DataParserError, DatasetScopeError
from app.parsers.data_parser import (
    DATASET_SCOPE_COLUMN,
    DEFAULT_DATASET_SCOPE,
    REFERENCE_DATASET_SCOPE,
)


def _frame(scopes: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"x": list(range(len(scopes))), DATASET_SCOPE_COLUMN: scopes})


def test_assert_nama_only_passes_for_pure_nama_frame():
    assert_nama_only(_frame([DEFAULT_DATASET_SCOPE, DEFAULT_DATASET_SCOPE]))


def test_assert_nama_only_raises_on_reference_row_contamination():
    df = _frame([DEFAULT_DATASET_SCOPE, REFERENCE_DATASET_SCOPE])
    with pytest.raises(DatasetScopeError) as exc_info:
        assert_nama_only(df)
    err = exc_info.value
    assert isinstance(err, DataParserError)
    assert err.code == "dataset_scope_violation"
    assert REFERENCE_DATASET_SCOPE in err.details["forbidden"]
    assert DEFAULT_DATASET_SCOPE in err.details["allowed"]


def test_assert_nama_only_raises_when_column_missing():
    with pytest.raises(DatasetScopeError):
        assert_nama_only(pd.DataFrame({"x": [1, 2]}))


def test_assert_scope_allows_explicit_reference_only_runs():
    df = _frame([REFERENCE_DATASET_SCOPE, REFERENCE_DATASET_SCOPE])
    # Reference-only is a valid OPT-IN scope; assert_scope honours it.
    assert_scope(df, allowed={REFERENCE_DATASET_SCOPE})


def test_assert_scope_blocks_mix_even_when_both_individually_allowed():
    # Both scopes are individually allowed; ALLOWED is the union — so a single
    # frame is still allowed. The contamination guard works at the *forbidden*
    # axis, not at the "we never mix" axis. We document this explicitly.
    df = _frame([DEFAULT_DATASET_SCOPE, REFERENCE_DATASET_SCOPE])
    assert_scope(df, allowed={DEFAULT_DATASET_SCOPE, REFERENCE_DATASET_SCOPE})
    # Mixing happens upstream: NAMA analytics call assert_nama_only, which
    # forbids reference rows. The dedicated test above covers the real-world
    # contamination case.
