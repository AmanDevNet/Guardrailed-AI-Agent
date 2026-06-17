from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.graph import run_agent
from app.guardrails import ALLOWED_TOPICS
from app.schemas import HealthResponse, QueryRequest

# =====================================================================
# FASTAPI APPLICATION SETUP
# =====================================================================
# We instantiate FastAPI. Crucially, we disable 'docs_url', 'redoc_url', 
# and 'openapi_url' by setting them to None. This prevents exposure of the 
# API schema endpoints (/docs, /redoc, /openapi.json) in production environments, 
# mitigating footprint reconnaissance by malicious actors.
app = FastAPI(
    title="Guardrailed AI Agent",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


# =====================================================================
# GLOBAL EXCEPTION HANDLERS
# =====================================================================
# By defining custom exception handlers, we ensure that the API always
# replies in a predictable JSON structure instead of raw traceback strings 
# or default HTML pages. This adheres to our "JSON Only" design spec.

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    """
    Triggers when client request payload fails Pydantic schema validation.
    Returns HTTP 422 with a structured error explanation.
    """
    return JSONResponse(
        status_code=422,
        content={"status": "error", "reason": "Invalid request payload", "details": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    """
    Triggers on HTTP routing errors (like 404 Not Found) or custom raise statements.
    Ensures HTTP errors are formatted in JSON.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "reason": str(exc.detail)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(_: Request, __: Exception):
    """
    Catch-all handler for unhandled backend exceptions.
    Masks internal backend tracebacks to avoid leaking infrastructure details, 
    returning a clean HTTP 500 JSON payload instead.
    """
    return JSONResponse(
        status_code=500,
        content={"status": "error", "reason": "Internal server error"},
    )


# =====================================================================
# ENDPOINTS
# =====================================================================

@app.get("/health", response_model=HealthResponse)
def health():
    """
    Simple Liveness/Readiness probe endpoint.
    Used by docker-compose, orchestrators, or load balancers to check service status.
    """
    return {"status": "ok"}


@app.get("/agent/scope")
def scope():
    """
    Metadata endpoint. Exposes the allowed web scraping scope topics, 
    our default policy (reject), and our mandatory response format (json_only).
    Allows calling clients to know boundaries before sending requests.
    """
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
    """
    Primary agent interface. 
    Accepts validated query, passes it to the LangGraph execution flow,
    and returns either a SuccessResponse or RejectionResponse.
    """
    return run_agent(payload.query)
