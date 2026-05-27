"""Typed error hierarchy for the parser and downstream layers.

Anything user-facing that originates here should be caught by the API layer
and rendered as the uniform error envelope documented in docs/API_SPEC.md.
"""

from __future__ import annotations

from typing import Any


class DataParserError(Exception):
    """Base class for all parser failures.

    Subclasses set a stable `code` used by the API error envelope.
    """

    code: str = "data_parser_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


class MissingSheetError(DataParserError):
    code = "missing_sheet"

    def __init__(self, sheet_name: str) -> None:
        super().__init__(
            f"Sheet '{sheet_name}' not found in workbook",
            details={"sheet_name": sheet_name},
        )


class MissingColumnError(DataParserError):
    code = "missing_column"

    def __init__(self, missing: list[str]) -> None:
        joined = ", ".join(missing)
        super().__init__(
            f"Missing required column(s): {joined}",
            details={"missing": missing},
        )


class MoneyParseError(DataParserError):
    code = "money_parse_error"

    def __init__(self, column: str, row_index: int, value: object) -> None:
        super().__init__(
            f"Cannot parse monetary value at row {row_index}, column '{column}': {value!r}",
            details={"column": column, "row_index": row_index, "value": str(value)},
        )


class RatioOutOfRangeError(DataParserError):
    code = "ratio_out_of_range"

    def __init__(self, column: str, row_index: int, value: float, allowed: tuple[float, float]) -> None:
        lo, hi = allowed
        super().__init__(
            f"Value {value!r} in column '{column}' at row {row_index} is outside the allowed ratio range [{lo}, {hi}]",
            details={"column": column, "row_index": row_index, "value": value, "allowed": [lo, hi]},
        )


class EncodingError(DataParserError):
    code = "encoding_error"


class UnsupportedFormatError(DataParserError):
    code = "unsupported_format"
