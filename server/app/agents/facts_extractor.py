"""
Facts Extractor Agent - Extract atomic facts related to a specific topic from text.
"""

from typing import List
from langchain_community.chat_models import ChatTongyi
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from pydantic import SecretStr
from dashscope import get_tokenizer
import json
import logging
from ..config import config
from ..models import ExtractedFact, FactReference

logger = logging.getLogger(__name__)


class FactsExtractorAgent:
    """Agent for extracting topic-related atomic facts from text using LangChain."""

    def __init__(self) -> None:
        """Initialize the facts extractor agent."""
        api_key = config.DASHSCOPE_API_KEY
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY is required for FactsExtractorAgent")

        model = config.DASHSCOPE_MODEL
        self.llm = ChatTongyi(
            model=model,
            api_key=SecretStr(api_key),
            streaming=False,
            # temperature=0.0000001,
        )

        self.tokenizer = get_tokenizer(model)

        # Create agent with specific system prompt for fact extraction
        system_prompt = self._get_system_prompt()
        self.agent = create_agent(
            model=self.llm,
            tools=[],  # No tools needed for this task
            system_prompt=system_prompt,
        )
        print(system_prompt)


    def _get_system_prompt(self) -> str:
        """Get the system prompt for fact extraction."""
        return """你是一个精确的事实提取助手。
你的任务是：
1. 从用户提供的[信源内容]中提取与[主题]相关的原子事实
2. 每个事实应是完备且具体的
3. 包括每个事实在[信源内容]中出现的精确引用位置（相对于[信源内容]起始的字符偏移和长度）
4. 以 JSON 格式返回结果

输出格式：
[
    {
        "fact": "提取的事实文本",
        "references": [
            {"offset": 123, "chars": 4, "content": "原始文本"}
        ]
    }
]

规则：
- 仅提取与[主题]直接相关的事实
- 每个事实应是原子性的（单一信息）
- offset 为引用的文本在[信源内容]中字符位置（从 0 开始计数）
- chars 为引用的字符数，中文算1个字符
- 如果一个事实来自多个部分，需包含所有引用
- 仅返回有效的 JSON，不要包含额外文本"""

    def _parse_llm_response(
        self, response: str, content: str, tokens: list[int]
    ) -> List[ExtractedFact]:
        """
        Parse LLM response and validate/fix references.

        Args:
            response: Raw LLM response
            content: Original content for validation

        Returns:
            List of validated ExtractedFact objects
        """
        try:
            # Extract JSON from response (in case LLM adds extra text)
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1
            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON array found in LLM response")
                return []

            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)

            if not isinstance(data, list):
                logger.warning("LLM response is not a list")
                return []

            facts = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                fact_text = item.get("fact", "").strip()
                if not fact_text:
                    continue

                # Validate and fix references
                references = []
                for ref in item.get("references", []):
                    if isinstance(ref, dict):
                        offset = ref.get("offset", 0)
                        length = ref.get("chars", 0)

                        # Validate reference bounds
                        if 0 <= offset < len(content) and length > 0:
                            # Ensure offset + length doesn't exceed
                            if offset + length > len(content):
                                length = len(content) - offset
                            references.append(
                                FactReference(
                                    offset=offset,
                                    length=length,
                                    content=ref.get('content') #content[offset : offset + length],
                                )
                            )

                facts.append(ExtractedFact(fact=fact_text, references=references))

            return facts

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return []

    async def extract_facts(self, content: str, topic: str) -> List[ExtractedFact]:
        """
        Extract topic-related atomic facts from the given content.

        Args:
            content: The source text to extract facts from
            topic: The topic to focus on

        Returns:
            List of extracted facts with references

        Raises:
            Exception: If LLM service fails
        """
        try:
            if not content.strip():
                return []

            if not topic.strip():
                return []

            tokens = self.tokenizer.encode(content)
            # Construct the prompt
            prompt = f"""[主题]:
{topic}

[信源内容](共 {len(content)} 字符):
{content}"""

            print(prompt)
            # Invoke the agent
            response = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=prompt)]}
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

            # Parse and validate the response
            facts = self._parse_llm_response(response_text, content, tokens)

            return facts

        except Exception as e:
            logger.error(f"Facts extraction failed: {e}")
            raise Exception(f"LLM service error: {str(e)}")
