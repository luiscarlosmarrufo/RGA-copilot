import pandas as pd
import pytest

from app.analytics.menu_engineering import Quadrant, classify_menu, quadrant_counts
from app.parsers.data_parser import (
    DATASET_SCOPE_COLUMN,
    DEFAULT_DATASET_SCOPE,
    DataParser,
)


@pytest.fixture
def cleaned(read_fixture) -> pd.DataFrame:
    return DataParser().load_csv(read_fixture("analytics_sample.csv")).dataframe


def test_classify_menu_assigns_known_quadrants_for_ant(cleaned):
    classified = classify_menu(cleaned)
    ant = classified[classified["LÍNEA DE NEGOCIO"] == "ANT"].set_index("SUBCATEGORÍA 2")
    # Fixture is hand-tuned: ANT median volume = 75, median margin = 0.40.
    assert ant.loc["A", "quadrant"] == Quadrant.ESTRELLAS.value         # 100 vol, 0.60 margin
    assert ant.loc["B", "quadrant"] == Quadrant.CABALLOS_DE_BATALLA.value  # 200 vol, 0.20 margin
    assert ant.loc["C", "quadrant"] == Quadrant.PUZZLES.value           # 50 vol, 0.70 margin
    assert ant.loc["D", "quadrant"] == Quadrant.PERROS.value            # 20 vol, 0.10 margin


def test_classify_menu_is_per_sucursal_per_period(cleaned):
    classified = classify_menu(cleaned)
    # JUR rows all have margen 0.50 (a flat group). Median = 0.50; all items
    # are >= median, so margin axis is high for everyone. Volume axis splits.
    jur = classified[classified["LÍNEA DE NEGOCIO"] == "JUR"]
    # Volumes are [100, 150, 80, 40] → sorted [40, 80, 100, 150] → median 90.
    # >= 90 → high (100, 150); below → low (80, 40).
    jur_by_item = jur.set_index("SUBCATEGORÍA 2")
    assert jur_by_item.loc["A", "quadrant"] == Quadrant.ESTRELLAS.value  # 100 high vol
    assert jur_by_item.loc["B", "quadrant"] == Quadrant.ESTRELLAS.value  # 150 high vol
    assert jur_by_item.loc["C", "quadrant"] == Quadrant.PUZZLES.value    # 80 low vol, high margin
    assert jur_by_item.loc["D", "quadrant"] == Quadrant.PUZZLES.value    # 40 low vol, high margin


def test_classify_menu_tie_at_median_lands_on_high_side():
    df = pd.DataFrame(
        {
            "MES": ["ENERO 2026"] * 4,
            "LÍNEA DE NEGOCIO": ["TST"] * 4,
            "SUBCATEGORÍA 2": ["A", "B", "C", "D"],
            "CANTIDAD": [10, 10, 10, 10],
            "MARGEN BRUTO": [0.10, 0.10, 0.10, 0.10],
            DATASET_SCOPE_COLUMN: [DEFAULT_DATASET_SCOPE] * 4,
        }
    )
    classified = classify_menu(df)
    # All four tie at the median on both axes → all four are ESTRELLAS.
    assert (classified["quadrant"] == Quadrant.ESTRELLAS.value).all()


def test_quadrant_counts_returns_one_row_per_group(cleaned):
    classified = classify_menu(cleaned)
    counts = quadrant_counts(classified).set_index(["LÍNEA DE NEGOCIO", "MES"])

    # ANT/ENERO 2026: exactly one item in each quadrant.
    ant_enero = counts.loc[("ANT", "ENERO 2026")]
    assert ant_enero[Quadrant.ESTRELLAS.value] == 1
    assert ant_enero[Quadrant.CABALLOS_DE_BATALLA.value] == 1
    assert ant_enero[Quadrant.PUZZLES.value] == 1
    assert ant_enero[Quadrant.PERROS.value] == 1


def test_quadrant_counts_requires_classify_first(cleaned):
    with pytest.raises(ValueError):
        quadrant_counts(cleaned)  # missing `quadrant` column
