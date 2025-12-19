# 测试 LLM 是否能原生感知 token，结论是不行
import asyncio
from langchain_community.chat_models import ChatTongyi
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr
from dashscope import get_tokenizer
from dashscope.tokenizers import Tokenizer
from .config import config


def get_model() -> tuple[BaseChatModel, Tokenizer]:
    api_key = config.DASHSCOPE_API_KEY
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY is required for FactsExtractorAgent")

    model = config.DASHSCOPE_MODEL
    llm = ChatTongyi(
        model=model,
        api_key=SecretStr(api_key),
        streaming=False,
        top_p=0.00000001
        # temperature=0.0000001,
    )

    tokenizer = get_tokenizer(model)

    return (llm, tokenizer)


async def main():
    (model, tokenizer) = get_model()

    content = "测试LLM是否能理解token的概念"
    tokens = tokenizer.encode(content)
    print(f'({len(tokens)}) - {content}')

    agent = create_agent(
        model,
    )

    response = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=f"""[token]定义为你的模型原生的分词/Tokenization算法的 1 个元素。
请输出以下文本总共的[token]个数:
{content}"""
                )
            ]
        }
    )

    # Extract the text response
    if isinstance(response, dict) and "messages" in response:
        messages = response["messages"]
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                response_text = last_message.content
            else:
                response_text = str(last_message)
        else:
            response_text = ""
    else:
        response_text = str(response)

    print(response_text)


if __name__ == "__main__":
    asyncio.run(main())
