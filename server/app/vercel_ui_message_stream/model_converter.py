from typing import Any, AsyncIterator

from langchain_core.messages import AIMessageChunk, BaseMessage


class ModelStreamToVercelConverter:
    """
    将 LangChain AIMessageChunk 流转换为 Vercel AI SDK UIMessageChunk 流

    负责处理模型输出的流式转换，包括：
    - text: 文本内容流
    - reasoning: 推理内容流
    - tool_call_chunks: 工具调用参数流
    """

    def __init__(self) -> None:
        self.current_id: str = ''
        self.text_started: bool = False
        self.tool_call_started: dict[str, bool] = {}
        self.tool_args_buffer: dict[str, str] = {}
        self.tool_names: dict[str, str] = {}  # 保存工具名称

    async def stream(
        self, stream: AsyncIterator[BaseMessage]
    ) -> AsyncIterator[dict[str, Any]]:
        """
        转换 LangChain AIMessageChunk 流为 Vercel AI SDK UIMessageChunk 流

        Args:
            stream: LangChain BaseMessage 异步迭代器，期望包含 AIMessageChunk

        Yields:
            dict: Vercel AI SDK UIMessageChunk 格式的事件字典
        """
        async for msg in stream:
            # 处理消息 ID 变化（新步骤开始）
            if msg.id and self.current_id != msg.id:
                # 结束上一个步骤
                if self.current_id:
                    yield {"type": "finish-step"}

                # 开始新步骤
                yield {"type": "start-step"}
                self.current_id = msg.id
                self.text_started = False
                self.tool_call_started = {}
                self.tool_args_buffer = {}
                self.tool_names = {}

            if isinstance(msg, AIMessageChunk):
                # 处理 reasoning 内容（如果存在）
                reasoning = getattr(msg, 'reasoning', None)
                if reasoning:
                    # 这里可以添加 reasoning-start/delta/end 逻辑
                    pass

                # 处理文本内容
                if msg.content and isinstance(msg.content, str):
                    if not self.text_started:
                        yield {"type": "text-start", "id": msg.id}
                        self.text_started = True
                    yield {
                        "type": "text-delta",
                        "id": msg.id,
                        "delta": msg.content,
                    }

                # 处理工具调用 chunks
                if hasattr(msg, 'tool_call_chunks') and msg.tool_call_chunks:
                    for chunk in msg.tool_call_chunks:
                        tool_call_id = chunk.get('id')
                        if not tool_call_id:
                            continue

                        # 获取工具调用的属性
                        tool_name = chunk.get('name', '')
                        args_chunk = chunk.get('args', '')

                        # 开始工具调用（首次遇到该 tool_call_id）
                        if tool_call_id not in self.tool_call_started:
                            self.tool_call_started[tool_call_id] = True
                            self.tool_args_buffer[tool_call_id] = ''
                            if tool_name:
                                self.tool_names[tool_call_id] = tool_name
                                yield {
                                    "type": "tool-input-start",
                                    "toolCallId": tool_call_id,
                                    "toolName": tool_name,
                                }
                        else:
                            # 保存工具名称（如果还没有保存）
                            if tool_name and tool_call_id not in self.tool_names:
                                self.tool_names[tool_call_id] = tool_name

                        # 累积参数并发送 delta
                        if args_chunk:
                            self.tool_args_buffer[tool_call_id] += args_chunk
                            yield {
                                "type": "tool-input-delta",
                                "toolCallId": tool_call_id,
                                "inputTextDelta": args_chunk,
                            }

                # 检查是否是最后一个 chunk（chunk_position == 'last'）
                if (
                    hasattr(msg, 'chunk_position')
                    and msg.chunk_position == 'last'
                ):
                    # 发送所有累积的工具调用参数
                    for tool_call_id, args_buffer in self.tool_args_buffer.items():
                        if args_buffer and tool_call_id in self.tool_call_started:
                            # 获取保存的工具名称
                            tool_name = self.tool_names.get(tool_call_id, '')

                            yield {
                                "type": "tool-input-available",
                                "toolCallId": tool_call_id,
                                "toolName": tool_name,
                                "input": args_buffer,
                            }
            else:
                print(
                    f"[ModelStreamToVercelConverter]: 不支持的消息类型 {str(type(msg))}"
                )

        # 流结束，清理状态
        if self.current_id:
            yield {"type": "finish-step"}
