from langchain_core.messages import BaseMessage, AIMessageChunk, ToolMessage
from typing import AsyncIterator, Any


class ModelStreamToVercelConverter:
    async def stream(
        self, stream: AsyncIterator[BaseMessage]
    ) -> AsyncIterator[dict[str, Any]]:
        id: str = ''
        async for msg in stream:
            if msg.id and id != msg.id:
                if id:
                    yield {"type": "step-end"}
                yield {"type": "step-start"}
                id = msg.id
            if isinstance(msg, AIMessageChunk):
                # TODO
                # text-start, text-delta, text-end
                # reasoning-start, reasoning-delta, reasoning-end
                # tool-input-start, tool-input-delta, tool-input-available
                yield {}
            elif isinstance(msg, ToolMessage):
                for content in msg.content:
                    if not isinstance(content, dict):
                        continue
                    # 似乎 vercel ai sdk 支持跳过 start + delta，直接输出 available
                    # tool-output-available
                    yield {
                        "type": "tool-output-available",
                        "toolCallId": content.get('tool_call_id'),
                        "output": content.get('content'),
                    }
            else:
                print(
                    f"[ModelStreamToVercelConverter]: 不支持的消息类型 {str(type(msg))}"
                )
        if id:
            yield {"type": "step-end"}
            id = ''
