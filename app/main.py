from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.graph import run_agent
from app.guardrails import ALLOWED_TOPICS
from app.schemas import HealthResponse, QueryRequest


app = FastAPI(
    title="Guardrailed AI Agent",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "reason": "Invalid request payload", "details": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "reason": str(exc.detail)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(_: Request, __: Exception):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "reason": "Internal server error"},
    )


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.get("/agent/scope")
def scope():
    return {
        "status": "success",
        "scope": {
            "allowed_topics": ALLOWED_TOPICS,
            "default_policy": "reject",
            "response_format": "json_only",
        },
    }


@app.post("/agent/query")
def query_agent(payload: QueryRequest):
    return run_agent(payload.query)
