"""
Pydantic models for request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import List


class PromptRequest(BaseModel):
    """Request model for agent endpoint."""
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User's text input for the LLM agent"
    )


class AgentResponse(BaseModel):
    """Response model for agent endpoint."""
    answer: str = Field(
        ...,
        min_length=1,
        description="Generated response from the LLM agent"
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Human-readable error message")
    code: str | None = Field(None, description="Machine-readable error code")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall service health")
    llm_configured: bool = Field(
        ..., description="Whether LLM credentials are configured"
    )


class FactReference(BaseModel):
    """Reference to the source text in the original content."""
    offset: int = Field(
        ...,
        ge=0,
        description="Starting position of the reference in original text"
    )
    length: int = Field(
        ..., gt=0, description="Length of the referenced text"
    )
    content: str | None


class ExtractedFact(BaseModel):
    """An extracted fact with its references."""
    fact: str = Field(
        ..., min_length=1, description="The extracted atomic fact"
    )
    references: List[FactReference] = Field(
        default_factory=list,
        description="References to the source text"
    )


class FactsExtractionRequest(BaseModel):
    """Request model for facts extraction endpoint."""
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Source text to extract facts from"
    )
    topic: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Topic to focus fact extraction on"
    )


class FactsExtractionResponse(BaseModel):
    """Response model for facts extraction endpoint."""
    facts: List[ExtractedFact] = Field(
        default_factory=list,
        description="List of extracted facts with references"
    )
