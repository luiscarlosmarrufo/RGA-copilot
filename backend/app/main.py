from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes import health, upload
from app.core.errors import DataParserError, UnsupportedFormatError


def create_app() -> FastAPI:
    app = FastAPI(
        title="RGA Financial Copilot API",
        version=__version__,
        description="Phase 1: backend skeleton + deterministic parser",
    )
    app.include_router(health.router)
    app.include_router(upload.router)

    @app.exception_handler(DataParserError)
    async def _parser_error_handler(_request: Request, exc: DataParserError) -> JSONResponse:
        status_code = 415 if isinstance(exc, UnsupportedFormatError) else 400
        return JSONResponse(status_code=status_code, content={"error": exc.to_dict()})

    return app


app = create_app()
