import pandas as pd
import pytest

from app.analytics.margins import aggregate_margins_per_sucursal
from app.analytics.sensitivity import shock_costs
from app.parsers.data_parser import DataParser


@pytest.fixture
def cleaned(read_fixture) -> pd.DataFrame:
    return DataParser().load_csv(read_fixture("analytics_sample.csv")).dataframe


def test_shock_costs_default_factor_increases_costs_by_5pct(cleaned):
    shocked = shock_costs(cleaned)  # default factor 1.05
    ant_a_orig = cleaned[
        (cleaned["LÍNEA DE NEGOCIO"] == "ANT") & (cleaned["SUBCATEGORÍA 2"] == "A")
    ].iloc[0]
    ant_a_shocked = shocked[
        (shocked["LÍNEA DE NEGOCIO"] == "ANT") & (shocked["SUBCATEGORÍA 2"] == "A")
    ].iloc[0]

    # Original COSTO TOTAL DEL SERVICIO = 400 → 400 * 1.05 = 420
    assert ant_a_shocked["COSTO TOTAL DEL SERVICIO"] == pytest.approx(420.0)
    # UTILIDAD BRUTA = TOTAL - new cost = 1000 - 420 = 580
    assert ant_a_shocked["UTILIDAD BRUTA"] == pytest.approx(580.0)
    # MARGEN BRUTO = 580 / 1000 = 0.58
    assert ant_a_shocked["MARGEN BRUTO"] == pytest.approx(0.58)
    # Source is unchanged
    assert ant_a_orig["MARGEN BRUTO"] == pytest.approx(0.60)


def test_shock_costs_aggregate_ant_margin_drops_by_expected_amount(cleaned):
    shocked = shock_costs(cleaned, factor=1.05)
    ant_agg = aggregate_margins_per_sucursal(shocked).set_index("LÍNEA DE NEGOCIO").loc["ANT"]
    # New ANT cost total = 2330 * 1.05 = 2446.5
    assert ant_agg["costo_total"] == pytest.approx(2446.5)
    # New ANT utilidad bruta = 3700 - 2446.5 = 1253.5
    assert ant_agg["utilidad_bruta"] == pytest.approx(1253.5)
    # New margen bruto = 1253.5 / 3700
    assert ant_agg["margen_bruto"] == pytest.approx(1253.5 / 3700)


def test_shock_costs_zero_factor_zeroes_costs_and_makes_margins_one(cleaned):
    shocked = shock_costs(cleaned, factor=0.0)
    assert (shocked["COSTO TOTAL DEL SERVICIO"] == 0).all()
    # With zero cost, margen = TOTAL / TOTAL = 1.0
    assert (shocked["MARGEN BRUTO"] == 1.0).all()


def test_shock_costs_does_not_mutate_input(cleaned):
    original = cleaned.copy()
    _ = shock_costs(cleaned, factor=1.20)
    pd.testing.assert_frame_equal(cleaned, original)


def test_shock_costs_rejects_negative_factor(cleaned):
    with pytest.raises(ValueError):
        shock_costs(cleaned, factor=-0.1)
