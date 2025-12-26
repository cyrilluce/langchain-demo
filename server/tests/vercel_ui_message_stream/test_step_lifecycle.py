"""
Unit tests for step lifecycle in stream converter.

Tests that verify the correct handling of start-step and finish-step in streaming.
"""

import pytest
from langchain_core.messages import AIMessageChunk, ToolMessage

from app.vercel_ui_message_stream.converter import StreamToVercelConverter


class TestStreamStepLifecycle:
    """Test step lifecycle in stream converter."""

    @pytest.mark.asyncio
    async def test_ai_message_with_tools_step_lifecycle(self):
        """
        Test that AI message and following tool messages share the same step.
        
        Expected flow:
        - start-step (from AIMessage)
        - text/tool-input events (from AIMessage)
        - tool-output events (from ToolMessage)  # NO start-step/finish-step here!
        - NO finish-step until next AI message or stream end
        """
        async def mock_stream():
            # AI message with tool call
            yield AIMessageChunk(
                id="msg-1",
                content="Let me help.",
                tool_call_chunks=[
                    {
                        "id": "call-1",
                        "name": "tool1",
                        "args": '{"param":"value"}',
                        "index": 0,
                    }
                ],
                chunk_position="last",
            )
            # Tool result - should NOT trigger new step
            msg = ToolMessage(
                content='{"result": "done"}',
                tool_call_id="call-1",
                name="tool1",
            )
            msg.id = "tool-1"
            yield msg

        converter = StreamToVercelConverter()
        events = []
        async for event in converter.stream(mock_stream()):
            events.append(event)

        # Verify step lifecycle
        event_types = [e["type"] for e in events]

        # Should have:
        # 1. start-step (from AI message)
        # 2. Various AI events (text-start, text-delta, tool-input-*)
        # 3. tool-output-available (from ToolMessage - NO new step!)
        # 4. finish-step (at end of stream)

        # Check that start-step appears exactly once at the beginning
        start_step_indices = [i for i, t in enumerate(event_types) if t == "start-step"]
        assert len(start_step_indices) == 1
        assert start_step_indices[0] == 0  # First event

        # Check that finish-step appears exactly once at the end
        finish_step_indices = [i for i, t in enumerate(event_types) if t == "finish-step"]
        assert len(finish_step_indices) == 1
        assert finish_step_indices[0] == len(events) - 1  # Last event

        # Verify tool-output-available is between start and finish
        tool_output_indices = [i for i, t in enumerate(event_types) if t == "tool-output-available"]
        assert len(tool_output_indices) == 1
        assert start_step_indices[0] < tool_output_indices[0] < finish_step_indices[0]

    @pytest.mark.asyncio
    async def test_multiple_ai_messages_multiple_steps(self):
        """
        Test that multiple AI messages create separate steps.
        
        Scenario: AI(msg1) -> Tool(result1) -> AI(msg2)
        
        Expected flow:
        - start-step (for msg1)
        - AI events for msg1
        - tool-output for result1 (NO step change)
        - finish-step (end of msg1's step)
        - start-step (for msg2)
        - AI events for msg2
        - finish-step (at end of stream)
        """
        async def mock_stream():
            # First AI message
            chunk1 = AIMessageChunk(
                id="msg-1",
                content="First",
                tool_call_chunks=[
                    {
                        "id": "call-1",
                        "name": "tool1",
                        "args": '{}',
                        "index": 0,
                    }
                ],
                chunk_position="last",
            )
            yield chunk1

            # Tool result
            tool1 = ToolMessage(
                content='{"result": "r1"}',
                tool_call_id="call-1",
                name="tool1",
            )
            tool1.id = "tool-1"
            yield tool1

            # Second AI message (different ID = new step)
            chunk2 = AIMessageChunk(
                id="msg-2",
                content="Second",
                chunk_position="last",
            )
            yield chunk2

        converter = StreamToVercelConverter()
        events = []
        async for event in converter.stream(mock_stream()):
            events.append(event)

        event_types = [e["type"] for e in events]

        # Should have exactly 2 start-step events
        start_steps = [i for i, t in enumerate(event_types) if t == "start-step"]
        assert len(start_steps) == 2

        # Should have exactly 2 finish-step events
        finish_steps = [i for i, t in enumerate(event_types) if t == "finish-step"]
        assert len(finish_steps) == 2

        # First finish-step should come before second start-step
        assert finish_steps[0] < start_steps[1]

        # Tool output should be between first start and first finish
        tool_outputs = [i for i, t in enumerate(event_types) if t == "tool-output-available"]
        assert len(tool_outputs) == 1
        assert start_steps[0] < tool_outputs[0] < finish_steps[0]

    @pytest.mark.asyncio
    async def test_complex_multi_step_scenario(self):
        """
        Test complex scenario matching the issue description.
        
        Scenario: AI(text1, toolCall1, toolCall2) -> Tool(result1) -> Tool(result2) ->
                  AI(toolCall3) -> Tool(result3) -> AI(text2)
        
        Expected steps:
        - Step 1: AI outputs + tool results 1&2
        - Step 2: AI tool call 3 + result 3
        - Step 3: AI text output
        """
        async def mock_stream():
            # Step 1: AI with 2 tool calls
            chunk1 = AIMessageChunk(
                id="msg-1",
                content="text1",
                tool_call_chunks=[
                    {"id": "call-1", "name": "tool1", "args": '{}', "index": 0},
                    {"id": "call-2", "name": "tool2", "args": '{}', "index": 1},
                ],
                chunk_position="last",
            )
            yield chunk1

            # Tool results (part of step 1)
            tool1 = ToolMessage(content='{"result": "r1"}', tool_call_id="call-1", name="tool1")
            tool1.id = "tool-1"
            yield tool1

            tool2 = ToolMessage(content='{"result": "r2"}', tool_call_id="call-2", name="tool2")
            tool2.id = "tool-2"
            yield tool2

            # Step 2: AI with 1 tool call
            chunk2 = AIMessageChunk(
                id="msg-2",
                content="",
                tool_call_chunks=[
                    {"id": "call-3", "name": "tool3", "args": '{}', "index": 0},
                ],
                chunk_position="last",
            )
            yield chunk2

            # Tool result (part of step 2)
            tool3 = ToolMessage(content='{"result": "r3"}', tool_call_id="call-3", name="tool3")
            tool3.id = "tool-3"
            yield tool3

            # Step 3: AI with text only
            chunk3 = AIMessageChunk(
                id="msg-3",
                content="text2",
                chunk_position="last",
            )
            yield chunk3

        converter = StreamToVercelConverter()
        events = []
        async for event in converter.stream(mock_stream()):
            events.append(event)

        event_types = [e["type"] for e in events]

        # Should have exactly 3 start-step events (one per AI message)
        start_steps = [i for i, t in enumerate(event_types) if t == "start-step"]
        assert len(start_steps) == 3

        # Should have exactly 3 finish-step events
        finish_steps = [i for i, t in enumerate(event_types) if t == "finish-step"]
        assert len(finish_steps) == 3

        # Should have 3 tool-output-available events
        tool_outputs = [i for i, t in enumerate(event_types) if t == "tool-output-available"]
        assert len(tool_outputs) == 3

        # Verify step structure:
        # Step 1: start -> ... -> tool-output(r1) -> tool-output(r2) -> finish
        # Step 2: start -> ... -> tool-output(r3) -> finish
        # Step 3: start -> ... -> finish

        # tool-output r1 and r2 should be in step 1 (between start[0] and finish[0])
        assert start_steps[0] < tool_outputs[0] < finish_steps[0]
        assert start_steps[0] < tool_outputs[1] < finish_steps[0]

        # tool-output r3 should be in step 2 (between start[1] and finish[1])
        assert start_steps[1] < tool_outputs[2] < finish_steps[1]

        # finish-step should come before next start-step
        assert finish_steps[0] < start_steps[1]
        assert finish_steps[1] < start_steps[2]

    @pytest.mark.asyncio
    async def test_stream_ends_with_finish_step(self):
        """Test that stream always ends with finish-step."""
        async def mock_stream():
            chunk = AIMessageChunk(id="msg-1", content="Hello", chunk_position="last")
            yield chunk

        converter = StreamToVercelConverter()
        events = []
        async for event in converter.stream(mock_stream()):
            events.append(event)

        # Last event should be finish-step
        assert len(events) > 0
        assert events[-1]["type"] == "finish-step"
