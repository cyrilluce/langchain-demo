"""
FastAPI application entry point.
"""

import json
from typing import AsyncIterator
from langchain_core.runnables import RunnableConfig
from app.vercel_ui_message_stream.converter import StreamToVercelConverter
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .models import HealthResponse
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
    Supports thread_id and checkpoint_id for session continuation.
    """
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid request payload")

    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    # Extract thread_id and checkpoint_id from request
    thread_id = body.get("thread_id", "1")  # Default to "1" for backward compatibility
    checkpoint_id = body.get("checkpoint_id")

    try:
        prompt = extract_prompt_from_messages(messages)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Build config for agent
    agent_config: RunnableConfig = {
        "configurable": {"thread_id": thread_id}  # type: ignore
    }
    if checkpoint_id:
        agent_config["configurable"]["checkpoint_id"] = checkpoint_id  # type: ignore

    converter = StreamToVercelConverter()

    async def event_stream() -> AsyncIterator[str]:
        # Use the new astream_messages method that returns AIMessageChunk objects
        message_stream = agent.astream_messages(prompt, config=agent_config)
        async for frame in converter.stream(message_stream):
            # print(json.dumps(frame, ensure_ascii=False))
            yield f'data: {json.dumps(frame, ensure_ascii=False)}\n\n'
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=VERCEL_UI_STREAM_HEADERS,
    )


@app.get("/chat/{thread_id}/history")
async def get_chat_history(
    thread_id: str, checkpoint_id: str | None = None
) -> dict[str, list[dict]]:
    """
    Get conversation history for a specific thread.
    
    Args:
        thread_id: The thread ID to get history for
        checkpoint_id: Optional checkpoint ID to get history up to that point
    
    Returns:
        Historical messages for the thread
    """
    try:
        messages = await agent.get_history(thread_id, checkpoint_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get history: {str(e)}"
        )


@app.get("/")
async def root() -> dict:
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
