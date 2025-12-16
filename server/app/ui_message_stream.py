"""
UI Message Stream utilities for Vercel AI SDK integration.

This module provides utilities to convert LangChain streams to Vercel AI SDK
UIMessage stream format, handling message extraction and stream conversion.
"""

from typing import AsyncIterator, Dict, Any, List
from .stream_converters import StreamConverter


# Vercel AI SDK stream headers
VERCEL_UI_STREAM_HEADERS = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "x-vercel-ai-ui-message-stream": "v1",
}


def extract_prompt_from_messages(messages: List[Dict[str, Any]]) -> str:
    """
    Extract the prompt text from Vercel AI SDK UIMessage format.

    The UIMessage format has this structure:
    {
        "id": "...",
        "role": "user" | "assistant",
        "parts": [
            {"type": "text", "text": "actual content"},
            ...
        ],
        "content": "fallback content"  # optional
    }

    Args:
        messages: List of UIMessage objects

    Returns:
        Extracted prompt text from the last user message

    Raises:
        ValueError: If no valid user message is found
    """
    if not messages:
        raise ValueError("No messages provided")

    # Find the last user message
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        if role != "user":
            continue

        # Try to extract from parts first
        parts = message.get("parts", [])
        if parts and isinstance(parts, list):
            for part in parts:
                if isinstance(part, dict) and part.get("type") == "text":
                    text = part.get("text")
                    if text and isinstance(text, str):
                        return text.strip()

        # Fallback to content field
        content = message.get("content")
        if content and isinstance(content, str):
            return content.strip()

    raise ValueError("No valid user message found in messages array")


class UIMessageStreamConverter:
    """
    Converter for transforming token streams to Vercel AI SDK UIMessage stream format.

    This class wraps the StreamConverter to provide a simple interface for
    converting arbitrary text token streams to the Vercel AI SDK format.
    """

    def __init__(self) -> None:
        """Initialize the converter."""
        self.stream_converter = StreamConverter()

    async def stream(self, token_stream: AsyncIterator[str]) -> AsyncIterator[str]:
        """
        Convert a simple token stream to Vercel AI SDK UIMessage stream format.

        This method wraps simple text tokens into AIMessageChunk objects and
        then converts them to the Vercel AI SDK format.

        Args:
            token_stream: AsyncIterator yielding text tokens

        Yields:
            SSE formatted events following Vercel AI SDK protocol
        """
        from langchain_core.messages import AIMessageChunk

        async def wrapped_stream():
            """Wrap text tokens as AIMessageChunk objects."""
            async for token in token_stream:
                if token:
                    yield AIMessageChunk(content=token)

        # Convert the wrapped stream using StreamConverter
        async for event in self.stream_converter.convert_stream(wrapped_stream()):
            yield event
