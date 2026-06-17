from typing import Literal

from pydantic import BaseModel, Field

# =====================================================================
# DATA VALIDATION SCHEMAS (Pydantic models)
# =====================================================================
# We use Pydantic (v2) to validate incoming JSON payloads and enforce
# strict outgoing response models. This ensures runtime type safety and
# prevents malformed requests from consuming backend processing power.


class QueryRequest(BaseModel):
    """
    Validates incoming user query payload for POST /agent/query.
    - query: Must be a string.
    - min_length=1: Rejects empty strings immediately (HTTP 422).
    """
    query: str = Field(..., min_length=1)


class SuccessResponse(BaseModel):
    """
    Ensures outgoing successful response payload conforms to requirements.
    - status: Must be the literal string "success".
    - response: Dict containing {"answer": "..."}.
    """
    status: Literal["success"]
    response: dict[str, str]


class RejectionResponse(BaseModel):
    """
    Ensures outgoing rejected response payload conforms to security standards.
    - status: Must be the literal string "rejected".
    - reason: The explanation (e.g., "Request is outside the agent's allowed scope").
    """
    status: Literal["rejected"]
    reason: str


class HealthResponse(BaseModel):
    """
    Validates healthcheck endpoint responses.
    - status: Must be the literal string "ok".
    """
    status: Literal["ok"]
