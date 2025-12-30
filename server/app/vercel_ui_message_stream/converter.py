"""
完整的 LangChain 到 Vercel AI SDK 流转换器 (V2)

简化的实现，直接管理 step 生命周期
"""

from typing import Any, AsyncIterator, Callable, cast

from langchain_core.messages import AIMessageChunk, BaseMessage, ToolMessage
from langgraph.types import StateSnapshot

from .model_converter import ModelStreamToVercelConverter
from .tool_converter import ToolStreamToVercelConverter


class StreamToVercelConverter:
    """
    完整的流转换器, 直接遍历消息流并管理 step 生命周期

    Step 生命周期规则:
    - 每个新的 AIMessage (通过 ID 识别) 开始一个新的 step
    - 在开始新 step 之前, 先结束上一个 step
    - ToolMessage 属于当前 step, 不触发 step 变化
    - 流结束时关闭最后一个 step
    """

    def __init__(
        self,
        checkpoint_converter: Callable[[StateSnapshot], dict[str, Any]] | None = None,
    ) -> None:
        self.current_ai_id: str | None = None
        self.step_started: bool = False
        self.model_converter = ModelStreamToVercelConverter()
        self.tool_converter = ToolStreamToVercelConverter()
        self.checkpoint_converter = (
            checkpoint_converter or self._default_checkpoint_converter
        )

    @staticmethod
    def _default_checkpoint_converter(snapshot: StateSnapshot) -> dict[str, Any]:
        """
        默认的 StateSnapshot 转换器

        Args:
            snapshot: LangGraph 的状态快照

        Returns:
            dict: Vercel AI SDK data-checkpoint 格式的事件
        """
        checkpoint_id = "unknown"
        parent_id = None

        if snapshot.config:
            configurable = snapshot.config.get("configurable", {})
            checkpoint_id = configurable.get("checkpoint_id", "unknown")

        if snapshot.parent_config:
            parent_configurable = snapshot.parent_config.get("configurable", {})
            parent_id = parent_configurable.get("checkpoint_id")

        return {
            "type": "data-checkpoint",
            "transient": True,
            "checkpoint": {"id": checkpoint_id, "parent": parent_id},
        }

    async def stream(
        self, stream: AsyncIterator[BaseMessage | StateSnapshot]
    ) -> AsyncIterator[dict[str, Any]]:
        """
        转换完整的 LangChain 消息流为 Vercel AI SDK 格式

        Args:
            stream: LangChain BaseMessage 或 StateSnapshot 异步迭代器

        Yields:
            dict: Vercel AI SDK UIMessageChunk 格式的事件字典
        """
        async for msg in stream:
            # 处理 StateSnapshot
            if isinstance(msg, StateSnapshot):
                yield self.checkpoint_converter(msg)

            # 处理 AIMessageChunk
            elif isinstance(msg, AIMessageChunk):
                # 检查是否是新的 AI 消息
                if msg.id and msg.id != self.current_ai_id:
                    # 结束上一个 step (如果存在)
                    if self.step_started:
                        yield {"type": "finish-step"}

                    # 开始新的 step
                    yield {"type": "start-step"}
                    self.current_ai_id = msg.id
                    self.step_started = True

                # 处理 AI 消息内容
                async def single_msg_stream() -> AsyncIterator[BaseMessage]:
                    yield cast(BaseMessage, msg)

                async for event in self.model_converter.stream(single_msg_stream()):
                    # 过滤掉 model_converter 可能发出的 step 事件
                    if event.get("type") not in ["start-step", "finish-step"]:
                        yield event

            # 处理 ToolMessage
            elif isinstance(msg, ToolMessage):
                # Tool 消息属于当前 step, 直接输出内容
                async def single_tool_stream() -> AsyncIterator[BaseMessage]:
                    yield cast(BaseMessage, msg)

                async for event in self.tool_converter.stream(single_tool_stream()):
                    # 过滤掉 tool_converter 可能发出的 step 事件
                    if event.get("type") not in ["start-step", "finish-step"]:
                        yield event

        # 流结束, 关闭最后一个 step
        if self.step_started:
            yield {"type": "finish-step"}
