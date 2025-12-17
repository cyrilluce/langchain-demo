from typing import AsyncIterator
from app.vercel_ui_message_stream.tool_converter import ToolStreamToVercelConverter
from langchain_core.messages import BaseMessage
from .utils import runTestWithProcessor


class TestToolConverter:
    """
    ToolStreamToVercelConverter 单元测试

    测试 LangChain ToolMessage 流到 Vercel AI SDK UIMessageChunk 流的转换
    验证工具执行结果的正确转换，包括：
    - step-start/step-end 事件
    - tool-output-available 事件
    - toolCallId 的正确映射
    - output 内容的正确提取
    """

    async def testToolMessages1(self) -> None:
        """
        测试单个 ToolMessage 的转换

        验证：
        - 正确生成 step-start 事件
        - 正确生成 tool-output-available 事件
        - 正确提取 toolCallId 和 output
        - 正确生成 step-end 事件
        """
        converter = ToolStreamToVercelConverter()

        def processor(stream: AsyncIterator[BaseMessage]) -> AsyncIterator[dict]:
            return converter.stream(stream)

        await runTestWithProcessor(
            "snapshots/tools.json",
            "snapshots/tools-converted.json",
            processor
        )

    async def testToolMessagesMultiple(self) -> None:
        """
        测试多个 ToolMessage 的转换

        验证：
        - 多个工具调用的正确处理
        - 每个工具调用独立的 step-start/step-end
        - 正确的 ID 跟踪和步骤分隔
        """
        converter = ToolStreamToVercelConverter()

        def processor(stream: AsyncIterator[BaseMessage]) -> AsyncIterator[dict]:
            return converter.stream(stream)

        await runTestWithProcessor(
            "snapshots/tools-multiple.json",
            "snapshots/tools-multiple-converted.json",
            processor
        )

    async def testToolMessagesWithListContent(self) -> None:
        """
        测试包含列表内容的 ToolMessage

        验证：
        - 列表格式内容的正确处理
        - 字典和字符串内容项的正确提取
        - 嵌套数据结构的正确转换
        """
        converter = ToolStreamToVercelConverter()

        def processor(stream: AsyncIterator[BaseMessage]) -> AsyncIterator[dict]:
            return converter.stream(stream)

        await runTestWithProcessor(
            "snapshots/tools-list-content.json",
            "snapshots/tools-list-content-converted.json",
            processor
        )

    async def testToolMessagesEmpty(self) -> None:
        """
        测试空工具输出

        验证：
        - 空内容的正确处理
        - 基本事件流的完整性
        """
        converter = ToolStreamToVercelConverter()

        def processor(stream: AsyncIterator[BaseMessage]) -> AsyncIterator[dict]:
            return converter.stream(stream)

        await runTestWithProcessor(
            "snapshots/tools-empty.json",
            "snapshots/tools-empty-converted.json",
            processor
        )
