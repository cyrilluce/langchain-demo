from langchain.agents import create_agent
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import AIMessageChunk
from pydantic import SecretStr
from .config import config
import json
from typing import cast


def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"


model = ChatTongyi(
    model=config.DASHSCOPE_MODEL,
    api_key=SecretStr(config.DASHSCOPE_API_KEY or ""),
)
agent = create_agent(
    model=model,
    tools=[get_weather],
)
for token, metadata in agent.stream(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    stream_mode="messages",
):
    token = cast(AIMessageChunk, token)  # 使用 cast 显式告诉类型检查器 token 的实际类型
    output = {
        "metadata": metadata,
        "token": token.model_dump(),
        "content": token.content_blocks,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
