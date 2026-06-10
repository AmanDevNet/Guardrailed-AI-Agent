from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)


class SuccessResponse(BaseModel):
    status: Literal["success"]
    response: dict[str, str]


class RejectionResponse(BaseModel):
    status: Literal["rejected"]
    reason: str


class HealthResponse(BaseModel):
    status: Literal["ok"]

