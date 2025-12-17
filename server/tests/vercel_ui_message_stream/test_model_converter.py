from typing import AsyncIterator
from app.vercel_ui_message_stream.model_converter import ModelStreamToVercelConverter
from langchain_core.messages import BaseMessage
from .utils import testWithProcessor

class TestModelConverter:
    async def testMessages1(self) -> None:
        converter = ModelStreamToVercelConverter()

        def processor(stream: AsyncIterator[BaseMessage]) -> AsyncIterator[dict]:
            return converter.stream(stream)

        await testWithProcessor(
            "snapshots/model.json", "snapshots/model-converted.json", processor
        )
