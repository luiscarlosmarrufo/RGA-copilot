"""RGA data parser.

Phase 1 scope: CSV input fully supported; Excel input wired through the same
pipeline but **must** target the `BD 2026` sheet by name. The parser never
defaults to sheet index 0.

The cleaning pipeline is deterministic and intentionally short:

  1. normalize column headers (NFC + whitespace trim)
  2. validate required columns; raise `MissingColumnError` on absence
  3. clean string columns: strip leading `*` and trailing `.`
  4. convert financial columns to float; CANTIDAD to nullable Int64
  5. drop rows where TOTAL == 0

Each step that drops or rewrites data records a row-count note in `warnings`.
"""

from __future__ import annotations

import re
import unicodedata
from io import BytesIO
from pathlib import Path
from typing import IO

import pandas as pd

from app.core.errors import (
    DataParserError,
    EncodingError,
    MissingColumnError,
    MissingSheetError,
    MoneyParseError,
    RatioOutOfRangeError,
)
from app.schemas.parser import ParseResult

REQUIRED_COLUMNS: tuple[str, ...] = (
    "MES",
    "LÍNEA DE NEGOCIO",
    "CANTIDAD",
    "TOTAL",
    "COSTO 1",
    "COSTO TOTAL DEL SERVICIO",
    "UTILIDAD BRUTA",
    "MARGEN BRUTO",
)

FINANCIAL_COLUMNS: tuple[str, ...] = (
    "TOTAL",
    "COSTO 1",
    "COSTO TOTAL DEL SERVICIO",
    "UTILIDAD BRUTA",
    "MARGEN BRUTO",
    "SUBTOTAL",
    "COSTO TOTAL SIN IVA",
)

INTEGER_COLUMNS: tuple[str, ...] = ("CANTIDAD",)

RATIO_COLUMNS: tuple[str, ...] = ("MARGEN BRUTO",)
RATIO_ALLOWED_RANGE: tuple[float, float] = (0.0, 1.5)

CANONICAL_SHEET_NAME = "BD 2026"
PREVIEW_ROWS = 5

_MONEY_STRIP_RE = re.compile(r"[\s\"'$,]")

CsvSource = str | Path | bytes | bytearray | IO[bytes] | IO[str]
ExcelSource = str | Path | bytes | bytearray | IO[bytes]


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


class DataParser:
    """Parser for RGA workbooks.

    Construction is parameterless on purpose; per-call options live on the
    `parse_*` methods so the parser can be reused across requests.
    """

    # ----- public entry points ----------------------------------------

    def parse_csv(self, source: CsvSource) -> ParseResult:
        df = self._read_csv(source)
        return self._process(df, sheet_resolved=None)

    def parse_excel(
        self,
        source: ExcelSource,
        *,
        sheet_name: str = CANONICAL_SHEET_NAME,
    ) -> ParseResult:
        if not sheet_name:
            raise DataParserError(
                "sheet_name must be provided; the parser never defaults to sheet index 0",
                details={"reason": "empty_sheet_name"},
            )
        df = self._read_excel(source, sheet_name=sheet_name)
        return self._process(df, sheet_resolved=sheet_name)

    # ----- IO ----------------------------------------------------------

    def _read_csv(self, source: CsvSource) -> pd.DataFrame:
        try:
            if isinstance(source, (bytes, bytearray)):
                buf = BytesIO(bytes(source))
                return pd.read_csv(buf, dtype=str, keep_default_na=False, encoding="utf-8")
            return pd.read_csv(source, dtype=str, keep_default_na=False, encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise EncodingError(f"CSV is not valid UTF-8: {exc}") from exc

    def _read_excel(self, source: ExcelSource, *, sheet_name: str) -> pd.DataFrame:
        try:
            if isinstance(source, (bytes, bytearray)):
                source = BytesIO(bytes(source))
            return pd.read_excel(source, sheet_name=sheet_name, dtype=str)
        except ValueError as exc:
            text = str(exc)
            if "Worksheet" in text or "sheet" in text.lower():
                raise MissingSheetError(sheet_name) from exc
            raise
        except KeyError as exc:
            # Some openpyxl paths raise KeyError for missing sheet names.
            raise MissingSheetError(sheet_name) from exc

    # ----- pipeline ----------------------------------------------------

    def _process(self, df: pd.DataFrame, *, sheet_resolved: str | None) -> ParseResult:
        warnings: list[str] = []

        df, header_warnings = self._normalize_headers(df)
        warnings.extend(header_warnings)

        columns_detected = list(df.columns)
        self._validate_required(df)
        required_present = {c: (c in df.columns) for c in REQUIRED_COLUMNS}
        row_count_original = len(df)
        sample_rows = self._records_preview(df, PREVIEW_ROWS)

        df, cleaning_warnings = self._clean_string_columns(df)
        warnings.extend(cleaning_warnings)

        df = self._convert_numeric(df)
        self._validate_ratios(df)

        df, dropped_zero = self._drop_zero_total(df)
        if dropped_zero:
            warnings.append(f"Dropped {dropped_zero} row(s) where TOTAL == 0")

        cleaned_preview = self._records_preview(df, PREVIEW_ROWS)

        return ParseResult(
            sheet_resolved=sheet_resolved,
            row_count_original=row_count_original,
            row_count_cleaned=len(df),
            columns_detected=columns_detected,
            required_columns_present=required_present,
            sample_rows=sample_rows,
            cleaned_data_preview=cleaned_preview,
            warnings=warnings,
        )

    # ----- steps -------------------------------------------------------

    @staticmethod
    def _normalize_headers(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        warnings: list[str] = []
        original = list(df.columns)
        new_cols = [_nfc(c).strip() if isinstance(c, str) else c for c in original]
        if new_cols != original:
            warnings.append("Normalized column headers (whitespace / Unicode NFC)")
        df.columns = new_cols
        return df, warnings

    @staticmethod
    def _validate_required(df: pd.DataFrame) -> None:
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise MissingColumnError(missing)

    @staticmethod
    def _clean_string_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        warnings: list[str] = []
        # Everything is read as strings on ingest; exclude only the columns we
        # know are numeric. Dtype-based filtering breaks on pandas >=3 where
        # the default string dtype is `str` rather than `object`.
        numeric = set(FINANCIAL_COLUMNS) | set(INTEGER_COLUMNS)
        string_cols = [c for c in df.columns if c not in numeric]
        for col in string_cols:
            series = df[col].astype(str).map(_nfc).str.strip()
            asterisk_count = int(series.str.startswith("*").sum())
            period_count = int(series.str.endswith(".").sum())
            series = series.str.replace(r"^\*+", "", regex=True)
            series = series.str.replace(r"\.+$", "", regex=True)
            series = series.str.strip()
            df[col] = series
            if asterisk_count:
                warnings.append(
                    f"Stripped leading '*' in column '{col}' ({asterisk_count} row(s))"
                )
            if period_count:
                warnings.append(
                    f"Stripped trailing '.' in column '{col}' ({period_count} row(s))"
                )
        return df, warnings

    @staticmethod
    def _parse_money_value(raw: object, column: str, row_index: int) -> float | None:
        """Strict monetary parser.

        Empty cells return None (rendered as NaN downstream). Anything that
        can't be normalized into a float raises `MoneyParseError` — the parser
        does not silently coerce malformed financial values.
        """
        if raw is None:
            return None
        if isinstance(raw, bool):
            raise MoneyParseError(column, row_index, raw)
        if isinstance(raw, (int, float)):
            return float(raw)
        s = str(raw).strip()
        if not s:
            return None
        cleaned = _MONEY_STRIP_RE.sub("", s)
        if cleaned in {"", "-", "+"}:
            return None
        try:
            return float(cleaned)
        except ValueError as exc:
            raise MoneyParseError(column, row_index, raw) from exc

    @classmethod
    def _convert_numeric(cls, df: pd.DataFrame) -> pd.DataFrame:
        for col in FINANCIAL_COLUMNS:
            if col not in df.columns:
                continue
            parsed = [
                cls._parse_money_value(raw, col, idx)
                for idx, raw in enumerate(df[col].tolist())
            ]
            df[col] = pd.array(parsed, dtype="float64")
        for col in INTEGER_COLUMNS:
            if col not in df.columns:
                continue
            parsed = [
                cls._parse_money_value(raw, col, idx)
                for idx, raw in enumerate(df[col].tolist())
            ]
            df[col] = pd.array(
                [int(v) if v is not None and pd.notna(v) else pd.NA for v in parsed],
                dtype="Int64",
            )
        return df

    @staticmethod
    def _validate_ratios(df: pd.DataFrame) -> None:
        lo, hi = RATIO_ALLOWED_RANGE
        for col in RATIO_COLUMNS:
            if col not in df.columns:
                continue
            for idx, value in enumerate(df[col].tolist()):
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    continue
                if value < lo or value > hi:
                    raise RatioOutOfRangeError(col, idx, float(value), RATIO_ALLOWED_RANGE)

    @staticmethod
    def _drop_zero_total(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        if "TOTAL" not in df.columns:
            return df, 0
        mask = df["TOTAL"].fillna(0) == 0
        dropped = int(mask.sum())
        if dropped:
            df = df.loc[~mask].reset_index(drop=True)
        return df, dropped

    # ----- preview helpers --------------------------------------------

    @staticmethod
    def _records_preview(df: pd.DataFrame, n: int) -> list[dict]:
        if df.empty:
            return []
        head = df.head(n).copy()
        # JSON-serializable: pd.NA / NaN -> None; Int64 -> int; numpy floats -> float.
        records: list[dict] = []
        for row in head.to_dict(orient="records"):
            clean_row: dict = {}
            for k, v in row.items():
                if v is pd.NA or (isinstance(v, float) and pd.isna(v)):
                    clean_row[k] = None
                elif hasattr(v, "item"):
                    clean_row[k] = v.item()
                else:
                    clean_row[k] = v
            records.append(clean_row)
        return records
