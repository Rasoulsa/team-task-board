from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "errors": [{"message": exc.message}]},
    )
