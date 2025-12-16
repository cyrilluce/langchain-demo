"""
LLM agent implementation using langchain agent framework with Aliyun Dashscope.
"""

from typing import Optional, AsyncIterator, Dict, Any, Union, List
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from pydantic import SecretStr
from .config import config
import asyncio


class LLMAgent:
    """LangChain Agent with Aliyun Dashscope integration and fallback support."""

    def __init__(self) -> None:
        """Initialize the agent with LLM and tools (prepared for future expansion)."""
        api_key = config.DASHSCOPE_API_KEY
        self.llm = ChatTongyi(
            model=config.DASHSCOPE_MODEL,
            api_key=SecretStr(api_key) if api_key else None,
        )
        self.tools: List = []  # Empty tools list, ready for future additions
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,  # Empty for now, ready for future tools
            system_prompt="You are a helpful AI assistant. Answer the user's questions concisely.",
        )
        self.fallback_mode = not config.is_llm_configured()

    async def ainvoke(
        self,
        input: Union[str, Dict[str, Any], BaseMessage],
        config: Optional[RunnableConfig] = None,
    ) -> str:
        """
        Invoke the agent with a prompt using langchain's standard interface.

        Args:
            input: The input can be:
                - str: Direct prompt text
                - Dict: Input variables (e.g., {"input": "prompt text"})
                - BaseMessage: A langchain message object
            config: Optional configuration for the invocation

        Returns:
            Generated response from agent or fallback message

        Raises:
            Exception: If agent processing fails (non-fallback mode)
        """
        if self.fallback_mode:
            prompt_text = self._extract_prompt(input)
            return self._fallback_response(prompt_text)

        try:
            # Extract prompt text
            prompt_text = self._extract_prompt(input)

            # Invoke the agent executor
            if self.agent:
                result = await self.agent.ainvoke(
                    {"messages": [HumanMessage(content=prompt_text)]}, config=config
                )
                # LangGraph agent returns a state dict with 'messages' key
                # Extract the last AI message
                if isinstance(result, dict) and "messages" in result:
                    messages = result["messages"]
                    if messages:
                        last_msg = messages[-1]
                        if isinstance(last_msg, AIMessage):
                            return (
                                last_msg.content
                                if isinstance(last_msg.content, str)
                                else str(last_msg.content)
                            )
                return str(result)
            else:
                return self._fallback_response(prompt_text)
        except Exception as e:
            raise Exception(f"LLM service error: {str(e)}")

    async def astream(
        self,
        input: Union[str, Dict[str, Any], BaseMessage],
        config: Optional[RunnableConfig] = None,
    ) -> AsyncIterator[str]:
        """
        Stream the agent's response using langchain's standard interface.

        Preference order:
        1. Direct LLM streaming (highest fidelity, no tools)
        2. Agent streaming (when tools are in play)
        3. Chunked fallback from the full response
        """
        if self.fallback_mode:
            prompt_text = self._extract_prompt(input)
            response = self._fallback_response(prompt_text)
            for word in response.split():
                yield word + " "
                await asyncio.sleep(0.05)
            return

        try:
            prompt_text = self._extract_prompt(input)

            # 1) Prefer direct chat model streaming when no tools are registered
            if self.llm and not self.tools:
                emitted = False
                async for chunk in self.agent.astream(
                    {"messages": [HumanMessage(content=prompt_text)]},
                    config=config,
                    stream_mode="messages",
                ):
                    text_chunk = self._extract_text_from_llm_chunk(chunk)
                    if text_chunk:
                        emitted = True
                        yield text_chunk
                if emitted:
                    return

            # 2) Fall back to LangGraph agent streaming (needed when tools are active)
            if self.agent:
                emitted = False
                async for chunk in self.agent.astream(
                    {"messages": [HumanMessage(content=prompt_text)]},
                    config=config,
                    stream_mode="messages",
                ):
                    text_chunk = self._extract_text_from_agent_chunk(chunk)
                    if text_chunk:
                        emitted = True
                        yield text_chunk
                if emitted:
                    return

            # 3) Last resort: chunk the final response so streaming never returns empty text
            final_response = await self.ainvoke(prompt_text)
            for piece in self._chunk_text(final_response):
                if piece:
                    yield piece
        except Exception as e:
            raise Exception(f"LLM service error: {str(e)}")

    def _extract_prompt(self, input: Union[str, Dict[str, Any], BaseMessage]) -> str:
        """
        Extract prompt text from various input formats.

        Args:
            input: The input in various formats

        Returns:
            Extracted prompt text
        """
        if isinstance(input, str):
            return input
        elif isinstance(input, dict):
            # Try common keys
            return input.get("input") or input.get("prompt") or str(input)
        elif isinstance(input, BaseMessage):
            content = input.content
            return content if isinstance(content, str) else str(content)
        else:
            return str(input)

    def _fallback_response(self, prompt: str) -> str:
        """Generate a fallback response when LLM is not configured."""
        return (
            f"[Fallback Mode] Echo: {prompt[:100]}... "
            f"(LLM not configured. Set DASHSCOPE_API_KEY to enable AI responses.)"
        )

    def _extract_text_from_llm_chunk(self, chunk: Any) -> str:
        """Best-effort extraction of textual content from a chat model chunk."""
        if isinstance(chunk, str):
            return chunk

        content = getattr(chunk, "content", None)
        text = self._coerce_content_to_text(content)
        if text:
            return text

        chunk_text = getattr(chunk, "text", None)
        if isinstance(chunk_text, str):
            return chunk_text

        return ""

    def _extract_text_from_agent_chunk(self, chunk: Any) -> str:
        """Extract assistant message text from LangGraph agent state updates."""
        if isinstance(chunk, dict) and "messages" in chunk:
            parts: List[str] = []
            for msg in chunk["messages"]:
                if isinstance(msg, AIMessage):
                    text = self._coerce_content_to_text(msg.content)
                    if text:
                        parts.append(text)
            return "".join(parts)
        return ""

    def _coerce_content_to_text(self, content: Any) -> str:
        """Normalize various LangChain content payloads into plain text."""
        if isinstance(content, str):
            return content

        if isinstance(content, dict):
            text_value = content.get("text")
            return text_value if isinstance(text_value, str) else ""

        if isinstance(content, list):
            fragments: List[str] = []
            for part in content:
                if isinstance(part, str):
                    fragments.append(part)
                elif isinstance(part, dict):
                    text_value = part.get("text")
                    if isinstance(text_value, str):
                        fragments.append(text_value)
                elif hasattr(part, "content"):
                    inner = getattr(part, "content")
                    if isinstance(inner, str):
                        fragments.append(inner)
            return "".join(fragments)

        if content is not None:
            stringified = str(content)
            return stringified if stringified and stringified != "None" else ""

        return ""

    def _chunk_text(self, text: Any, chunk_size: int = 120) -> List[str]:
        """Split a full response into smaller chunks for pseudo-streaming."""
        if text is None:
            return []

        if not isinstance(text, str):
            text = str(text)

        if not text:
            return []

        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    def is_ready(self) -> bool:
        """Check if the agent is ready to process requests."""
        return True  # Agent is always ready (fallback mode or LLM mode)

    def add_tool(self, tool: Any) -> None:
        """
        Add a tool to the agent (for future expansion).

        Args:
            tool: A LangChain tool object

        Note: After adding tools, you need to reinitialize the agent
        """
        self.tools.append(tool)
        # Reinitialize agent with new tools
        if not self.fallback_mode and self.llm:
            try:
                self.agent = create_agent(
                    model=self.llm,
                    tools=self.tools,
                    system_prompt="You are a helpful AI assistant. Use the available tools when needed to answer questions.",
                    debug=True,  # Enable debug mode when using tools
                )
            except Exception as e:
                print(f"Failed to reinitialize agent with tools: {e}")

    async def astream_messages(
        self,
        input: Union[str, Dict[str, Any], BaseMessage],
        config: Optional[RunnableConfig] = None,
    ) -> AsyncIterator[Any]:
        """
        Stream the agent's response as AIMessageChunk objects for proper conversion.

        This method returns raw LangChain message chunks suitable for conversion
        to Vercel AI SDK UIMessage format.

        Args:
            input: The input (same as astream)
            config: Optional configuration

        Yields:
            AIMessageChunk or ToolMessage objects
        """
        if self.fallback_mode:
            prompt_text = self._extract_prompt(input)
            response = self._fallback_response(prompt_text)
            # Emit as chunks
            for word in response.split():
                yield AIMessage(content=word + " ")
                await asyncio.sleep(0.05)
            return

        try:
            prompt_text = self._extract_prompt(input)

            # Stream using messages mode to get proper AIMessageChunk objects
            if self.agent:
                async for chunk in self.agent.astream(
                    {"messages": [HumanMessage(content=prompt_text)]},
                    config=config,
                    stream_mode="messages",
                ):
                    # Yield the raw chunk for conversion
                    yield chunk
            else:
                # No agent - use direct LLM streaming
                if self.llm:
                    async for chunk in self.llm.astream(prompt_text):
                        yield chunk
        except Exception as e:
            raise Exception(f"LLM service error: {str(e)}")

    # Backward compatibility methods
    async def process_prompt(self, prompt: str) -> str:
        """Legacy method for backward compatibility. Use ainvoke() instead."""
        return await self.ainvoke(prompt)

    async def process_prompt_stream(self, prompt: str) -> AsyncIterator[str]:
        """Legacy method for backward compatibility. Use astream() instead."""
        async for chunk in self.astream(prompt):
            yield chunk


# Global agent instance
agent = LLMAgent()
