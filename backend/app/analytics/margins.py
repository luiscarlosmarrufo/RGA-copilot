"""Margin analytics.

Canonical formulas (see docs/DATA_CONTRACTS.md § 2):

* ``utilidad_bruta = TOTAL - COSTO TOTAL DEL SERVICIO``
* ``margen_bruto  = utilidad_bruta / TOTAL``   (NaN when TOTAL <= 0)
* ``cost_leakage  = COSTO TOTAL DEL SERVICIO - COSTO 1``

All functions are pure: ``(DataFrame, params) -> Series | DataFrame``. The
caller is responsible for slicing the DataFrame before calling — these
functions don't filter rows beyond what their formula requires.
"""

from __future__ import annotations

import pandas as pd

from app.analytics.scope import assert_nama_only


def utilidad_bruta(df: pd.DataFrame) -> pd.Series:
    assert_nama_only(df)
    return df["TOTAL"] - df["COSTO TOTAL DEL SERVICIO"]


def margen_bruto(df: pd.DataFrame) -> pd.Series:
    assert_nama_only(df)
    total = df["TOTAL"]
    safe_total = total.where(total > 0)  # NaN where TOTAL <= 0
    return utilidad_bruta(df) / safe_total


def cost_leakage(df: pd.DataFrame) -> pd.Series:
    assert_nama_only(df)
    return df["COSTO TOTAL DEL SERVICIO"] - df["COSTO 1"]


def cost_leakage_ratio(df: pd.DataFrame) -> pd.Series:
    """Cost leakage as a fraction of ``COSTO TOTAL DEL SERVICIO``.

    NaN where ``COSTO TOTAL DEL SERVICIO`` is zero or missing.
    """
    assert_nama_only(df)
    denom = df["COSTO TOTAL DEL SERVICIO"]
    safe_denom = denom.where(denom > 0)
    return cost_leakage(df) / safe_denom


def aggregate_margins_per_sucursal(df: pd.DataFrame) -> pd.DataFrame:
    """Per-sucursal totals + recomputed margen bruto.

    Output columns:
        ``LÍNEA DE NEGOCIO``, ``ventas_total``, ``costo_total``,
        ``cantidad_total``, ``utilidad_bruta``, ``margen_bruto``.
    """
    assert_nama_only(df)
    grouped = (
        df.groupby("LÍNEA DE NEGOCIO", sort=True)
        .agg(
            ventas_total=("TOTAL", "sum"),
            costo_total=("COSTO TOTAL DEL SERVICIO", "sum"),
            cantidad_total=("CANTIDAD", "sum"),
        )
        .reset_index()
    )
    grouped["utilidad_bruta"] = grouped["ventas_total"] - grouped["costo_total"]
    safe_ventas = grouped["ventas_total"].where(grouped["ventas_total"] > 0)
    grouped["margen_bruto"] = grouped["utilidad_bruta"] / safe_ventas
    return grouped
