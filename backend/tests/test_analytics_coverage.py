import pandas as pd

from app.analytics.coverage import (
    DEFAULT_DECLARED_WINDOW,
    compute_period_coverage,
    missing_period_warning,
)


def _df_with_months(months: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"MES": months})


def test_coverage_with_all_months_present_has_no_missing():
    df = _df_with_months(list(DEFAULT_DECLARED_WINDOW))
    cov = compute_period_coverage(df)
    assert cov.actual == DEFAULT_DECLARED_WINDOW
    assert cov.missing == ()
    assert cov.has_missing is False
    assert missing_period_warning(cov) is None


def test_coverage_with_missing_april_flags_it():
    df = _df_with_months(["ENERO 2026", "FEBRERO 2026", "MARZO 2026"])
    cov = compute_period_coverage(df)
    assert cov.actual == ("ENERO 2026", "FEBRERO 2026", "MARZO 2026")
    assert cov.missing == ("ABRIL 2026",)
    warning = missing_period_warning(cov)
    assert warning is not None
    assert warning["code"] == "missing_periods"
    assert warning["missing"] == ["ABRIL 2026"]
    assert warning["actual"] == ["ENERO 2026", "FEBRERO 2026", "MARZO 2026"]
    assert warning["declared"] == list(DEFAULT_DECLARED_WINDOW)


def test_coverage_preserves_declared_order_in_outputs():
    df = _df_with_months(["MARZO 2026", "ENERO 2026"])  # out of order in source
    cov = compute_period_coverage(df)
    assert cov.actual == ("ENERO 2026", "MARZO 2026")
    assert cov.missing == ("FEBRERO 2026", "ABRIL 2026")


def test_coverage_with_unexpected_month_surfaces_it_separately():
    df = _df_with_months(["ENERO 2026", "FEBRERO 2026", "MARZO 2026", "MAYO 2026"])
    cov = compute_period_coverage(df)
    assert cov.actual == ("ENERO 2026", "FEBRERO 2026", "MARZO 2026")
    assert cov.missing == ("ABRIL 2026",)
    assert cov.unexpected == ("MAYO 2026",)


def test_coverage_when_column_absent_treats_everything_as_missing():
    df = pd.DataFrame({"OTHER_COLUMN": [1, 2]})
    cov = compute_period_coverage(df)
    assert cov.actual == ()
    assert cov.missing == DEFAULT_DECLARED_WINDOW
    assert missing_period_warning(cov) is not None


def test_coverage_supports_overridden_declared_window():
    df = _df_with_months(["MAYO 2026", "JUNIO 2026"])
    cov = compute_period_coverage(df, declared=("MAYO 2026", "JUNIO 2026", "JULIO 2026"))
    assert cov.actual == ("MAYO 2026", "JUNIO 2026")
    assert cov.missing == ("JULIO 2026",)
