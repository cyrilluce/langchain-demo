"""
FastAPI application entry point.
"""

import json
from typing import AsyncIterator, Dict, Any
from app.vercel_ui_message_stream.converter import StreamToVercelConverter
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .models import (
    HealthResponse,
    FactsExtractionRequest,
    FactsExtractionResponse
)
from .agent import agent
from .agents.facts_extractor import FactsExtractorAgent
from .config import config
from .ui_message_stream import (
    VERCEL_UI_STREAM_HEADERS,
    extract_prompt_from_messages,
)

# Initialize FastAPI app
app = FastAPI(
    title="Monorepo LLM Agent API",
    description="Minimal LLM agent using langchain/langgraph with Aliyun Dashscope",
    version="1.0.0",
)

# Configure CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize facts extractor agent (lazy loading on first use)
_facts_extractor_agent = None


def get_facts_extractor_agent() -> FactsExtractorAgent:
    """Get or create the facts extractor agent instance."""
    global _facts_extractor_agent
    if _facts_extractor_agent is None:
        _facts_extractor_agent = FactsExtractorAgent()
    return _facts_extractor_agent


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service status and LLM configuration state.
    """
    return HealthResponse(status="healthy", llm_configured=config.is_llm_configured())


@app.post("/agent/stream")
async def process_agent_request_stream(request: Request) -> StreamingResponse:
    """
    Process a prompt with the LLM agent using streaming response.
    Compatible with Vercel AI SDK UIMessage streaming format.
    """
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid request payload")

    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    try:
        prompt = extract_prompt_from_messages(messages)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    converter = StreamToVercelConverter()

    async def event_stream() -> AsyncIterator[str]:
        # Use the new astream_messages method that returns AIMessageChunk objects
        message_stream = agent.astream_messages(prompt)
        async for frame in converter.stream(message_stream):
            # print(json.dumps(frame, ensure_ascii=False))
            yield f'data: {json.dumps(frame, ensure_ascii=False)}\n\n'
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=VERCEL_UI_STREAM_HEADERS,
    )


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "name": "Monorepo LLM Agent API",
        "version": "1.0.0",
        "endpoints": {
            "agent": "POST /agent",
            "agent_stream": "POST /agent/stream",
            "facts_extract": "POST /facts/extract",
            "health": "GET /health",
        },
    }


@app.post("/facts/extract", response_model=FactsExtractionResponse)
async def extract_facts(
    request: FactsExtractionRequest
) -> FactsExtractionResponse:
    """
    Extract topic-related atomic facts from the given content.

    Returns a list of extracted facts with references to the source text.
    Returns HTTP 503 if the LLM service fails.
    """
    try:
        extractor = get_facts_extractor_agent()
        facts = await extractor.extract_facts(
            request.content, request.topic
        )
        return FactsExtractionResponse(facts=facts)
    except Exception as e:
        error_message = str(e)
        if "LLM service error" in error_message:
            raise HTTPException(status_code=503, detail=error_message)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {error_message}"
        )
