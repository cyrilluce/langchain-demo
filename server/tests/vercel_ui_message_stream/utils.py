import json
from typing import AsyncIterator, Callable, cast
from langchain_core.messages import messages_from_dict, BaseMessage
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

# 根据 snapshot 验证
async def testWithProcessor(
    input: str,
    output: str,
    processor: Callable[[AsyncIterator[BaseMessage]], AsyncIterator[dict]],
) -> None:
    # 根据 snapshot 恢复出 AIMessageChunk、ToolMessageChunk
    data = readJson(input)
    expects = readJson(output)

    messages = messages_from_dict(data)

    async def stream() -> AsyncIterator[BaseMessage]:
        for message in messages:
            yield message

    async for chunk in processor(stream()):
        expectChunk = expects.pop()
        assert chunk == expectChunk, f"Chunk mismatch: {chunk} != {expectChunk}"

    assert len(expects) == 0, "消息都处理了"



def readJson(path: str) -> list[dict]:
    fullPath = os.path.join(current_dir, path)
    with open(fullPath, "r") as file:
        return cast(list[dict], json.load(file))

