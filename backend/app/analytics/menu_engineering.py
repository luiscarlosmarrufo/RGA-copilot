"""Menu engineering quadrants (per sucursal-period).

Rule (docs/DATA_CONTRACTS.md § 3):

* Estrellas         — high volume / high margin
* Caballos de Batalla — high volume / low margin
* Puzzles           — low volume  / high margin
* Perros            — low volume  / low margin

"High" is defined as ``>= median`` of the (sucursal, period) group. Tie-break
on the median row is ``>=`` (i.e. items exactly at the median land on the HIGH
side of both axes — they become Estrellas, not Perros).
"""

from __future__ import annotations

from enum import StrEnum

import pandas as pd

from app.analytics.scope import assert_nama_only

VOLUME_COLUMN = "CANTIDAD"
MARGIN_COLUMN = "MARGEN BRUTO"
GROUP_COLUMNS: tuple[str, ...] = ("LÍNEA DE NEGOCIO", "MES")


class Quadrant(StrEnum):
    ESTRELLAS = "estrellas"
    CABALLOS_DE_BATALLA = "caballos_de_batalla"
    PUZZLES = "puzzles"
    PERROS = "perros"


def classify_menu(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``volumen``, ``margen_unitario`` and ``quadrant`` columns.

    The grouping happens **per (sucursal, period)** so each branch sets its
    own bar. Items with NaN volume or margin land in ``perros`` (lowest tier).

    Implementation uses ``groupby.transform`` to broadcast the per-group
    medians back over the original rows — avoids ``groupby.apply``, whose
    ``include_groups`` semantics changed in pandas 3.
    """
    assert_nama_only(df)
    work = df.copy()
    work["volumen"] = work[VOLUME_COLUMN]
    work["margen_unitario"] = work[MARGIN_COLUMN]

    grouped = work.groupby(list(GROUP_COLUMNS), sort=True)
    vol_median = grouped["volumen"].transform("median")
    margin_median = grouped["margen_unitario"].transform("median")

    high_vol = work["volumen"] >= vol_median
    high_margin = work["margen_unitario"] >= margin_median

    work["quadrant"] = Quadrant.PERROS.value
    work.loc[high_vol & high_margin, "quadrant"] = Quadrant.ESTRELLAS.value
    work.loc[high_vol & ~high_margin, "quadrant"] = Quadrant.CABALLOS_DE_BATALLA.value
    work.loc[~high_vol & high_margin, "quadrant"] = Quadrant.PUZZLES.value
    return work


def quadrant_counts(classified: pd.DataFrame) -> pd.DataFrame:
    """Tally items per quadrant per (sucursal, period)."""
    if "quadrant" not in classified.columns:
        raise ValueError("DataFrame must have been passed through classify_menu first")
    pivot = (
        classified.groupby([*GROUP_COLUMNS, "quadrant"], sort=True)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for q in Quadrant:
        if q.value not in pivot.columns:
            pivot[q.value] = 0
    return pivot[[*GROUP_COLUMNS, *(q.value for q in Quadrant)]]
