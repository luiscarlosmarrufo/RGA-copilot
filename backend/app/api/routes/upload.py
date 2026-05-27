from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.core.errors import UnsupportedFormatError
from app.parsers.data_parser import DataParser
from app.schemas.parser import ParseResult

router = APIRouter(prefix="/api", tags=["upload"])


@router.post(
    "/upload",
    response_model=ParseResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload(file: Annotated[UploadFile, File()]) -> ParseResult:
    name = (file.filename or "").lower()
    contents = await file.read()
    parser = DataParser()
    if name.endswith(".csv"):
        return parser.parse_csv(contents)
    if name.endswith((".xlsx", ".xls")):
        return parser.parse_excel(contents)
    raise UnsupportedFormatError(
        f"Unsupported file extension for '{file.filename}'. Expected .csv, .xlsx, or .xls.",
        details={"filename": file.filename},
    )
