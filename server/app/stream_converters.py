"""
Stream converters for transforming LangChain AIMessageChunk to Vercel AI SDK UIMessageChunk.

This module provides separate converters for different LangGraph node types:
- ModelConverter: Converts model/LLM output chunks (reasoning, text, tool_call_chunk)
- ToolsConverter: Converts tool execution output chunks

The converters implement the Vercel AI SDK Data Stream Protocol with start/delta/end patterns.
"""

from typing import AsyncIterator, Dict, Any, Optional, Set
from langchain_core.messages import AIMessageChunk, ToolMessage
import json
import uuid


class BaseConverter:
    """Base class for stream converters with shared utilities."""
    
    def __init__(self):
        """Initialize converter state tracking."""
        self.active_chunks: Dict[str, Dict[str, Any]] = {}  # Track active chunks by ID
        self.seen_indices: Set[int] = set()  # Track seen chunk indices
    
    def _generate_id(self, prefix: str = "") -> str:
        """Generate a unique ID for a chunk."""
        return f"{prefix}{uuid.uuid4().hex[:24]}"
    
    def _format_sse(self, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event."""
        return f"data: {json.dumps(data)}\n\n"
    
    def _emit_start(self, chunk_type: str, chunk_id: str, **kwargs) -> str:
        """Emit a start event."""
        data = {"type": f"{chunk_type}-start", "id": chunk_id}
        data.update(kwargs)
        return self._format_sse(data)
    
    def _emit_delta(self, chunk_type: str, chunk_id: str, delta: str, **kwargs) -> str:
        """Emit a delta event."""
        data = {"type": f"{chunk_type}-delta", "id": chunk_id, "delta": delta}
        data.update(kwargs)
        return self._format_sse(data)
    
    def _emit_end(self, chunk_type: str, chunk_id: str, **kwargs) -> str:
        """Emit an end event."""
        data = {"type": f"{chunk_type}-end", "id": chunk_id}
        data.update(kwargs)
        return self._format_sse(data)
    
    def _emit_available(self, chunk_type: str, chunk_id: str, content: Any, **kwargs) -> str:
        """Emit an available event (alternative to end)."""
        data = {"type": f"{chunk_type}-available", "id": chunk_id}
        if isinstance(content, dict):
            data.update(content)
        else:
            data["content"] = content
        data.update(kwargs)
        return self._format_sse(data)


class ModelConverter(BaseConverter):
    """
    Converter for model/LLM node output.
    
    Handles conversion of:
    - reasoning -> reasoning-start, reasoning-delta, reasoning-end
    - text -> text-start, text-delta, text-end
    - tool_call_chunk -> tool-input-start, tool-input-delta, tool-input-available
    """
    
    def __init__(self):
        super().__init__()
        self.reasoning_id: Optional[str] = None
        self.text_id: Optional[str] = None
        self.tool_call_ids: Dict[int, str] = {}  # Map tool call index to chunk ID
        self.tool_call_inputs: Dict[int, str] = {}  # Accumulate tool call inputs
    
    async def convert(self, chunk: AIMessageChunk) -> AsyncIterator[str]:
        """
        Convert an AIMessageChunk to Vercel AI SDK UIMessageChunk events.
        
        Args:
            chunk: LangChain AIMessageChunk from model stream
            
        Yields:
            SSE formatted string events
        """
        # Handle reasoning content (if present - not all models support this)
        reasoning = getattr(chunk, 'reasoning', None)
        if reasoning:
            async for event in self._handle_reasoning(reasoning):
                yield event
        
        # Handle text content
        if chunk.content:
            async for event in self._handle_text(chunk.content):
                yield event
        
        # Handle tool call chunks (if present)
        tool_call_chunks = getattr(chunk, 'tool_call_chunks', None)
        if tool_call_chunks:
            for tool_chunk in tool_call_chunks:
                async for event in self._handle_tool_call_chunk(tool_chunk):
                    yield event
        
        # Check if this is the last chunk
        chunk_position = getattr(chunk, 'chunk_position', None)
        if chunk_position == 'last':
            async for event in self._finalize_all():
                yield event
    
    async def _handle_reasoning(self, reasoning: str) -> AsyncIterator[str]:
        """Handle reasoning content chunks."""
        if not self.reasoning_id:
            # First reasoning chunk - emit start
            self.reasoning_id = self._generate_id("reasoning_")
            yield self._emit_start("reasoning", self.reasoning_id)
        
        # Emit delta
        if reasoning:
            yield self._emit_delta("reasoning", self.reasoning_id, reasoning)
    
    async def _handle_text(self, content: Any) -> AsyncIterator[str]:
        """Handle text content chunks."""
        # Extract text from content (could be string, dict, or list)
        text = self._extract_text(content)
        if not text:
            return
        
        if not self.text_id:
            # First text chunk - emit start
            self.text_id = self._generate_id("text_")
            yield self._emit_start("text", self.text_id)
        
        # Emit delta
        yield self._emit_delta("text", self.text_id, text)
    
    async def _handle_tool_call_chunk(self, tool_chunk: Any) -> AsyncIterator[str]:
        """
        Handle tool call chunks.
        
        Tool chunks have:
        - index: which tool call this belongs to
        - name: tool name (may be partial)
        - args: tool arguments (may be partial JSON string)
        - id: tool call ID (may be in first chunk only)
        
        Args:
            tool_chunk: Can be Dict or ToolCallChunk object
        """
        # Handle both dict and ToolCallChunk object
        if isinstance(tool_chunk, dict):
            index = tool_chunk.get('index', 0)
            name = tool_chunk.get('name', '')
            args = tool_chunk.get('args', '')
            tool_call_id = tool_chunk.get('id', '')
        else:
            # ToolCallChunk object
            index = getattr(tool_chunk, 'index', 0)
            name = getattr(tool_chunk, 'name', '')
            args = getattr(tool_chunk, 'args', '')
            tool_call_id = getattr(tool_chunk, 'id', '')
        
        # First chunk for this tool call index
        if index not in self.tool_call_ids:
            chunk_id = tool_call_id or self._generate_id("call_")
            self.tool_call_ids[index] = chunk_id
            self.tool_call_inputs[index] = ''
            
            # Emit tool-input-start
            yield self._emit_start(
                "tool-input",
                chunk_id,
                toolCallId=chunk_id,
                toolName=name
            )
        
        chunk_id = self.tool_call_ids[index]
        
        # Accumulate arguments
        if args:
            self.tool_call_inputs[index] += args
            # Emit tool-input-delta with the incremental text
            yield self._format_sse({
                "type": "tool-input-delta",
                "toolCallId": chunk_id,
                "inputTextDelta": args
            })
    
    async def _finalize_all(self) -> AsyncIterator[str]:
        """Finalize all active chunks when stream ends."""
        # Finalize reasoning
        if self.reasoning_id:
            yield self._emit_end("reasoning", self.reasoning_id)
            self.reasoning_id = None
        
        # Finalize text
        if self.text_id:
            yield self._emit_end("text", self.text_id)
            self.text_id = None
        
        # Finalize tool calls
        for index, chunk_id in self.tool_call_ids.items():
            accumulated_input = self.tool_call_inputs.get(index, '')
            try:
                # Parse accumulated JSON string
                parsed_input = json.loads(accumulated_input) if accumulated_input else {}
            except json.JSONDecodeError:
                # If parsing fails, use raw string
                parsed_input = {"raw": accumulated_input}
            
            # Emit tool-input-available
            yield self._format_sse({
                "type": "tool-input-available",
                "toolCallId": chunk_id,
                "input": parsed_input
            })
        
        # Clear tool call tracking
        self.tool_call_ids.clear()
        self.tool_call_inputs.clear()
    
    def _extract_text(self, content: Any) -> str:
        """Extract text from various content formats."""
        if isinstance(content, str):
            return content
        
        if isinstance(content, dict):
            return content.get("text", "")
        
        if isinstance(content, list):
            texts = []
            for part in content:
                if isinstance(part, str):
                    texts.append(part)
                elif isinstance(part, dict):
                    texts.append(part.get("text", ""))
            return "".join(texts)
        
        return ""
    
    async def finalize(self) -> AsyncIterator[str]:
        """Explicitly finalize the stream (called when no more chunks)."""
        async for event in self._finalize_all():
            yield event


class ToolsConverter(BaseConverter):
    """
    Converter for tools node output.
    
    Handles conversion of:
    - ToolMessage text -> tool-output-start, tool-output-delta, tool-output-end
    """
    
    def __init__(self):
        super().__init__()
        self.tool_output_ids: Dict[str, str] = {}  # Map tool_call_id to chunk ID
        self.tool_outputs: Dict[str, str] = {}  # Accumulate tool outputs as strings
        self.tool_output_types: Dict[str, Any] = {}  # Store original content for proper output
    
    async def convert(self, message: ToolMessage) -> AsyncIterator[str]:
        """
        Convert a ToolMessage to Vercel AI SDK tool output events.
        
        Args:
            message: LangChain ToolMessage from tool execution
            
        Yields:
            SSE formatted string events
        """
        tool_call_id = message.tool_call_id
        content = message.content
        
        if not tool_call_id:
            # Can't process without tool_call_id
            return
        
        # Store original content type
        if tool_call_id not in self.tool_output_types:
            self.tool_output_types[tool_call_id] = content
        
        # Convert content to string for streaming
        if isinstance(content, str):
            output_text = content
        else:
            output_text = json.dumps(content) if isinstance(content, dict) else str(content)
        
        # First output for this tool call
        if tool_call_id not in self.tool_output_ids:
            chunk_id = self._generate_id("output_")
            self.tool_output_ids[tool_call_id] = chunk_id
            self.tool_outputs[tool_call_id] = ''
            
            # Emit tool-output-start
            yield self._format_sse({
                "type": "tool-output-start",
                "toolCallId": tool_call_id,
                "id": chunk_id
            })
        
        chunk_id = self.tool_output_ids[tool_call_id]
        
        # Accumulate and emit delta
        if output_text:
            self.tool_outputs[tool_call_id] += output_text
            
            # For streaming, chunk the output
            for text_chunk in self._chunk_text(output_text, 100):
                yield self._format_sse({
                    "type": "tool-output-delta",
                    "toolCallId": tool_call_id,
                    "id": chunk_id,
                    "delta": text_chunk
                })
    
    async def finalize_tool(self, tool_call_id: str) -> AsyncIterator[str]:
        """Finalize a specific tool output."""
        if tool_call_id in self.tool_output_ids:
            chunk_id = self.tool_output_ids[tool_call_id]
            
            # Use the original content if available, otherwise use accumulated
            if tool_call_id in self.tool_output_types:
                raw_content = self.tool_output_types[tool_call_id]
            else:
                raw_content = self.tool_outputs.get(tool_call_id, '')
            
            # Try to parse as JSON if it's a string, otherwise use as-is
            if isinstance(raw_content, str):
                try:
                    output = json.loads(raw_content)
                except (json.JSONDecodeError, TypeError):
                    output = raw_content
            else:
                output = raw_content
            
            # Emit tool-output-available
            yield self._format_sse({
                "type": "tool-output-available",
                "toolCallId": tool_call_id,
                "output": output
            })
            
            # Clean up
            del self.tool_output_ids[tool_call_id]
            del self.tool_outputs[tool_call_id]
            if tool_call_id in self.tool_output_types:
                del self.tool_output_types[tool_call_id]
    
    async def finalize_all(self) -> AsyncIterator[str]:
        """Finalize all pending tool outputs."""
        for tool_call_id in list(self.tool_output_ids.keys()):
            async for event in self.finalize_tool(tool_call_id):
                yield event
    
    def _chunk_text(self, text: str, chunk_size: int = 100) -> list[str]:
        """Split text into chunks for streaming."""
        if not text:
            return []
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


class StreamConverter:
    """
    Main converter that routes chunks to appropriate converters.
    
    This class handles the overall stream conversion, determining whether
    a chunk comes from the model or tools node and routing accordingly.
    """
    
    def __init__(self):
        self.model_converter = ModelConverter()
        self.tools_converter = ToolsConverter()
        self.message_id: Optional[str] = None
    
    async def convert_stream(
        self, 
        chunk_stream: AsyncIterator[Any]
    ) -> AsyncIterator[str]:
        """
        Convert a LangChain stream to Vercel AI SDK format.
        
        Args:
            chunk_stream: AsyncIterator of LangChain messages/chunks
            
        Yields:
            SSE formatted events following Vercel AI SDK protocol
        """
        # Emit message start
        if not self.message_id:
            self.message_id = self._generate_message_id()
            yield self._format_sse({
                "type": "start",
                "messageId": self.message_id
            })
        
        try:
            async for chunk in chunk_stream:
                # Route based on chunk type
                if isinstance(chunk, AIMessageChunk):
                    async for event in self.model_converter.convert(chunk):
                        yield event
                elif isinstance(chunk, ToolMessage):
                    async for event in self.tools_converter.convert(chunk):
                        yield event
                    # Finalize tool output when we get the complete message
                    if chunk.tool_call_id:
                        async for event in self.tools_converter.finalize_tool(chunk.tool_call_id):
                            yield event
                else:
                    # Unknown chunk type - try to extract text
                    if hasattr(chunk, 'content'):
                        text_chunk = AIMessageChunk(content=chunk.content)
                        async for event in self.model_converter.convert(text_chunk):
                            yield event
        
        finally:
            # Finalize all pending chunks
            async for event in self.model_converter.finalize():
                yield event
            async for event in self.tools_converter.finalize_all():
                yield event
            
            # Emit finish message
            yield self._format_sse({"type": "finish"})
            
            # Emit stream termination
            yield "data: [DONE]\n\n"
    
    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        return f"msg_{uuid.uuid4().hex[:24]}"
    
    def _format_sse(self, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event."""
        return f"data: {json.dumps(data)}\n\n"
