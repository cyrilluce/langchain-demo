from typing import AsyncIterator

from langchain_core.messages import BaseMessage

from app.vercel_ui_message_stream.converter import StreamToVercelConverter

from .utils import runTestWithProcessor


class TestStreamConverter:
    """
    StreamToVercelConverter 单元测试

    测试完整的 LangChain 消息流到 Vercel AI SDK UIMessageChunk 流的转换
    验证：
    - 消息类型路由（AIMessageChunk vs ToolMessage）
    - Model 和 Tool 转换器的协调
    - 完整 agent 执行流的正确转换
    """

    async def testFullStream(self) -> None:
        """
        测试完整的 agent 执行流

        验证：
        - 工具调用阶段的正确转换
        - 工具输出阶段的正确转换
        - 文本响应阶段的正确转换
        - 多个步骤之间的正确分隔
        """
        converter = StreamToVercelConverter()

        def processor(stream: AsyncIterator[BaseMessage]) -> AsyncIterator[dict]:
            return converter.stream(stream)

        await runTestWithProcessor(
            "snapshots/full.json",
            "snapshots/full-converted.json",
            processor
        )
