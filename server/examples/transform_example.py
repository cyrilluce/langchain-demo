#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example usage of LangChain to Vercel UI Message transformation.

This example demonstrates how to convert LangChain conversation history
to Vercel AI SDK UIMessage format for frontend consumption.
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from app.vercel_ui_message_transform import convert_to_ui_messages
import json


def example_basic_conversation() -> None:
    """Example: Basic conversation without tools."""
    print("\n=== Example 1: Basic Conversation ===\n")

    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="What is the weather like today?"),
        AIMessage(content="I'd be happy to help you check the weather!"),
    ]

    ui_messages = convert_to_ui_messages(messages)
    print(json.dumps(ui_messages, indent=2, ensure_ascii=False))


def example_tool_calling() -> None:
    """Example: Conversation with tool calling."""
    print("\n=== Example 2: Tool Calling ===\n")

    messages = [
        HumanMessage(content="What's the weather in Tokyo?"),
        AIMessage(
            content="Let me check that for you.",
            tool_calls=[
                {
                    "id": "call-123",
                    "name": "get_weather",
                    "args": {"city": "Tokyo", "unit": "celsius"},
                }
            ],
        ),
        ToolMessage(
            content='{"temperature": 22, "condition": "sunny", "humidity": 65}',
            tool_call_id="call-123",
            name="get_weather",
        ),
        AIMessage(
            content="The weather in Tokyo is sunny with a temperature "
            "of 22°C and 65% humidity."
        ),
    ]

    ui_messages = convert_to_ui_messages(messages)
    print(json.dumps(ui_messages, indent=2, ensure_ascii=False))
    print("\nNote: Tool call and result are merged into a single part with both input and output.")
    print("The JSON output is automatically decoded into a Python dict.")


def example_multimodal() -> None:
    """Example: Multimodal message with image."""
    print("\n=== Example 3: Multimodal Message ===\n")

    messages = [
        HumanMessage(
            content=[
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/photo.jpg"},
                },
            ]
        ),
        AIMessage(content="I can see a beautiful sunset over the ocean."),
    ]

    ui_messages = convert_to_ui_messages(messages)
    print(json.dumps(ui_messages, indent=2, ensure_ascii=False))


def example_merged_responses() -> None:
    """Example: Multiple consecutive assistant responses (merged)."""
    print("\n=== Example 4: Merged Assistant Responses ===\n")

    messages = [
        HumanMessage(content="Tell me a story"),
        AIMessage(content="Once upon a time..."),
        AIMessage(content="there was a brave knight."),
        AIMessage(content="He went on many adventures."),
    ]

    ui_messages = convert_to_ui_messages(messages)
    print(json.dumps(ui_messages, indent=2, ensure_ascii=False))
    print(
        "\nNote: The 3 consecutive assistant messages are merged "
        "into one UIMessage with multiple parts."
    )


if __name__ == "__main__":
    example_basic_conversation()
    example_tool_calling()
    example_multimodal()
    example_merged_responses()
