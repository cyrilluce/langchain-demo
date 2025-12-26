"""
Unit tests for vercel_ui_message_transform.transform module.

Tests the conversion of LangChain BaseMessage objects to Vercel AI SDK
UIMessage format.
"""

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from app.vercel_ui_message_transform.transform import (
    convert_to_ui_messages,
    _convert_user_message,
    _convert_assistant_block,
    _convert_tool_message_to_part,
)


class TestConvertToUIMessages:
    """Test the main convert_to_ui_messages function."""

    def test_simple_system_message(self):
        """Test conversion of a simple system message."""
        messages = [SystemMessage(content="You are a helpful assistant.")]
        result = convert_to_ui_messages(messages)

        assert len(result) == 1
        assert result[0]["role"] == "system"
        assert result[0]["parts"] == [
            {"type": "text", "text": "You are a helpful assistant."}
        ]

    def test_simple_user_message(self):
        """Test conversion of a simple user message."""
        messages = [HumanMessage(content="Hello, how are you?")]
        result = convert_to_ui_messages(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["parts"] == [{"type": "text", "text": "Hello, how are you?"}]

    def test_simple_assistant_message(self):
        """Test conversion of a simple assistant message."""
        messages = [AIMessage(content="I'm doing well, thank you!")]
        result = convert_to_ui_messages(messages)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert len(result[0]["parts"]) == 2
        assert result[0]["parts"][0] == {"type": "step-start"}
        assert result[0]["parts"][1] == {"type": "text", "text": "I'm doing well, thank you!"}

    def test_conversation_sequence(self):
        """Test conversion of a typical conversation sequence."""
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="What is the weather?"),
            AIMessage(content="Let me check that for you."),
            HumanMessage(content="Thank you!"),
            AIMessage(content="You're welcome!"),
        ]
        result = convert_to_ui_messages(messages)

        assert len(result) == 5
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"
        assert result[3]["role"] == "user"
        assert result[4]["role"] == "assistant"

    def test_assistant_with_tool_calls(self):
        """Test conversion of assistant message with tool calls."""
        messages = [
            AIMessage(
                content="Let me check the weather.",
                tool_calls=[
                    {
                        "id": "call-1",
                        "name": "get_weather",
                        "args": {"city": "San Francisco"},
                    }
                ],
            )
        ]
        result = convert_to_ui_messages(messages)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert len(result[0]["parts"]) == 3
        assert result[0]["parts"][0] == {"type": "step-start"}
        assert result[0]["parts"][1]["type"] == "text"
        assert result[0]["parts"][2]["type"] == "tool-get_weather"
        assert result[0]["parts"][2]["toolCallId"] == "call-1"
        assert result[0]["parts"][2]["input"] == {"city": "San Francisco"}

    def test_assistant_with_tool_message(self):
        """Test merging of tool messages into assistant message."""
        messages = [
            AIMessage(
                content="Checking weather...",
                tool_calls=[
                    {
                        "id": "call-1",
                        "name": "get_weather",
                        "args": {"city": "Tokyo"},
                    }
                ],
            ),
            ToolMessage(
                content='{"temperature": 72, "condition": "sunny"}',
                tool_call_id="call-1",
                name="get_weather",
            ),
        ]
        result = convert_to_ui_messages(messages)

        # Tool message should be merged into assistant message
        # as single part with output
        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert len(result[0]["parts"]) == 3  # step-start + text + merged tool part

        # Check step-start
        assert result[0]["parts"][0] == {"type": "step-start"}

        # Check text part
        assert result[0]["parts"][1]["type"] == "text"
        assert result[0]["parts"][1]["text"] == "Checking weather..."

        # Check merged tool part
        tool_part = result[0]["parts"][2]
        assert tool_part["type"] == "tool-get_weather"
        assert tool_part["toolCallId"] == "call-1"
        assert tool_part["input"] == {"city": "Tokyo"}
        # Output should be JSON decoded
        assert tool_part["output"] == {"temperature": 72, "condition": "sunny"}
        assert tool_part["state"] == "output-available"

    def test_multiple_consecutive_assistants(self):
        """Test merging of consecutive assistant messages."""
        messages = [
            AIMessage(content="First response."),
            AIMessage(content="Second response."),
            AIMessage(content="Third response."),
        ]
        result = convert_to_ui_messages(messages)

        # All consecutive assistant messages merged into one
        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        # 3 messages × (step-start + text) = 6 parts
        assert len(result[0]["parts"]) == 6
        assert result[0]["parts"][0] == {"type": "step-start"}
        assert result[0]["parts"][1]["text"] == "First response."
        assert result[0]["parts"][2] == {"type": "step-start"}
        assert result[0]["parts"][3]["text"] == "Second response."
        assert result[0]["parts"][4] == {"type": "step-start"}
        assert result[0]["parts"][5]["text"] == "Third response."

    def test_orphaned_tool_message(self):
        """Test handling of tool message without preceding assistant message."""
        messages = [
            ToolMessage(
                content="Tool result",
                tool_call_id="call-1",
                name="some_tool",
            )
        ]
        result = convert_to_ui_messages(messages)

        # Should create an assistant message containing the tool result
        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert len(result[0]["parts"]) == 1
        assert result[0]["parts"][0]["type"] == "tool-some_tool"

    def test_empty_messages_list(self):
        """Test conversion of empty messages list."""
        messages = []
        result = convert_to_ui_messages(messages)

        assert result == []

    def test_multimodal_user_message(self):
        """Test conversion of user message with image content."""
        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
                ]
            )
        ]
        result = convert_to_ui_messages(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert len(result[0]["parts"]) == 2
        assert result[0]["parts"][0]["type"] == "text"
        assert result[0]["parts"][1]["type"] == "file"
        assert result[0]["parts"][1]["url"] == "https://example.com/image.jpg"


class TestConvertUserMessage:
    """Test the _convert_user_message helper function."""

    def test_simple_text_content(self):
        """Test conversion of simple text content."""
        msg = HumanMessage(content="Hello world")
        result = _convert_user_message(msg)

        assert result["role"] == "user"
        assert result["parts"] == [{"type": "text", "text": "Hello world"}]

    def test_empty_content(self):
        """Test conversion of message with empty content."""
        msg = HumanMessage(content="")
        result = _convert_user_message(msg)

        assert result["role"] == "user"
        assert len(result["parts"]) == 1
        assert result["parts"][0]["type"] == "text"

    def test_list_content_with_text(self):
        """Test conversion of list content with text items."""
        msg = HumanMessage(
            content=[
                {"type": "text", "text": "First part"},
                {"type": "text", "text": "Second part"},
            ]
        )
        result = _convert_user_message(msg)

        assert len(result["parts"]) == 2
        assert result["parts"][0]["text"] == "First part"
        assert result["parts"][1]["text"] == "Second part"


class TestConvertAssistantBlock:
    """Test the _convert_assistant_block helper function."""

    def test_single_text_message(self):
        """Test conversion of single assistant message with text."""
        messages = [AIMessage(content="Hello!")]
        result = _convert_assistant_block(messages)

        assert result["role"] == "assistant"
        assert len(result["parts"]) == 2
        assert result["parts"][0] == {"type": "step-start"}
        assert result["parts"][1] == {"type": "text", "text": "Hello!"}

    def test_message_with_tool_calls(self):
        """Test conversion of message with tool calls."""
        messages = [
            AIMessage(
                content="Calling tool...",
                tool_calls=[
                    {
                        "id": "tc-1",
                        "name": "calculator",
                        "args": {"operation": "add", "a": 1, "b": 2},
                    }
                ],
            )
        ]
        result = _convert_assistant_block(messages)

        assert len(result["parts"]) == 3
        assert result["parts"][0] == {"type": "step-start"}
        assert result["parts"][1]["type"] == "text"
        assert result["parts"][2]["type"] == "tool-calculator"
        assert result["parts"][2]["toolCallId"] == "tc-1"
        assert result["parts"][2]["input"]["operation"] == "add"

    def test_block_with_tool_message(self):
        """Test conversion of block containing tool message."""
        messages = [
            AIMessage(
                content="",
                tool_calls=[{"id": "tc-1", "name": "search", "args": {"q": "test"}}],
            ),
            ToolMessage(
                content="Search results...",
                tool_call_id="tc-1",
                name="search",
            ),
        ]
        result = _convert_assistant_block(messages)

        # Should have step-start + one merged tool part
        assert len(result["parts"]) == 2
        assert result["parts"][0] == {"type": "step-start"}
        tool_part = result["parts"][1]
        assert tool_part["type"] == "tool-search"
        assert tool_part["toolCallId"] == "tc-1"
        assert tool_part["input"] == {"q": "test"}
        assert tool_part["output"] == "Search results..."
        assert tool_part["state"] == "output-available"

    def test_empty_block(self):
        """Test conversion of empty block."""
        messages = []
        result = _convert_assistant_block(messages)

        assert result["role"] == "assistant"
        assert len(result["parts"]) == 2
        assert result["parts"][0] == {"type": "step-start"}
        assert result["parts"][1]["type"] == "text"
        assert result["parts"][1]["text"] == ""


class TestConvertToolMessageToPart:
    """Test the _convert_tool_message_to_part helper function."""

    def test_basic_tool_message(self):
        """Test conversion of basic tool message."""
        msg = ToolMessage(
            content="Result data",
            tool_call_id="call-123",
            name="my_tool",
        )
        result = _convert_tool_message_to_part(msg)

        assert result["type"] == "tool-my_tool"
        assert result["toolCallId"] == "call-123"
        assert result["toolName"] == "my_tool"
        assert result["output"] == "Result data"
        assert result["state"] == "output-available"

    def test_tool_message_without_name(self):
        """Test conversion of tool message without name."""
        msg = ToolMessage(
            content="Result",
            tool_call_id="call-456",
        )
        result = _convert_tool_message_to_part(msg)

        # Should fallback to generic tool-result type
        assert result["type"] == "tool-result"
        assert result["toolCallId"] == "call-456"
        assert result["toolName"] == ""

    def test_tool_output_json_decode(self):
        """Test that tool output is JSON decoded when possible."""
        messages = [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-1",
                        "name": "calculator",
                        "args": {"a": 1, "b": 2},
                    }
                ],
            ),
            ToolMessage(
                content='{"result": 3, "status": "success"}',
                tool_call_id="call-1",
                name="calculator",
            ),
        ]
        result = convert_to_ui_messages(messages)

        # parts[0] is step-start, parts[1] is the tool
        tool_part = result[0]["parts"][1]
        # Output should be decoded from JSON string to dict
        assert isinstance(tool_part["output"], dict)
        assert tool_part["output"] == {"result": 3, "status": "success"}

    def test_tool_output_non_json_string(self):
        """Test that non-JSON tool output remains as string."""
        messages = [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-1",
                        "name": "echo",
                        "args": {"text": "hello"},
                    }
                ],
            ),
            ToolMessage(
                content="Plain text result",
                tool_call_id="call-1",
                name="echo",
            ),
        ]
        result = convert_to_ui_messages(messages)

        # parts[0] is step-start, parts[1] is the tool
        tool_part = result[0]["parts"][1]
        # Output should remain as string
        assert isinstance(tool_part["output"], str)
        assert tool_part["output"] == "Plain text result"
