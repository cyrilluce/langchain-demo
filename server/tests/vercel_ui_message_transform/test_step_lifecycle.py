"""
Unit tests for step-start lifecycle in transform module.

Tests that verify the correct handling of step-start parts in UIMessage format.
"""

from langchain_core.messages import (
    AIMessage,
    ToolMessage,
)
from app.vercel_ui_message_transform.transform import (
    convert_to_ui_messages,
    _convert_assistant_block,
)


class TestStepLifecycle:
    """Test step-start lifecycle handling in UIMessage transformation."""

    def test_simple_assistant_with_step_start(self):
        """Test that simple assistant message includes step-start."""
        messages = [AIMessage(content="Hello!")]
        result = convert_to_ui_messages(messages)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        # Should include step-start and text
        assert len(result[0]["parts"]) == 2
        assert result[0]["parts"][0] == {"type": "step-start"}
        assert result[0]["parts"][1] == {"type": "text", "text": "Hello!"}

    def test_assistant_with_tool_calls_includes_step_start(self):
        """Test that assistant message with tool calls includes step-start."""
        messages = [
            AIMessage(
                content="Checking...",
                tool_calls=[
                    {"id": "call-1", "name": "tool1", "args": {"param": "value"}},
                ],
            )
        ]
        result = convert_to_ui_messages(messages)

        assert len(result) == 1
        parts = result[0]["parts"]
        # Should include step-start, text, and tool
        assert len(parts) == 3
        assert parts[0] == {"type": "step-start"}
        assert parts[1]["type"] == "text"
        assert parts[2]["type"] == "tool-tool1"

    def test_multiple_consecutive_ai_messages_multiple_steps(self):
        """Test that each AI message gets its own step-start."""
        messages = [
            AIMessage(content="First."),
            AIMessage(content="Second."),
            AIMessage(content="Third."),
        ]
        result = convert_to_ui_messages(messages)

        assert len(result) == 1
        parts = result[0]["parts"]
        # 3 AI messages: each has step-start + text = 6 parts
        assert len(parts) == 6
        assert parts[0] == {"type": "step-start"}
        assert parts[1]["text"] == "First."
        assert parts[2] == {"type": "step-start"}
        assert parts[3]["text"] == "Second."
        assert parts[4] == {"type": "step-start"}
        assert parts[5]["text"] == "Third."

    def test_complex_multi_step_scenario(self):
        """
        Test complex scenario with multiple steps as described in the issue.
        
        Scenario: AI(text1, toolCall1, toolCall2), Tool(result1), Tool(result2), 
                  AI(toolCall3), Tool(result3), AI(text2)
        
        Expected structure:
        - step-start, text1, tool1, tool2 (Step 1: AI with 2 tool calls + results)
        - step-start, tool3 (Step 2: AI with 1 tool call + result)
        - step-start, text2 (Step 3: AI with text response)
        """
        messages = [
            AIMessage(
                content="Let me help with that.",
                tool_calls=[
                    {"id": "call-1", "name": "tool1", "args": {"param": "a"}},
                    {"id": "call-2", "name": "tool2", "args": {"param": "b"}},
                ],
            ),
            ToolMessage(content='{"result": "r1"}', tool_call_id="call-1", name="tool1"),
            ToolMessage(content='{"result": "r2"}', tool_call_id="call-2", name="tool2"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "call-3", "name": "tool3", "args": {"param": "c"}},
                ],
            ),
            ToolMessage(content='{"result": "r3"}', tool_call_id="call-3", name="tool3"),
            AIMessage(content="Here is your final answer."),
        ]
        result = convert_to_ui_messages(messages)

        # All AI and Tool messages should be merged into one UIMessage
        assert len(result) == 1
        assert result[0]["role"] == "assistant"

        parts = result[0]["parts"]
        # Expected structure:
        # step-start, text1, tool1, tool2,
        # step-start, tool3,
        # step-start, text2
        # = 8 parts total
        assert len(parts) == 8

        # Step 1
        assert parts[0] == {"type": "step-start"}
        assert parts[1]["type"] == "text"
        assert parts[1]["text"] == "Let me help with that."
        assert parts[2]["type"] == "tool-tool1"
        assert parts[2]["output"] == {"result": "r1"}
        assert parts[3]["type"] == "tool-tool2"
        assert parts[3]["output"] == {"result": "r2"}

        # Step 2
        assert parts[4] == {"type": "step-start"}
        assert parts[5]["type"] == "tool-tool3"
        assert parts[5]["output"] == {"result": "r3"}

        # Step 3
        assert parts[6] == {"type": "step-start"}
        assert parts[7]["type"] == "text"
        assert parts[7]["text"] == "Here is your final answer."

    def test_assistant_block_with_step_start(self):
        """Test _convert_assistant_block includes step-start."""
        messages = [
            AIMessage(
                content="Processing...",
                tool_calls=[
                    {"id": "tc-1", "name": "search", "args": {"q": "test"}},
                ],
            ),
            ToolMessage(
                content="Results...",
                tool_call_id="tc-1",
                name="search",
            ),
        ]
        result = _convert_assistant_block(messages)

        # Should have step-start, and merged tool part
        assert len(result["parts"]) >= 2
        assert result["parts"][0] == {"type": "step-start"}

    def test_empty_block_includes_step_start(self):
        """Test that empty block still includes step-start."""
        messages = []
        result = _convert_assistant_block(messages)

        assert result["role"] == "assistant"
        # Even empty block should have step-start and fallback text
        assert len(result["parts"]) == 2
        assert result["parts"][0] == {"type": "step-start"}
        assert result["parts"][1]["type"] == "text"
