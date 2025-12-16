"""
Unit tests for stream converters.

Tests the conversion from LangChain AIMessageChunk to Vercel AI SDK UIMessageChunk.
"""

import pytest
import json
from langchain_core.messages import AIMessageChunk, ToolMessage
from app.stream_converters import ModelConverter, ToolsConverter, StreamConverter


class TestModelConverter:
    """Test ModelConverter class."""
    
    @pytest.mark.asyncio
    async def test_text_conversion(self):
        """Test basic text chunk conversion."""
        converter = ModelConverter()
        
        # Simulate streaming text chunks
        chunk1 = AIMessageChunk(content="Hello")
        chunk2 = AIMessageChunk(content=" world")
        chunk3 = AIMessageChunk(content="!", chunk_position="last")
        
        events = []
        async for event in converter.convert(chunk1):
            events.append(event)
        async for event in converter.convert(chunk2):
            events.append(event)
        async for event in converter.convert(chunk3):
            events.append(event)
        
        # Parse events
        parsed_events = [json.loads(e.replace("data: ", "").strip()) for e in events if e.strip() and not e.startswith("data: [DONE]")]
        
        # Should have: text-start, text-delta (Hello), text-delta ( world), text-delta (!), text-end
        assert len(parsed_events) >= 4
        assert parsed_events[0]["type"] == "text-start"
        assert "id" in parsed_events[0]
        
        # Find text deltas
        deltas = [e for e in parsed_events if e["type"] == "text-delta"]
        assert len(deltas) == 3
        assert deltas[0]["delta"] == "Hello"
        assert deltas[1]["delta"] == " world"
        assert deltas[2]["delta"] == "!"
        
        # Should end with text-end
        assert parsed_events[-1]["type"] == "text-end"
    
    @pytest.mark.asyncio
    async def test_reasoning_conversion(self):
        """Test reasoning chunk conversion."""
        converter = ModelConverter()
        
        # Create chunk with reasoning attribute
        chunk = AIMessageChunk(content=[dict({"type":"reasoning", "reasoning":"Let me think..."})])
        
        events = []
        async for event in converter.convert(chunk):
            events.append(event)
        
        # Finalize to get end event
        async for event in converter.finalize():
            events.append(event)
        
        parsed_events = [json.loads(e.replace("data: ", "").strip()) for e in events if e.strip()]
        
        # Should have: reasoning-start, reasoning-delta, reasoning-end
        assert any(e["type"] == "reasoning-start" for e in parsed_events)
        assert any(e["type"] == "reasoning-delta" for e in parsed_events)
        assert any(e["type"] == "reasoning-end" for e in parsed_events)
        
        # Check delta content
        delta = next(e for e in parsed_events if e["type"] == "reasoning-delta")
        assert delta["delta"] == "Let me think..."
    
    @pytest.mark.asyncio
    async def test_tool_call_chunk_conversion(self):
        """Test tool call chunk conversion."""
        converter = ModelConverter()
        
        # Simulate tool call chunks (progressive building)
        chunk1 = AIMessageChunk(content="", tool_call_chunks=[
            {"index": 0, "name": "get_weather", "args": "", "id": "call_123"}
        ])
        chunk2 = AIMessageChunk(content="", tool_call_chunks=[
            {"index": 0, "name": "", "args": '{"city":', "id": ""}
        ])
        chunk3 = AIMessageChunk(content="", tool_call_chunks=[
            {"index": 0, "name": "", "args": ' "SF"}', "id": ""}
        ])
        
        events = []
        async for event in converter.convert(chunk1):
            events.append(event)
        async for event in converter.convert(chunk2):
            events.append(event)
        async for event in converter.convert(chunk3):
            events.append(event)
        
        # Finalize to get tool-input-available
        async for event in converter.finalize():
            events.append(event)
        
        parsed_events = [json.loads(e.replace("data: ", "").strip()) for e in events if e.strip()]
        
        # Should have: tool-input-start, tool-input-delta (x2), tool-input-available
        start_event = next(e for e in parsed_events if e["type"] == "tool-input-start")
        assert start_event["toolCallId"] == "call_123"
        assert start_event["toolName"] == "get_weather"
        
        delta_events = [e for e in parsed_events if e["type"] == "tool-input-delta"]
        assert len(delta_events) == 2
        assert delta_events[0]["inputTextDelta"] == '{"city":'
        assert delta_events[1]["inputTextDelta"] == ' "SF"}'
        
        available_event = next(e for e in parsed_events if e["type"] == "tool-input-available")
        assert available_event["toolCallId"] == "call_123"
        assert available_event["input"]["city"] == "SF"


class TestToolsConverter:
    """Test ToolsConverter class."""
    
    @pytest.mark.asyncio
    async def test_tool_output_conversion(self):
        """Test tool output message conversion."""
        converter = ToolsConverter()
        
        # Create tool message
        tool_msg = ToolMessage(
            content="The weather is sunny",
            tool_call_id="call_123"
        )
        
        events = []
        async for event in converter.convert(tool_msg):
            events.append(event)
        
        # Finalize tool output
        async for event in converter.finalize_tool("call_123"):
            events.append(event)
        
        parsed_events = [json.loads(e.replace("data: ", "").strip()) for e in events if e.strip()]
        
        # Should have: tool-output-start, tool-output-delta (chunked), tool-output-available
        start_event = next(e for e in parsed_events if e["type"] == "tool-output-start")
        assert start_event["toolCallId"] == "call_123"
        
        delta_events = [e for e in parsed_events if e["type"] == "tool-output-delta"]
        assert len(delta_events) >= 1
        
        # Reconstruct output from deltas
        output_text = "".join(e["delta"] for e in delta_events)
        assert output_text == "The weather is sunny"
        
        available_event = next(e for e in parsed_events if e["type"] == "tool-output-available")
        assert available_event["toolCallId"] == "call_123"
        assert available_event["output"] == "The weather is sunny"
    
    @pytest.mark.asyncio
    async def test_tool_output_json_content(self):
        """Test tool output with JSON content."""
        converter = ToolsConverter()
        
        # Note: ToolMessage converts dict content to string automatically
        # So we test with a JSON string that can be parsed back
        json_content = '{"weather": "sunny", "temp": 72}'
        tool_msg = ToolMessage(
            content=json_content,
            tool_call_id="call_456"
        )
        
        events = []
        async for event in converter.convert(tool_msg):
            events.append(event)
        
        async for event in converter.finalize_tool("call_456"):
            events.append(event)
        
        parsed_events = [json.loads(e.replace("data: ", "").strip()) for e in events if e.strip()]
        
        # Check available event has parsed JSON
        available_event = next(e for e in parsed_events if e["type"] == "tool-output-available")
        
        # The output should be parsed back to dict from JSON string
        output = available_event["output"]
        assert isinstance(output, dict)
        assert output["weather"] == "sunny"
        assert output["temp"] == 72


class TestStreamConverter:
    """Test the main StreamConverter class."""
    
    @pytest.mark.asyncio
    async def test_full_stream_conversion(self):
        """Test full stream conversion with mixed content."""
        converter = StreamConverter()
        
        async def mock_stream():
            """Mock LangChain stream with various chunk types."""
            # Text chunks
            yield AIMessageChunk(content="Hello")
            yield AIMessageChunk(content=" world")
            # Tool call
            yield AIMessageChunk(content="", tool_call_chunks=[
                {"index": 0, "name": "get_info", "args": '{"q":"test"}', "id": "call_1"}
            ])
            # Tool result
            yield ToolMessage(content="Result here", tool_call_id="call_1")
            # Final text
            yield AIMessageChunk(content=" Done", chunk_position="last")
        
        events = []
        async for event in converter.convert_stream(mock_stream()):
            events.append(event)
        
        parsed_events = []
        for e in events:
            if e.strip() and not e.startswith("data: [DONE]"):
                try:
                    parsed_events.append(json.loads(e.replace("data: ", "").strip()))
                except json.JSONDecodeError:
                    pass
        
        # Should have message start
        assert parsed_events[0]["type"] == "start"
        assert "messageId" in parsed_events[0]
        
        # Should have text events
        assert any(e["type"] == "text-start" for e in parsed_events)
        assert any(e["type"] == "text-delta" for e in parsed_events)
        
        # Should have tool events
        assert any(e["type"] == "tool-input-start" for e in parsed_events)
        assert any(e["type"] == "tool-output-start" for e in parsed_events)
        
        # Should end with finish
        finish_events = [e for e in parsed_events if e["type"] == "finish"]
        assert len(finish_events) == 1
    
    @pytest.mark.asyncio
    async def test_stream_with_reasoning(self):
        """Test stream conversion with reasoning content."""
        converter = StreamConverter()
        
        async def mock_stream():
            """Mock stream with reasoning."""
            chunk = AIMessageChunk(content=[{"type":"reasoning", "reasoning": "I think..."}, "Answer"])
            yield chunk
        
        events = []
        async for event in converter.convert_stream(mock_stream()):
            events.append(event)
        
        parsed_events = []
        for e in events:
            if e.strip() and not e.startswith("data: [DONE]"):
                try:
                    parsed_events.append(json.loads(e.replace("data: ", "").strip()))
                except json.JSONDecodeError:
                    pass
        
        # Should have reasoning events
        assert any(e["type"] == "reasoning-start" for e in parsed_events)
        assert any(e["type"] == "reasoning-delta" for e in parsed_events)
        assert any(e["type"] == "reasoning-end" for e in parsed_events)
        
        # And text events
        assert any(e["type"] == "text-start" for e in parsed_events)


class TestUIMessageStreamHelpers:
    """Test helper functions for UI message stream."""
    
    def test_extract_prompt_from_messages(self):
        """Test prompt extraction from UIMessage format."""
        from app.ui_message_stream import extract_prompt_from_messages
        
        # Test with parts format
        messages = [
            {
                "id": "msg1",
                "role": "user",
                "parts": [
                    {"type": "text", "text": "Hello AI"}
                ]
            }
        ]
        
        prompt = extract_prompt_from_messages(messages)
        assert prompt == "Hello AI"
        
        # Test with content fallback
        messages = [
            {
                "id": "msg2",
                "role": "user",
                "content": "Fallback content"
            }
        ]
        
        prompt = extract_prompt_from_messages(messages)
        assert prompt == "Fallback content"
        
        # Test with multiple messages (should get last user message)
        messages = [
            {"id": "msg1", "role": "user", "parts": [{"type": "text", "text": "First"}]},
            {"id": "msg2", "role": "assistant", "parts": [{"type": "text", "text": "Response"}]},
            {"id": "msg3", "role": "user", "parts": [{"type": "text", "text": "Second"}]}
        ]
        
        prompt = extract_prompt_from_messages(messages)
        assert prompt == "Second"
    
    def test_extract_prompt_error_cases(self):
        """Test error handling in prompt extraction."""
        from app.ui_message_stream import extract_prompt_from_messages
        
        # Empty messages
        with pytest.raises(ValueError, match="No messages provided"):
            extract_prompt_from_messages([])
        
        # No user messages
        messages = [
            {"id": "msg1", "role": "assistant", "parts": [{"type": "text", "text": "Hi"}]}
        ]
        
        with pytest.raises(ValueError, match="No valid user message found"):
            extract_prompt_from_messages(messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
