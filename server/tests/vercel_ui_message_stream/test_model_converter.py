from typing import AsyncIterator

from langchain_core.messages import BaseMessage

from app.vercel_ui_message_stream.model_converter import ModelStreamToVercelConverter

from .utils import runTestWithProcessor


class TestModelConverter:
    """
    ModelStreamToVercelConverter 单元测试

    测试 LangChain AIMessageChunk 流到 Vercel AI SDK UIMessageChunk 流的转换
    验证模型输出的正确转换，包括：
    - text-start/text-delta 事件
    - tool-input-start/tool-input-delta/tool-input-available 事件
    - start-step/finish-step 步骤管理
    """

    async def testMessages1(self) -> None:
        """
        测试完整的工具调用和文本响应流

        验证：
        - 工具调用参数的流式输出
        - 工具调用完成后的 available 事件
        - 文本内容的流式输出
        - 正确的步骤分隔
        """
        converter = ModelStreamToVercelConverter()

        def processor(stream: AsyncIterator[BaseMessage]) -> AsyncIterator[dict]:
            return converter.stream(stream)

        await runTestWithProcessor(
            "snapshots/model.json", "snapshots/model-converted.json", processor
        )

    async def testTextOnly(self) -> None:
        """
        测试纯文本响应流

        验证：
        - text-start 和 text-delta 事件
        - 无工具调用时的正确处理
        """
        converter = ModelStreamToVercelConverter()

        def processor(stream: AsyncIterator[BaseMessage]) -> AsyncIterator[dict]:
            return converter.stream(stream)

        await runTestWithProcessor(
            "snapshots/text-only.json",
            "snapshots/text-only-converted.json",
            processor
        )

    async def testMultipleToolCalls(self) -> None:
        """
        测试多个工具调用

        验证：
        - 多个工具同时调用的处理
        - 每个工具独立的参数累积
        - 正确的 toolCallId 映射
        """
        converter = ModelStreamToVercelConverter()

        def processor(stream: AsyncIterator[BaseMessage]) -> AsyncIterator[dict]:
            return converter.stream(stream)

        await runTestWithProcessor(
            "snapshots/multiple-tools.json",
            "snapshots/multiple-tools-converted.json",
            processor
        )
