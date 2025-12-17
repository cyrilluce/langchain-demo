"""
FastAPI application entry point.
"""

import json
from typing import AsyncIterator
from app.vercel_ui_message_stream.converter import StreamToVercelConverter
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .models import PromptRequest, AgentResponse, ErrorResponse, HealthResponse
from .agent import agent
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


@app.post(
    "/agent",
    response_model=AgentResponse,
    responses={503: {"model": ErrorResponse, "description": "LLM service unavailable"}},
)
async def process_agent_request(request: PromptRequest) -> AgentResponse:
    """
    Process a prompt with the LLM agent.

    - **prompt**: User's text input (1-10000 characters)

    Returns the agent's generated response or fallback message.
    """
    try:
        answer = await agent.process_prompt(request.prompt)
        return AgentResponse(answer=answer)
    except Exception:
        # Return HTTP 503 for LLM failures
        raise HTTPException(
            status_code=503,
            detail={
                "error": "LLM service temporarily unavailable. Please try again later.",
                "code": "LLM_UNAVAILABLE",
            },
        )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service status and LLM configuration state.
    """
    return HealthResponse(status="healthy", llm_configured=config.is_llm_configured())


@app.post("/agent/stream")
async def process_agent_request_stream(request: Request):
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
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Monorepo LLM Agent API",
        "version": "1.0.0",
        "endpoints": {
            "agent": "POST /agent",
            "agent_stream": "POST /agent/stream",
            "health": "GET /health",
        },
    }
