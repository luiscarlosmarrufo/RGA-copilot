import pandas as pd
import pytest

from app.analytics.alerts import (
    all_financial_alerts,
    inefficient_line_alerts,
    low_margin_alerts,
    profit_concentration_alerts,
)
from app.parsers.data_parser import (
    DATASET_SCOPE_COLUMN,
    DEFAULT_DATASET_SCOPE,
    DataParser,
)


@pytest.fixture
def cleaned(read_fixture) -> pd.DataFrame:
    return DataParser().load_csv(read_fixture("analytics_sample.csv")).dataframe


# ---------- low margin -------------------------------------------------------


def test_low_margin_fires_above_5pp_below_benchmark(cleaned):
    alerts = low_margin_alerts(cleaned, benchmark=0.50)
    sucursales = {a.details["sucursal"] for a in alerts}
    assert "ANT" in sucursales   # margen ~37% → ~13 pp below benchmark
    assert "JUR" not in sucursales  # exactly 50%, delta 0 pp
    assert "CAM" not in sucursales  # margen ~57%, above benchmark
    ant_alert = next(a for a in alerts if a.details["sucursal"] == "ANT")
    assert ant_alert.severity == "HIGH"
    assert ant_alert.code == "low_margin"
    assert ant_alert.details["delta_pp"] == pytest.approx(-12.97, abs=0.1)


def test_low_margin_strict_boundary_at_exactly_5pp_below():
    df = pd.DataFrame(
        {
            "MES": ["ENERO 2026", "ENERO 2026", "ENERO 2026"],
            "LÍNEA DE NEGOCIO": ["BELOW", "AT", "ABOVE"],
            "CANTIDAD": [1, 1, 1],
            "TOTAL": [1000.0, 1000.0, 1000.0],
            "COSTO 1": [600.0, 550.0, 500.0],
            "COSTO TOTAL DEL SERVICIO": [600.0, 550.0, 500.0],
            "UTILIDAD BRUTA": [400.0, 450.0, 500.0],
            "MARGEN BRUTO": [0.40, 0.45, 0.50],
            DATASET_SCOPE_COLUMN: [DEFAULT_DATASET_SCOPE] * 3,
        }
    )
    alerts = low_margin_alerts(df, benchmark=0.50)
    fired = {a.details["sucursal"] for a in alerts}
    # BELOW: -10 pp → fires. AT: -5 pp exactly → does NOT fire (rule is > 5 pp).
    # ABOVE: 0 pp → does not fire.
    assert fired == {"BELOW"}


# ---------- profit concentration --------------------------------------------


def test_profit_concentration_above_50pct_is_high(cleaned):
    alerts = profit_concentration_alerts(cleaned)
    by_tag = {a.details["tag"]: a for a in alerts}
    # CALIENTE share ~74.25% → HIGH.
    assert "CALIENTE" in by_tag
    assert by_tag["CALIENTE"].severity == "HIGH"
    assert by_tag["CALIENTE"].details["share"] == pytest.approx(0.7425, abs=0.001)
    # FRIA share ~25.75% → below MEDIUM threshold → no alert.
    assert "FRIA" not in by_tag


def test_profit_concentration_medium_band_between_40_and_50pct():
    # Two tags carrying 45% and 55% of profit respectively.
    df = pd.DataFrame(
        {
            "MES": ["ENERO 2026"] * 2,
            "LÍNEA DE NEGOCIO": ["X"] * 2,
            "CANTIDAD": [1, 1],
            "TOTAL": [100.0, 100.0],
            "COSTO 1": [55.0, 45.0],
            "COSTO TOTAL DEL SERVICIO": [55.0, 45.0],
            "UTILIDAD BRUTA": [45.0, 55.0],
            "MARGEN BRUTO": [0.45, 0.55],
            "COL ESPECIAL 1": ["AA", "BB"],
            DATASET_SCOPE_COLUMN: [DEFAULT_DATASET_SCOPE] * 2,
        }
    )
    alerts = profit_concentration_alerts(df)
    by_tag = {a.details["tag"]: a for a in alerts}
    assert by_tag["AA"].severity == "MEDIUM"   # 45%
    assert by_tag["BB"].severity == "HIGH"     # 55%


def test_profit_concentration_below_40pct_does_not_fire():
    df = pd.DataFrame(
        {
            "MES": ["ENERO 2026"] * 3,
            "LÍNEA DE NEGOCIO": ["X"] * 3,
            "CANTIDAD": [1, 1, 1],
            "TOTAL": [100.0, 100.0, 100.0],
            "COSTO 1": [70.0, 70.0, 70.0],
            "COSTO TOTAL DEL SERVICIO": [70.0, 70.0, 70.0],
            "UTILIDAD BRUTA": [30.0, 30.0, 30.0],
            "MARGEN BRUTO": [0.30, 0.30, 0.30],
            "COL ESPECIAL 1": ["AA", "BB", "CC"],
            DATASET_SCOPE_COLUMN: [DEFAULT_DATASET_SCOPE] * 3,
        }
    )
    alerts = profit_concentration_alerts(df)
    # Each tag carries 33.3% → none above 40%.
    assert alerts == []


# ---------- inefficient line ------------------------------------------------


def test_inefficient_line_flags_ant_only(cleaned):
    alerts = inefficient_line_alerts(cleaned)
    sucursales = {a.details["sucursal"] for a in alerts}
    assert sucursales == {"ANT"}
    ant = next(a for a in alerts if a.details["sucursal"] == "ANT")
    assert ant.code == "inefficient_line"
    assert ant.severity == "MEDIUM"
    # Mean of others (JUR 0.50, CAM 2100/3700≈0.5676) ≈ 0.5338; ANT 1370/3700≈0.3703.
    assert ant.details["others_mean_margen_bruto"] == pytest.approx(
        (0.50 + 2100 / 3700) / 2, abs=1e-6
    )


def test_inefficient_line_strict_boundary_at_exactly_2pp_below():
    # Two sucursales with margens [0.50, 0.52]. Each compares to the other.
    # 0.50 vs 0.52 → -2 pp exactly → does NOT fire (rule is > 2 pp below).
    df = pd.DataFrame(
        {
            "MES": ["ENERO 2026"] * 4,
            "LÍNEA DE NEGOCIO": ["A", "A", "B", "B"],
            "CANTIDAD": [1, 1, 1, 1],
            "TOTAL": [100.0, 100.0, 100.0, 100.0],
            "COSTO 1": [50.0, 50.0, 48.0, 48.0],
            "COSTO TOTAL DEL SERVICIO": [50.0, 50.0, 48.0, 48.0],
            "UTILIDAD BRUTA": [50.0, 50.0, 52.0, 52.0],
            "MARGEN BRUTO": [0.50, 0.50, 0.52, 0.52],
            DATASET_SCOPE_COLUMN: [DEFAULT_DATASET_SCOPE] * 4,
        }
    )
    alerts = inefficient_line_alerts(df)
    assert alerts == []


def test_inefficient_line_fires_above_2pp_below():
    # A at 0.40, B at 0.50, C at 0.60. Each compared against the mean of the OTHERS.
    # A: others_mean=(0.50+0.60)/2=0.55, delta=(0.40-0.55)*100=-15 pp → fires.
    # B: others_mean=(0.40+0.60)/2=0.50, delta=0 → no alert.
    # C: others_mean=(0.40+0.50)/2=0.45, delta=+15 pp → no alert.
    df = pd.DataFrame(
        {
            "MES": ["ENERO 2026"] * 3,
            "LÍNEA DE NEGOCIO": ["A", "B", "C"],
            "CANTIDAD": [1, 1, 1],
            "TOTAL": [100.0, 100.0, 100.0],
            "COSTO 1": [60.0, 50.0, 40.0],
            "COSTO TOTAL DEL SERVICIO": [60.0, 50.0, 40.0],
            "UTILIDAD BRUTA": [40.0, 50.0, 60.0],
            "MARGEN BRUTO": [0.40, 0.50, 0.60],
            DATASET_SCOPE_COLUMN: [DEFAULT_DATASET_SCOPE] * 3,
        }
    )
    alerts = inefficient_line_alerts(df)
    assert {a.details["sucursal"] for a in alerts} == {"A"}


# ---------- combined ---------------------------------------------------------


def test_all_financial_alerts_combines_three_rules(cleaned):
    alerts = all_financial_alerts(cleaned, low_margin_benchmark=0.50)
    codes = {a.code for a in alerts}
    assert "low_margin" in codes
    assert "profit_concentration" in codes
    assert "inefficient_line" in codes


def test_alert_to_dict_envelope_shape():
    alert_list = profit_concentration_alerts(
        pd.DataFrame(
            {
                "MES": ["ENERO 2026", "ENERO 2026"],
                "LÍNEA DE NEGOCIO": ["X", "X"],
                "CANTIDAD": [1, 1],
                "TOTAL": [100.0, 100.0],
                "COSTO 1": [40.0, 60.0],
                "COSTO TOTAL DEL SERVICIO": [40.0, 60.0],
                "UTILIDAD BRUTA": [60.0, 40.0],
                "MARGEN BRUTO": [0.60, 0.40],
                "COL ESPECIAL 1": ["AA", "BB"],
                DATASET_SCOPE_COLUMN: [DEFAULT_DATASET_SCOPE] * 2,
            }
        )
    )
    assert alert_list, "expected at least one alert in this synthetic frame"
    envelope = alert_list[0].to_dict()
    assert set(envelope.keys()) == {"code", "severity", "message", "details"}
