import pandas as pd
import pytest

from app.analytics.margins import (
    aggregate_margins_per_sucursal,
    cost_leakage,
    cost_leakage_ratio,
    margen_bruto,
    utilidad_bruta,
)
from app.analytics.scope import assert_nama_only
from app.core.errors import DatasetScopeError
from app.parsers.data_parser import (
    DATASET_SCOPE_COLUMN,
    DEFAULT_DATASET_SCOPE,
    REFERENCE_DATASET_SCOPE,
    DataParser,
)


@pytest.fixture
def cleaned(read_fixture) -> pd.DataFrame:
    return DataParser().load_csv(read_fixture("analytics_sample.csv")).dataframe


def test_utilidad_bruta_matches_source_column(cleaned):
    recomputed = utilidad_bruta(cleaned).astype(float).reset_index(drop=True)
    source = cleaned["UTILIDAD BRUTA"].astype(float).reset_index(drop=True)
    pd.testing.assert_series_equal(recomputed, source, check_names=False)


def test_margen_bruto_matches_source_column(cleaned):
    recomputed = margen_bruto(cleaned).reset_index(drop=True)
    source = cleaned["MARGEN BRUTO"].astype(float).reset_index(drop=True)
    for a, b in zip(recomputed.tolist(), source.tolist(), strict=True):
        assert a == pytest.approx(b, abs=1e-9)


def test_cost_leakage_per_row(cleaned):
    leakage = cost_leakage(cleaned)
    # ANT rows (first 4): ctotal - costo1 → 0, 100, 50, 30
    assert leakage.iloc[0] == pytest.approx(0.0)
    assert leakage.iloc[1] == pytest.approx(100.0)
    assert leakage.iloc[2] == pytest.approx(50.0)
    assert leakage.iloc[3] == pytest.approx(30.0)


def test_cost_leakage_ratio_handles_zero_cost(cleaned):
    ratio = cost_leakage_ratio(cleaned)
    # Row 0 ANT/A: ctotal=400, costo1=400 → leakage=0, ratio = 0/400 = 0
    assert ratio.iloc[0] == pytest.approx(0.0)
    # Row 1 ANT/B: leakage=100, ctotal=1600 → ratio = 100/1600 = 0.0625
    assert ratio.iloc[1] == pytest.approx(0.0625)


def test_aggregate_margins_per_sucursal_golden(cleaned):
    agg = aggregate_margins_per_sucursal(cleaned).set_index("LÍNEA DE NEGOCIO")

    # ANT: ventas 3700, costo 2330, ub 1370, margen 1370/3700
    assert agg.loc["ANT", "ventas_total"] == pytest.approx(3700.0)
    assert agg.loc["ANT", "costo_total"] == pytest.approx(2330.0)
    assert agg.loc["ANT", "utilidad_bruta"] == pytest.approx(1370.0)
    assert agg.loc["ANT", "margen_bruto"] == pytest.approx(1370 / 3700)

    # JUR: every item at 0.50 margin → aggregate also 0.50
    assert agg.loc["JUR", "margen_bruto"] == pytest.approx(0.50)
    assert agg.loc["JUR", "ventas_total"] == pytest.approx(3700.0)

    # CAM: ventas 3700, ub 2100
    assert agg.loc["CAM", "utilidad_bruta"] == pytest.approx(2100.0)
    assert agg.loc["CAM", "margen_bruto"] == pytest.approx(2100 / 3700)


def test_scope_guard_blocks_reference_rows_in_margins(cleaned):
    contaminated = cleaned.copy()
    contaminated.iloc[0, contaminated.columns.get_loc(DATASET_SCOPE_COLUMN)] = (
        REFERENCE_DATASET_SCOPE
    )
    with pytest.raises(DatasetScopeError):
        utilidad_bruta(contaminated)


def test_dataset_scope_column_is_present_after_parse(cleaned):
    assert DATASET_SCOPE_COLUMN in cleaned.columns
    assert (cleaned[DATASET_SCOPE_COLUMN] == DEFAULT_DATASET_SCOPE).all()
    # Guard passes — no exception.
    assert_nama_only(cleaned)
