"""
LLM agent implementation using langchain agent framework with Aliyun Dashscope.
"""

from typing import Optional, AsyncIterator, Dict, Any, Union, List, cast
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import BaseMessage, HumanMessage, AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.memory import InMemoryStore
from langchain.agents import create_agent
from pydantic import SecretStr
from .config import config
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from .vercel_ui_message_transform.transform import convert_to_ui_messages
import logging


def get_weather(city: str) -> dict[str, str]:
    """Get weather for a given city."""

    return {f"{city}": "Sunny"}


class LLMAgent:
    """LangChain Agent with Aliyun Dashscope integration and fallback support."""

    def __init__(self, init_pool: bool = True) -> None:
        """
        Initialize the agent with LLM and tools (prepared for future expansion).

        Args:
            init_pool: Whether to initialize the connection pool immediately.
                      Set to False for testing to avoid async pool issues.
        """
        api_key = config.DASHSCOPE_API_KEY
        self.llm = ChatTongyi(
            model=config.DASHSCOPE_MODEL,
            api_key=SecretStr(api_key) if api_key else None,
            streaming=True,
        )
        self.tools: List = [get_weather]  # Empty tools list, ready for future additions
        self.store = InMemoryStore()
        if init_pool:
            self.pool = AsyncConnectionPool(
                "postgresql://noeticai:noeticai@localhost:5432/langchain_demo",
                kwargs={
                    "autocommit": True,  # Critical
                    "row_factory": dict_row,
                    "prepare_threshold": 0,
                },
                open=True,
            )
            self.checkpointer = AsyncPostgresSaver(self.pool)  # type: ignore
        else:
            self.checkpointer = None  # type: ignore
        self.agent: Any
        self.fallback_mode = not config.is_llm_configured()
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,  # Empty for now, ready for future tools
            system_prompt=(
                "You are a helpful AI assistant. "
                "Answer the user's questions concisely."
            ),
            checkpointer=self.checkpointer,
            # store=self.store
        )

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

    async def get_history(
        self, thread_id: str, checkpoint_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a thread.

        Args:
            thread_id: The thread ID to get history for
            checkpoint_id: Optional checkpoint ID to get history up to that point

        Returns:
            List of message dictionaries
        """
        try:
            config = {"configurable": {"thread_id": thread_id}}
            if checkpoint_id:
                config["configurable"]["checkpoint_id"] = checkpoint_id

            state = await self.agent.aget_state(config)
            messages = state.values.get("messages", [])

            # Convert messages to dictionaries
            return convert_to_ui_messages(messages)
        except Exception as e:
            logging.error(f"Error getting history: {str(e)}")
            return []

    async def astream_messages(
        self,
        input: Union[str, Dict[str, Any], BaseMessage],
        config: Optional[RunnableConfig] = None,
    ) -> AsyncIterator[BaseMessage]:
        """
        Stream the agent's response as BaseMessage objects for proper conversion.

        This method returns raw LangChain message chunks suitable for conversion
        to Vercel AI SDK UIMessage format.

        Args:
            input: The input (same as astream)
            config: Optional configuration with thread_id and checkpoint_id

        Yields:
            BaseMessage objects
        """
        try:
            prompt_text = self._extract_prompt(input)

            # Use provided config or default to thread_id "1"
            if config is None:
                user_id = "1"
                config = {"configurable": {"thread_id": "1", "user_id": user_id}}

            # Stream using messages mode to get proper AIMessageChunk objects
            if self.agent:
                async for stream_mode, payload in self.agent.astream(
                    {"messages": [HumanMessage(content=prompt_text)]},
                    config,
                    stream_mode=[
                        "messages",
                        "checkpoints",
                        "custom",
                        "debug",
                        "tasks",
                        "updates",
                        "values",
                    ],
                    print_mode=[
                        "messages",
                        "checkpoints",
                        "custom",
                        "debug",
                        "tasks",
                        "updates",
                        "values",
                    ],
                ):
                    if stream_mode == "messages":
                        [chunk, _] = cast(tuple[BaseMessage, dict[str, Any]], payload)
                        # Yield the raw chunk for conversion
                        yield chunk

            else:
                # No agent - use direct LLM streaming
                if self.llm:
                    async for chunk in self.llm.astream(prompt_text):
                        yield chunk
        except Exception as e:
            # Log the error and yield an error message chunk
            logging.error(f"Error in astream_messages: {str(e)}")
            yield AIMessageChunk(content=f"Error: {str(e)}")
            raise Exception(f"LLM service error: {str(e)}")


# Global agent instance
agent = LLMAgent()
