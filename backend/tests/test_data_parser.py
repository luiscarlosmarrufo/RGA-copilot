import pytest

from app.core.errors import (
    DataParserError,
    EncodingError,
    MissingColumnError,
    MissingSheetError,
    MoneyParseError,
    RatioOutOfRangeError,
)
from app.parsers.data_parser import (
    CANONICAL_SHEET_NAME,
    FINANCIAL_COLUMNS,
    REQUIRED_COLUMNS,
    DataParser,
)

# ---------- valid CSV parsing -------------------------------------------------


def test_valid_csv_parses(read_fixture):
    parser = DataParser()
    result = parser.parse_csv(read_fixture("valid.csv"))

    assert result.sheet_resolved is None  # CSV has no sheet concept
    assert result.row_count_original == 4
    assert result.row_count_cleaned == 4

    for col in REQUIRED_COLUMNS:
        assert result.required_columns_present[col] is True

    assert "MES" in result.columns_detected
    assert "LÍNEA DE NEGOCIO" in result.columns_detected

    assert len(result.sample_rows) > 0
    assert len(result.cleaned_data_preview) > 0


# ---------- missing required columns ------------------------------------------


def test_missing_required_columns_raises_typed_error(read_fixture):
    parser = DataParser()
    with pytest.raises(MissingColumnError) as exc_info:
        parser.parse_csv(read_fixture("missing_required_columns.csv"))

    err = exc_info.value
    assert isinstance(err, DataParserError)
    assert err.code == "missing_column"
    assert err.details["missing"]

    missing = set(err.details["missing"])
    assert "TOTAL" in missing
    assert "COSTO 1" in missing


# ---------- numeric conversion ------------------------------------------------


def test_financial_columns_are_floats(read_fixture):
    parser = DataParser()
    result = parser.parse_csv(read_fixture("valid.csv"))

    for row in result.cleaned_data_preview:
        for col in FINANCIAL_COLUMNS:
            if col not in row:
                continue
            value = row[col]
            if value is None:
                continue
            assert isinstance(value, (int, float))
            float(value)

    first_total = result.cleaned_data_preview[0]["TOTAL"]
    assert first_total == pytest.approx(1160.0)

    first_margin = result.cleaned_data_preview[0]["MARGEN BRUTO"]
    assert first_margin == pytest.approx(0.70)


def test_cantidad_becomes_integer(read_fixture):
    parser = DataParser()
    result = parser.parse_csv(read_fixture("valid.csv"))
    first_qty = result.cleaned_data_preview[0]["CANTIDAD"]
    assert isinstance(first_qty, int)
    assert first_qty == 100


# ---------- category cleanup --------------------------------------------------


def test_category_cleanup_strips_asterisks_and_periods(read_fixture):
    parser = DataParser()
    result = parser.parse_csv(read_fixture("needs_cleaning.csv"))

    for row in result.cleaned_data_preview:
        for key, value in row.items():
            if isinstance(value, str) and value:
                assert not value.startswith("*"), f"value still starts with *: {value!r} (col {key})"
                assert not value.endswith("."), f"value still ends with .: {value!r} (col {key})"

    assert result.cleaned_data_preview[0]["LÍNEA DE NEGOCIO"] == "ANT"
    assert result.cleaned_data_preview[0]["SUBCATEGORÍA 1"] == "Alimentos"
    assert result.cleaned_data_preview[0]["SUBCATEGORÍA 2"] == "YAKIMESHI MIXTO"

    joined_warnings = "\n".join(result.warnings)
    assert "Stripped leading '*'" in joined_warnings
    assert "Stripped trailing '.'" in joined_warnings


# ---------- TOTAL == 0 filtering ---------------------------------------------


def test_total_zero_rows_are_dropped(read_fixture):
    parser = DataParser()
    result = parser.parse_csv(read_fixture("with_total_zero.csv"))

    assert result.row_count_original == 4
    assert result.row_count_cleaned == 2

    for row in result.cleaned_data_preview:
        assert row["TOTAL"] != 0

    assert any("TOTAL == 0" in w for w in result.warnings)


# ---------- DataParserError behavior -----------------------------------------


def test_dataparser_error_to_dict_envelope():
    err = MissingColumnError(["MES", "TOTAL"])
    assert isinstance(err, DataParserError)
    envelope = err.to_dict()
    assert envelope["code"] == "missing_column"
    assert "MES" in envelope["message"]
    assert envelope["details"]["missing"] == ["MES", "TOTAL"]


def test_missing_sheet_error_carries_sheet_name():
    err = MissingSheetError("BD 2026")
    assert err.code == "missing_sheet"
    assert err.details["sheet_name"] == "BD 2026"
    assert "BD 2026" in err.message


def test_excel_path_refuses_empty_sheet_name():
    parser = DataParser()
    with pytest.raises(DataParserError) as exc_info:
        parser.parse_excel(b"unused", sheet_name="")
    assert "sheet_name" in exc_info.value.message


def test_excel_default_sheet_is_bd_2026():
    assert CANONICAL_SHEET_NAME == "BD 2026"


# ---------- typed error coverage ---------------------------------------------


def test_money_parse_error_raises_on_unparseable_value(read_fixture):
    parser = DataParser()
    with pytest.raises(MoneyParseError) as exc_info:
        parser.parse_csv(read_fixture("bad_money.csv"))
    err = exc_info.value
    assert err.code == "money_parse_error"
    assert err.details["column"] == "TOTAL"
    assert "not-a-number" in err.details["value"]


def test_ratio_out_of_range_raises_for_margen_bruto(read_fixture):
    parser = DataParser()
    with pytest.raises(RatioOutOfRangeError) as exc_info:
        parser.parse_csv(read_fixture("bad_ratio.csv"))
    err = exc_info.value
    assert err.code == "ratio_out_of_range"
    assert err.details["column"] == "MARGEN BRUTO"
    assert err.details["value"] == pytest.approx(2.40)


def test_encoding_error_raises_on_non_utf8():
    # 'LÍNEA' encoded in latin-1 yields a byte sequence (0xCD) that is invalid
    # as the first byte of a UTF-8 multi-byte character when followed by ASCII.
    raw = "MES,LÍNEA DE NEGOCIO,CANTIDAD,TOTAL,COSTO 1,COSTO TOTAL DEL SERVICIO,UTILIDAD BRUTA,MARGEN BRUTO\nENERO 2026,ANT,1,1,1,1,1,0.5\n".encode(
        "latin-1"
    )
    parser = DataParser()
    with pytest.raises(EncodingError):
        parser.parse_csv(raw)


# ---------- Excel multi-sheet round-trip -------------------------------------


def _required_headers_row() -> list[str]:
    return list(REQUIRED_COLUMNS)


def _valid_data_row() -> list[str]:
    # MES, LÍNEA DE NEGOCIO, CANTIDAD, TOTAL, COSTO 1, COSTO TOTAL DEL SERVICIO, UTILIDAD BRUTA, MARGEN BRUTO
    return ["ENERO 2026", "ANT", "100", "1160.00", "300.00", "348.00", "812.00", "0.70"]


def test_excel_resolves_bd_2026_not_first_sheet(make_xlsx):
    decoy_rows = [["IGNORE", "ME"], ["a", "b"]]
    bd_rows = [_required_headers_row(), _valid_data_row()]
    xlsx_bytes = make_xlsx({"DECOY FIRST SHEET": decoy_rows, "BD 2026": bd_rows})

    parser = DataParser()
    result = parser.parse_excel(xlsx_bytes)

    assert result.sheet_resolved == "BD 2026"
    assert result.row_count_original == 1
    assert all(result.required_columns_present[c] for c in REQUIRED_COLUMNS)
    assert result.cleaned_data_preview[0]["TOTAL"] == pytest.approx(1160.0)


def test_excel_missing_bd_2026_raises_missing_sheet(make_xlsx):
    xlsx_bytes = make_xlsx(
        {
            "RESUMEN": [["A", "B"], ["x", "y"]],
            "OTRA HOJA": [["C", "D"], ["1", "2"]],
        }
    )
    parser = DataParser()
    with pytest.raises(MissingSheetError) as exc_info:
        parser.parse_excel(xlsx_bytes)
    assert exc_info.value.details["sheet_name"] == "BD 2026"


# ---------- API surface ------------------------------------------------------


def test_upload_endpoint_returns_parse_result(client, read_fixture):
    files = {"file": ("valid.csv", read_fixture("valid.csv"), "text/csv")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 202
    body = response.json()
    assert body["sheet_resolved"] is None
    assert body["row_count_original"] == 4
    assert body["row_count_cleaned"] == 4
    assert all(body["required_columns_present"][c] for c in REQUIRED_COLUMNS)


def test_upload_endpoint_xlsx_returns_sheet_resolved(client, make_xlsx):
    bd_rows = [_required_headers_row(), _valid_data_row()]
    xlsx_bytes = make_xlsx({"INDEX SHEET": [["junk"]], "BD 2026": bd_rows})
    files = {
        "file": (
            "workbook.xlsx",
            xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post("/api/upload", files=files)
    assert response.status_code == 202
    body = response.json()
    assert body["sheet_resolved"] == "BD 2026"


def test_upload_endpoint_returns_typed_error_on_missing_columns(client, read_fixture):
    files = {
        "file": (
            "missing_required_columns.csv",
            read_fixture("missing_required_columns.csv"),
            "text/csv",
        )
    }
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "missing_column"
    assert "missing" in body["error"]["details"]


def test_upload_endpoint_rejects_unsupported_format(client):
    files = {"file": ("notes.txt", b"hello", "text/plain")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 415
    body = response.json()
    assert body["error"]["code"] == "unsupported_format"
