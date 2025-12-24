"""
Tests for conversation history features.
"""

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def agent():
    """Create an agent instance for testing."""
    # Import here to avoid importing the global agent
    from app.agent import LLMAgent

    # Initialize without pool to avoid async issues in tests
    agent = LLMAgent(init_pool=False)
    return agent


@pytest.mark.asyncio
async def test_astream_messages_without_checkpointer(agent):
    """Test streaming messages without checkpointer (fallback mode)."""
    chunks = []
    async for chunk in agent.astream_messages("Test message"):
        chunks.append(chunk)

    assert len(chunks) > 0


@pytest.mark.asyncio
async def test_astream_messages_with_config(agent):
    """Test streaming messages with explicit config."""
    config = {"configurable": {"thread_id": "test-thread"}}

    chunks = []
    async for chunk in agent.astream_messages("Test message", config=config):
        chunks.append(chunk)

    assert len(chunks) > 0
