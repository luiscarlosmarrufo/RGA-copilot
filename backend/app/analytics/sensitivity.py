"""Cost sensitivity analysis.

Models a multiplicative shock to the cost columns and recomputes the derived
financial fields. The default ``factor=1.05`` implements the standard "5%
input cost increase" scenario from docs/DATA_CONTRACTS.md § 2.
"""

from __future__ import annotations

import pandas as pd

from app.analytics.scope import assert_nama_only

# Cost columns shocked together. ``COSTO 2..50`` are sparse and intentionally
# excluded from Phase 2; revisit when those slots actually carry data.
COST_COLUMNS_TO_SHOCK: tuple[str, ...] = (
    "COSTO 1",
    "COSTO TOTAL SIN IVA",
    "COSTO TOTAL DEL SERVICIO",
)


def shock_costs(df: pd.DataFrame, *, factor: float = 1.05) -> pd.DataFrame:
    """Return a copy of ``df`` with cost columns multiplied by ``factor`` and
    the derived ``UTILIDAD BRUTA`` / ``MARGEN BRUTO`` recomputed.

    Volume (``CANTIDAD``) and revenue (``TOTAL``) are not touched — the
    scenario simulates a pure cost shock with all else equal.
    """
    assert_nama_only(df)
    if factor < 0:
        raise ValueError("factor must be non-negative")
    out = df.copy()
    for col in COST_COLUMNS_TO_SHOCK:
        if col in out.columns:
            out[col] = out[col] * factor

    out["UTILIDAD BRUTA"] = out["TOTAL"] - out["COSTO TOTAL DEL SERVICIO"]
    safe_total = out["TOTAL"].where(out["TOTAL"] > 0)
    out["MARGEN BRUTO"] = out["UTILIDAD BRUTA"] / safe_total
    return out
