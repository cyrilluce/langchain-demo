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

    content = "# 2024年四川省交通运输行业发展统计公报\n年末颁证民用航空机场17个。全年旅客吞吐量达到100万人次以上的机场6个，较上年末减少1个，按旅客吞吐量从高到低分别是：成都天府国际机场、成都双流国际机场、绵阳南郊机场、泸州云龙机场、宜宾五粮液机场、达州金垭机场。全年货邮吞吐量达到1000吨以上的机场8个，较上年末持平，按货邮吞吐量从高到低分别是：成都双流国际机场、成都天府国际机场、宜宾五粮液机场、绵阳南郊机场、泸州云龙机场、南充高坪机场、达州金垭机场、西昌青山机场。"

    agent = create_agent(
        model,
    )

    response = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=f"""请输出[信源原文]的字符/char个数，并写明计算过程
[信源原文]:
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
