"""Deterministic financial alerts (Phase 2 subset).

Three rules from docs/DATA_CONTRACTS.md § 4 — the Maps and Trends alerts
depend on Phase 4 data sources and are intentionally omitted here:

* ``low_margin``            — sucursal margin > 5 pp below the benchmark.
* ``profit_concentration``  — a single ``COL ESPECIAL 1`` item carries
                              more than 40% (MEDIUM) / 50% (HIGH) of profit.
* ``inefficient_line``      — sucursal margin > 2 pp below the mean of the
                              other sucursales.

All severities and message templates are Spanish-ready strings; the message
text itself stays English-templated at this layer and is localized in the UI
i18n catalog in Phase 6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from app.analytics.margins import aggregate_margins_per_sucursal, utilidad_bruta
from app.analytics.scope import assert_nama_only

Severity = str  # "MEDIUM" | "HIGH"

# Boundary precision: a value within 1e-6 pp of a strict threshold is treated
# as on the boundary (does not fire). Required because expressions like
# (0.50 - 0.52) * 100 evaluate to -2.0000000000000018 under IEEE-754.
_PP_DECIMALS = 6


def _strictly_below_pp(value: float, reference: float, threshold_pp: float) -> tuple[bool, float]:
    """Return (fires, delta_pp) where fires == True iff ``value`` is strictly
    more than ``threshold_pp`` percentage points below ``reference``.
    """
    delta_pp = (value - reference) * 100.0
    return round(delta_pp, _PP_DECIMALS) < -threshold_pp, delta_pp


@dataclass(frozen=True)
class Alert:
    code: str
    severity: Severity
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


# ---- low margin --------------------------------------------------------


def low_margin_alerts(df: pd.DataFrame, *, benchmark: float) -> list[Alert]:
    """Sucursales with margen bruto more than 5 pp below ``benchmark`` (ratio).

    ``benchmark`` is expressed as a ratio (e.g. ``0.65`` for 65%).
    """
    assert_nama_only(df)
    margins = aggregate_margins_per_sucursal(df)
    out: list[Alert] = []
    for _, row in margins.iterrows():
        margin = row["margen_bruto"]
        if pd.isna(margin):
            continue
        fires, delta_pp = _strictly_below_pp(float(margin), benchmark, 5.0)
        if not fires:
            continue
        out.append(
            Alert(
                code="low_margin",
                severity="HIGH",
                message=(
                    f"Sucursal {row['LÍNEA DE NEGOCIO']} con margen "
                    f"{abs(delta_pp):.1f} pp por debajo del benchmark."
                ),
                details={
                    "sucursal": row["LÍNEA DE NEGOCIO"],
                    "margen_bruto": float(margin),
                    "benchmark": benchmark,
                    "delta_pp": delta_pp,
                },
            )
        )
    return out


# ---- profit concentration ---------------------------------------------


def profit_concentration_alerts(
    df: pd.DataFrame,
    *,
    tag_column: str = "COL ESPECIAL 1",
    medium_threshold: float = 0.40,
    high_threshold: float = 0.50,
) -> list[Alert]:
    """Single ``COL ESPECIAL 1`` tag carrying disproportionate profit.

    Returns one alert per offending tag. Severity is HIGH when the tag's
    share of utilidad bruta exceeds ``high_threshold`` (default 50%), MEDIUM
    when it exceeds ``medium_threshold`` (40%) but not 50%.
    """
    assert_nama_only(df)
    if tag_column not in df.columns:
        return []
    work = df[[tag_column]].copy()
    work["utilidad_bruta"] = utilidad_bruta(df)
    total_profit = work["utilidad_bruta"].sum()
    if not total_profit or pd.isna(total_profit) or total_profit <= 0:
        return []
    grouped = (
        work.groupby(tag_column, sort=True, dropna=True)["utilidad_bruta"].sum().reset_index()
    )
    out: list[Alert] = []
    for _, row in grouped.iterrows():
        share = float(row["utilidad_bruta"]) / float(total_profit)
        if share <= medium_threshold:
            continue
        severity = "HIGH" if share > high_threshold else "MEDIUM"
        out.append(
            Alert(
                code="profit_concentration",
                severity=severity,
                message=(
                    f"La categoría '{row[tag_column]}' concentra {share * 100:.1f}% "
                    f"de la utilidad bruta."
                ),
                details={
                    "tag": row[tag_column],
                    "share": share,
                    "utilidad_bruta": float(row["utilidad_bruta"]),
                    "total_utilidad_bruta": float(total_profit),
                },
            )
        )
    return out


# ---- inefficient business line ----------------------------------------


def inefficient_line_alerts(df: pd.DataFrame, *, threshold_pp: float = 2.0) -> list[Alert]:
    """Sucursales whose margin is more than ``threshold_pp`` pp below the mean
    margin of the OTHER sucursales (each line is compared against the rest).
    """
    assert_nama_only(df)
    margins = aggregate_margins_per_sucursal(df).dropna(subset=["margen_bruto"])
    if margins.empty or len(margins) < 2:
        return []
    out: list[Alert] = []
    total_margin = margins["margen_bruto"].sum()
    n = len(margins)
    for _, row in margins.iterrows():
        # Mean of the other lines = (total - this) / (n - 1).
        others_mean = (total_margin - float(row["margen_bruto"])) / (n - 1)
        fires, delta_pp = _strictly_below_pp(
            float(row["margen_bruto"]), others_mean, threshold_pp
        )
        if not fires:
            continue
        out.append(
            Alert(
                code="inefficient_line",
                severity="MEDIUM",
                message=(
                    f"Sucursal {row['LÍNEA DE NEGOCIO']} opera "
                    f"{abs(delta_pp):.1f} pp por debajo del promedio de las "
                    f"otras sucursales."
                ),
                details={
                    "sucursal": row["LÍNEA DE NEGOCIO"],
                    "margen_bruto": float(row["margen_bruto"]),
                    "others_mean_margen_bruto": float(others_mean),
                    "delta_pp": delta_pp,
                },
            )
        )
    return out


def all_financial_alerts(
    df: pd.DataFrame,
    *,
    low_margin_benchmark: float,
) -> list[Alert]:
    """Convenience: run all Phase 2 alert rules in one pass."""
    return (
        low_margin_alerts(df, benchmark=low_margin_benchmark)
        + profit_concentration_alerts(df)
        + inefficient_line_alerts(df)
    )
