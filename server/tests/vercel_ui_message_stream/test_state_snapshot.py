"""
Unit tests for StateSnapshot handling in stream converter.

Tests that verify StateSnapshot conversion to data-checkpoint events.
"""

import pytest
from langchain_core.messages import AIMessageChunk, ToolMessage
from langgraph.types import StateSnapshot

from app.vercel_ui_message_stream.converter import StreamToVercelConverter


class TestStreamStateSnapshot:
    """Test StateSnapshot handling in stream converter."""

    @pytest.mark.asyncio
    async def test_state_snapshot_default_converter(self):
        """
        Test that StateSnapshot is converted using default converter.

        Expected output:
        {
            "type": "data-checkpoint",
            "transient": True,
            "checkpoint": {"id": "xxx", "parent": "xxx"}
        }
        """
        async def mock_stream():
            # Create a mock StateSnapshot
            snapshot = StateSnapshot(
                values={},
                next=(),
                config={
                    "configurable": {
                        "checkpoint_id": "checkpoint-123",
                        "thread_id": "thread-1",
                    }
                },
                metadata={},
                created_at="2024-01-01T00:00:00Z",
                parent_config={
                    "configurable": {
                        "checkpoint_id": "checkpoint-parent",
                    }
                },
                tasks=(),
                interrupts=(),
            )
            yield snapshot

        converter = StreamToVercelConverter()
        events = []
        async for event in converter.stream(mock_stream()):
            events.append(event)

        # Should have exactly one event
        assert len(events) == 1

        # Verify event structure
        event = events[0]
        assert event["type"] == "data-checkpoint"
        assert event["transient"] is True
        assert "checkpoint" in event
        assert event["checkpoint"]["id"] == "checkpoint-123"
        assert event["checkpoint"]["parent"] == "checkpoint-parent"

    @pytest.mark.asyncio
    async def test_state_snapshot_custom_converter(self):
        """
        Test that custom checkpoint converter is used when provided.
        """

        def custom_converter(snapshot: StateSnapshot) -> dict:
            """Custom converter that adds extra metadata."""
            return {
                "type": "custom-checkpoint",
                "data": {
                    "checkpoint_id": snapshot.config.get("configurable", {}).get(
                        "checkpoint_id"
                    ),
                    "custom_field": "custom_value",
                },
            }

        async def mock_stream():
            snapshot = StateSnapshot(
                values={},
                next=(),
                config={
                    "configurable": {
                        "checkpoint_id": "checkpoint-456",
                    }
                },
                metadata={},
                created_at="2024-01-01T00:00:00Z",
                parent_config=None,
                tasks=(),
                interrupts=(),
            )
            yield snapshot

        converter = StreamToVercelConverter(checkpoint_converter=custom_converter)
        events = []
        async for event in converter.stream(mock_stream()):
            events.append(event)

        # Should have exactly one event
        assert len(events) == 1

        # Verify custom converter was used
        event = events[0]
        assert event["type"] == "custom-checkpoint"
        assert event["data"]["checkpoint_id"] == "checkpoint-456"
        assert event["data"]["custom_field"] == "custom_value"

    @pytest.mark.asyncio
    async def test_mixed_stream_with_snapshot(self):
        """
        Test mixed stream with AI messages, tool messages and state snapshots.

        Expected flow:
        - start-step (AI message)
        - AI events
        - data-checkpoint (StateSnapshot - no step change)
        - tool-output (ToolMessage - no step change)
        - finish-step (end of stream)
        """
        async def mock_stream():
            # AI message
            yield AIMessageChunk(
                id="msg-1",
                content="Processing",
                tool_call_chunks=[
                    {
                        "id": "call-1",
                        "name": "search",
                        "args": '{"query":"test"}',
                        "index": 0,
                    }
                ],
                chunk_position="last",
            )

            # State snapshot in the middle
            snapshot = StateSnapshot(
                values={},
                next=(),
                config={"configurable": {"checkpoint_id": "chk-1"}},
                metadata={},
                created_at="2024-01-01T00:00:00Z",
                parent_config=None,
                tasks=(),
                interrupts=(),
            )
            yield snapshot

            # Tool message
            tool_msg = ToolMessage(
                content='{"result": "found"}',
                tool_call_id="call-1",
                name="search",
            )
            tool_msg.id = "tool-1"
            yield tool_msg

        converter = StreamToVercelConverter()
        events = []
        async for event in converter.stream(mock_stream()):
            events.append(event)

        event_types = [e["type"] for e in events]

        # Verify step lifecycle
        assert event_types[0] == "start-step"
        assert event_types[-1] == "finish-step"

        # Verify data-checkpoint is present and doesn't create new step
        checkpoint_indices = [
            i for i, t in enumerate(event_types) if t == "data-checkpoint"
        ]
        assert len(checkpoint_indices) == 1

        # data-checkpoint should be between start-step and finish-step
        assert 0 < checkpoint_indices[0] < len(events) - 1

        # Should only have one start-step and one finish-step
        start_steps = [t for t in event_types if t == "start-step"]
        finish_steps = [t for t in event_types if t == "finish-step"]
        assert len(start_steps) == 1
        assert len(finish_steps) == 1

    @pytest.mark.asyncio
    async def test_state_snapshot_without_parent(self):
        """
        Test StateSnapshot without parent_config.
        """
        async def mock_stream():
            snapshot = StateSnapshot(
                values={},
                next=(),
                config={"configurable": {"checkpoint_id": "chk-no-parent"}},
                metadata={},
                created_at="2024-01-01T00:00:00Z",
                parent_config=None,
                tasks=(),
                interrupts=(),
            )
            yield snapshot

        converter = StreamToVercelConverter()
        events = []
        async for event in converter.stream(mock_stream()):
            events.append(event)

        assert len(events) == 1
        event = events[0]
        assert event["type"] == "data-checkpoint"
        assert event["checkpoint"]["id"] == "chk-no-parent"
        assert event["checkpoint"]["parent"] is None

    @pytest.mark.asyncio
    async def test_state_snapshot_without_config(self):
        """
        Test StateSnapshot with missing or incomplete config.
        """
        async def mock_stream():
            snapshot = StateSnapshot(
                values={},
                next=(),
                config={},  # Empty config
                metadata={},
                created_at="2024-01-01T00:00:00Z",
                parent_config=None,
                tasks=(),
                interrupts=(),
            )
            yield snapshot

        converter = StreamToVercelConverter()
        events = []
        async for event in converter.stream(mock_stream()):
            events.append(event)

        assert len(events) == 1
        event = events[0]
        assert event["type"] == "data-checkpoint"
        # Should fallback to "unknown"
        assert event["checkpoint"]["id"] == "unknown"
        assert event["checkpoint"]["parent"] is None

    @pytest.mark.asyncio
    async def test_multiple_snapshots_in_stream(self):
        """
        Test stream with multiple state snapshots.
        """
        async def mock_stream():
            # First AI message
            yield AIMessageChunk(id="msg-1", content="Step 1", chunk_position="last")

            # First snapshot
            yield StateSnapshot(
                values={},
                next=(),
                config={"configurable": {"checkpoint_id": "chk-1"}},
                metadata={},
                created_at="2024-01-01T00:00:00Z",
                parent_config=None,
                tasks=(),
                interrupts=(),
            )

            # Second snapshot
            yield StateSnapshot(
                values={},
                next=(),
                config={"configurable": {"checkpoint_id": "chk-2"}},
                metadata={},
                created_at="2024-01-01T00:00:01Z",
                parent_config={"configurable": {"checkpoint_id": "chk-1"}},
                tasks=(),
                interrupts=(),
            )

        converter = StreamToVercelConverter()
        events = []
        async for event in converter.stream(mock_stream()):
            events.append(event)

        event_types = [e["type"] for e in events]

        # Count checkpoint events
        checkpoint_events = [e for e in events if e["type"] == "data-checkpoint"]
        assert len(checkpoint_events) == 2

        # Verify checkpoint IDs
        assert checkpoint_events[0]["checkpoint"]["id"] == "chk-1"
        assert checkpoint_events[0]["checkpoint"]["parent"] is None
        assert checkpoint_events[1]["checkpoint"]["id"] == "chk-2"
        assert checkpoint_events[1]["checkpoint"]["parent"] == "chk-1"

        # Verify step lifecycle (one start, one finish)
        start_steps = [t for t in event_types if t == "start-step"]
        finish_steps = [t for t in event_types if t == "finish-step"]
        assert len(start_steps) == 1
        assert len(finish_steps) == 1
