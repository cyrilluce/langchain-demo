"""
Transform LangChain messages to Vercel AI SDK UIMessage format.

This module implements the reverse transformation of Vercel AI SDK's
convertToModelMessages function. It converts LangChain BaseMessage objects
to UIMessage format compatible with the Vercel AI SDK frontend.

Key transformations:
1. Multiple consecutive assistant messages are merged into a single UIMessage
   with parts array
2. Tool messages are merged into the preceding assistant message as
   tool-result parts
3. System/user messages are converted to simple text-based UIMessages
"""

from typing import Any, Dict, List, Sequence
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)


def convert_to_ui_messages(messages: Sequence[BaseMessage]) -> List[Dict[str, Any]]:
    """
    Convert LangChain BaseMessage objects to Vercel AI SDK UIMessage format.

    This implements the reverse of Vercel's convertToModelMessages:
    - System messages -> UIMessage with role="system"
    - HumanMessage -> UIMessage with role="user"
    - AIMessage -> UIMessage with role="assistant"
    - ToolMessage -> merged into preceding assistant message as tool-result part

    Args:
        messages: List of LangChain BaseMessage objects

    Returns:
        List of UIMessage dictionaries compatible with Vercel AI SDK

    Examples:
        >>> from langchain_core.messages import HumanMessage, AIMessage
        >>> messages = [
        ...     HumanMessage(content="Hello"),
        ...     AIMessage(content="Hi there!")
        ... ]
        >>> ui_messages = convert_to_ui_messages(messages)
        >>> ui_messages[0]["role"]
        'user'
        >>> ui_messages[1]["role"]
        'assistant'
    """
    ui_messages: List[Dict[str, Any]] = []
    i = 0

    while i < len(messages):
        msg = messages[i]

        if isinstance(msg, SystemMessage):
            # System message: simple text part
            ui_messages.append({
                "role": "system",
                "parts": [{"type": "text", "text": msg.content}],
            })
            i += 1

        elif isinstance(msg, HumanMessage):
            # User message: convert content to parts
            ui_messages.append(_convert_user_message(msg))
            i += 1

        elif isinstance(msg, AIMessage):
            # Assistant message: may be followed by tool messages
            # Collect consecutive assistant and tool messages into a block
            block_messages = [msg]
            j = i + 1

            # Collect following tool messages and potential assistant messages
            while j < len(messages):
                next_msg = messages[j]
                if isinstance(next_msg, ToolMessage):
                    block_messages.append(next_msg)
                    j += 1
                elif isinstance(next_msg, AIMessage):
                    # In UIMessage format, multiple assistant messages
                    # can be part of the same step
                    block_messages.append(next_msg)
                    j += 1
                else:
                    break

            # Convert the block to a single UIMessage
            ui_messages.append(_convert_assistant_block(block_messages))
            i = j

        elif isinstance(msg, ToolMessage):
            # Orphaned tool message (no preceding assistant message)
            # This shouldn't happen in well-formed conversations,
            # but we handle it gracefully by creating a tool-only message
            ui_messages.append({
                "role": "assistant",
                "parts": [_convert_tool_message_to_part(msg)],
            })
            i += 1

        else:
            # Unknown message type - skip
            i += 1

    return ui_messages


def _convert_user_message(msg: HumanMessage) -> Dict[str, Any]:
    """
    Convert HumanMessage to UIMessage format.

    Args:
        msg: LangChain HumanMessage

    Returns:
        UIMessage dictionary with role="user"
    """
    parts: List[Dict[str, Any]] = []

    if isinstance(msg.content, str):
        # Simple text content
        parts.append({"type": "text", "text": msg.content})
    elif isinstance(msg.content, list):
        # Multi-modal content
        for item in msg.content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append({"type": "text", "text": item.get("text", "")})
                elif item.get("type") == "image_url":
                    # Image content
                    image_url = item.get("image_url", {})
                    if isinstance(image_url, dict):
                        url = image_url.get("url", "")
                    else:
                        url = str(image_url)
                    parts.append({
                        "type": "file",
                        "mediaType": "image/*",
                        "url": url,
                    })
            elif isinstance(item, str):
                parts.append({"type": "text", "text": item})

    if not parts:
        # Fallback to empty text
        parts.append({"type": "text", "text": ""})

    return {"role": "user", "parts": parts}


def _convert_assistant_block(block_messages: Sequence[BaseMessage]) -> Dict[str, Any]:
    """
    Convert a block of assistant and tool messages to a single UIMessage.

    In Vercel AI SDK UIMessage format:
    - Multiple assistant responses and tool results are merged into one message
    - Tool messages become tool-result parts in the content array
    - Assistant text and tool calls are preserved as separate parts

    Args:
        block_messages: List of consecutive AIMessage and ToolMessage objects

    Returns:
        UIMessage dictionary with role="assistant"
    """
    parts: List[Dict[str, Any]] = []

    for msg in block_messages:
        if isinstance(msg, AIMessage):
            # Add text content if present
            if msg.content and isinstance(msg.content, str):
                parts.append({"type": "text", "text": msg.content})

            # Add tool calls if present
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    # Create tool-call part (Vercel's tool invocation format)
                    parts.append({
                        "type": f"tool-{tool_call.get('name', 'unknown')}",
                        "toolCallId": tool_call.get("id", ""),
                        "toolName": tool_call.get("name", ""),
                        "input": tool_call.get("args", {}),
                        "state": "output-available",  # Default state
                    })

        elif isinstance(msg, ToolMessage):
            # Tool message becomes a tool-result part
            parts.append(_convert_tool_message_to_part(msg))

    if not parts:
        # Fallback to empty text
        parts.append({"type": "text", "text": ""})

    return {"role": "assistant", "parts": parts}


def _convert_tool_message_to_part(msg: ToolMessage) -> Dict[str, Any]:
    """
    Convert ToolMessage to a tool-result part.

    Args:
        msg: LangChain ToolMessage

    Returns:
        Dictionary representing a tool-result part
    """
    # Extract tool call id and name from message
    tool_call_id = getattr(msg, "tool_call_id", "")

    # Try to extract tool name from additional_kwargs or artifact
    tool_name = ""
    if hasattr(msg, "additional_kwargs"):
        tool_name = msg.additional_kwargs.get("name", "")
    if not tool_name and hasattr(msg, "name"):
        tool_name = msg.name or ""

    return {
        "type": f"tool-{tool_name}" if tool_name else "tool-result",
        "toolCallId": tool_call_id,
        "toolName": tool_name,
        "output": msg.content,
        "state": "output-available",
    }
