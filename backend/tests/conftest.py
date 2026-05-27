import sys
from io import BytesIO
from pathlib import Path

# Make `app.*` importable without installing the package.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def fixtures_path() -> Path:
    return FIXTURES


@pytest.fixture
def read_fixture(fixtures_path: Path):
    def _read(name: str) -> bytes:
        return (fixtures_path / name).read_bytes()

    return _read


@pytest.fixture
def make_xlsx():
    """Build a multi-sheet workbook in memory.

    Lets us prove that `parse_excel` resolves sheets by NAME — never by index.
    """
    from openpyxl import Workbook

    def _build(sheets: dict[str, list[list]]) -> bytes:
        wb = Workbook()
        default = wb.active
        if default is not None:
            wb.remove(default)
        for name, rows in sheets.items():
            ws = wb.create_sheet(title=name)
            for row in rows:
                ws.append(row)
        buf = BytesIO()
        wb.save(buf)
        return buf.getvalue()

    return _build
