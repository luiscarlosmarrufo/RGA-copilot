from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ParseResult(BaseModel):
    """Structured output of the data parser.

    Mirrors the JSON contract documented in docs/DATA_CONTRACTS.md. Future
    phases extend this model with persistence ids; never break field names.
    """

    sheet_resolved: str | None = None
    row_count_original: int
    row_count_cleaned: int
    columns_detected: list[str]
    required_columns_present: dict[str, bool]
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)
    cleaned_data_preview: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
