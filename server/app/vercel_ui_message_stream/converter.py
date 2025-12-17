"""
完整的 LangChain 到 Vercel AI SDK 流转换器

将 LangChain agent 的 messages 流解析，根据消息类型分配到不同的转换器处理
使用 asyncio.Queue 实现真正的实时流处理，同时保证输出顺序
"""

import asyncio
from typing import Any, AsyncIterator

from langchain_core.messages import AIMessageChunk, BaseMessage, ToolMessage

from .model_converter import ModelStreamToVercelConverter
from .tool_converter import ToolStreamToVercelConverter


class StreamToVercelConverter:
    """
    完整的流转换器，协调 Model 和 Tool 转换器

    使用 asyncio.Queue 实现实时处理，但按消息类型分段保证顺序：
    - 同类型的连续消息立即流式处理
    - 类型切换时确保前一个转换器完成后再开始下一个
    """

    def __init__(self) -> None:
        pass

    async def stream(
        self, stream: AsyncIterator[BaseMessage]
    ) -> AsyncIterator[dict[str, Any]]:
        """
        转换完整的 LangChain 消息流为 Vercel AI SDK 格式

        Args:
            stream: LangChain BaseMessage 异步迭代器

        Yields:
            dict: Vercel AI SDK UIMessageChunk 格式的事件字典

        实时流程：
        1. 识别消息类型切换点
        2. 对每段同类型消息启动转换器任务
        3. 立即流式输出该段的转换结果
        4. 下一段开始前确保上一段完成
        """
        current_type: type[BaseMessage] | None = None
        current_queue: asyncio.Queue[BaseMessage | None] | None = None
        current_task: asyncio.Task | None = None
        output_queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

        async def process_segment(
            input_queue: asyncio.Queue[BaseMessage | None],
            converter_type: type[BaseMessage]
        ) -> None:
            """处理一段同类型的消息"""
            async def segment_stream() -> AsyncIterator[BaseMessage]:
                while True:
                    msg = await input_queue.get()
                    if msg is None:
                        break
                    yield msg

            try:
                if converter_type == AIMessageChunk:
                    converter = ModelStreamToVercelConverter()
                    async for event in converter.stream(segment_stream()):
                        await output_queue.put(event)
                elif converter_type == ToolMessage:
                    converter = ToolStreamToVercelConverter()
                    async for event in converter.stream(segment_stream()):
                        await output_queue.put(event)
            except Exception as e:
                print(f"[Converter Error]: {e}")
            finally:
                await output_queue.put(None)  # 标记该段完成

        async def consume_output() -> AsyncIterator[dict[str, Any]]:
            """持续消费输出队列并 yield 事件"""
            while True:
                event = await output_queue.get()
                if event is None:
                    break
                yield event

        # 主循环：处理输入流
        async for msg in stream:
            msg_type = type(msg)

            # 如果消息类型改变，完成当前段并启动新段
            if current_type != msg_type:
                # 完成当前段
                if current_queue is not None:
                    await current_queue.put(None)  # 发送结束信号
                    if current_task is not None:
                        # 输出当前段的所有事件
                        async for event in consume_output():
                            yield event
                        # 等待任务完成
                        await current_task

                # 启动新段
                current_type = msg_type
                current_queue = asyncio.Queue()
                current_task = asyncio.create_task(
                    process_segment(current_queue, current_type)
                )

            # 将消息放入当前队列（立即处理）
            if current_queue is not None:
                await current_queue.put(msg)

                # 立即尝试输出已处理的事件（非阻塞）
                while not output_queue.empty():
                    try:
                        event = output_queue.get_nowait()
                        if event is None:
                            # 如果收到结束标记，放回去等待后续处理
                            await output_queue.put(None)
                            break
                        yield event
                    except asyncio.QueueEmpty:
                        break

        # 完成最后一段
        if current_queue is not None:
            await current_queue.put(None)
            if current_task is not None:
                async for event in consume_output():
                    yield event
                await current_task
