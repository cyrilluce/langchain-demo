"""
Pydantic models for request/response schemas.
"""

from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """Request model for agent endpoint."""
    prompt: str = Field(..., min_length=1, max_length=10000, description="User's text input for the LLM agent")


class AgentResponse(BaseModel):
    """Response model for agent endpoint."""
    answer: str = Field(..., min_length=1, description="Generated response from the LLM agent")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Human-readable error message")
    code: str | None = Field(None, description="Machine-readable error code")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall service health")
    llm_configured: bool = Field(..., description="Whether LLM credentials are configured")
