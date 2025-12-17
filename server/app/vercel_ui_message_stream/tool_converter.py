from langchain_core.messages import BaseMessage, ToolMessage
from typing import AsyncIterator, Any


class ToolStreamToVercelConverter:
    """
    将 LangChain ToolMessage 流转换为 Vercel AI SDK UIMessageChunk 流

    负责处理工具执行结果的流式输出，输出格式遵循 Vercel AI SDK 的流协议：
    - step-start: 开始新的工具执行步骤
    - tool-output-available: 工具执行结果可用
    - step-end: 结束工具执行步骤
    """

    async def stream(
        self, stream: AsyncIterator[BaseMessage]
    ) -> AsyncIterator[dict[str, Any]]:
        """
        转换 LangChain ToolMessage 流为 Vercel AI SDK UIMessageChunk 流

        Args:
            stream: LangChain BaseMessage 异步迭代器，期望包含 ToolMessage

        Yields:
            dict: Vercel AI SDK UIMessageChunk 格式的事件字典

        流程:
        1. 检测新消息，发送 step-start
        2. 解析 ToolMessage 内容，发送 tool-output-available
        3. 消息结束时发送 step-end
        """
        current_id: str = ''

        async for msg in stream:
            # 跟踪消息 ID 变化，用于判断是否开始新的步骤
            if msg.id and current_id != msg.id:
                # 如果有旧的 ID，先结束上一个步骤
                if current_id:
                    yield {"type": "step-end"}
                # 开始新的步骤
                yield {"type": "step-start"}
                current_id = msg.id

            # 只处理 ToolMessage
            if isinstance(msg, ToolMessage):
                # ToolMessage.content 可能是字符串或者包含字典的列表
                # 根据 LangChain 文档，content 通常是字符串
                if isinstance(msg.content, str):
                    # 简单字符串内容
                    yield {
                        "type": "tool-output-available",
                        "toolCallId": msg.tool_call_id,
                        "output": msg.content,
                    }
                elif isinstance(msg.content, list):
                    # 列表格式内容（可能包含多个工具输出）
                    for content_item in msg.content:
                        if isinstance(content_item, dict):
                            # 字典格式的内容 - 保留完整字典结构
                            tool_call_id = (
                                content_item.get('tool_call_id')
                                or msg.tool_call_id
                            )
                            yield {
                                "type": "tool-output-available",
                                "toolCallId": tool_call_id,
                                "output": content_item,
                            }
                        elif isinstance(content_item, str):
                            # 字符串格式的内容项
                            yield {
                                "type": "tool-output-available",
                                "toolCallId": msg.tool_call_id,
                                "output": content_item,
                            }
                else:
                    # 其他类型直接输出
                    yield {
                        "type": "tool-output-available",
                        "toolCallId": msg.tool_call_id,
                        "output": msg.content,
                    }
            else:
                # 非 ToolMessage 类型，记录警告
                print(
                    f"[ToolStreamToVercelConverter]: 不支持的消息类型 {str(type(msg))}"
                )

        # 流结束，如果还有未结束的步骤，发送 step-end
        if current_id:
            yield {"type": "step-end"}
