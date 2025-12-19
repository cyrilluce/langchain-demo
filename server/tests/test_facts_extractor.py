"""
Unit tests for FactsExtractorAgent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.facts_extractor import FactsExtractorAgent


class TestFactsExtractorAgent:
    """Test suite for FactsExtractorAgent."""

    @pytest.fixture
    def mock_config(self):
        """Mock config with API key."""
        with patch("app.agents.facts_extractor.config") as mock_cfg:
            mock_cfg.DASHSCOPE_API_KEY = "test-api-key"
            mock_cfg.DASHSCOPE_MODEL = "qwen-turbo"
            yield mock_cfg

    @pytest.fixture
    def agent(self, mock_config):
        """Create agent instance with mocked LLM."""
        with patch("app.agents.facts_extractor.ChatTongyi"):
            with patch("app.agents.facts_extractor.create_agent") as mock_create:
                mock_agent = MagicMock()
                mock_create.return_value = mock_agent
                agent = FactsExtractorAgent()
                agent.agent = mock_agent
                yield agent

    @pytest.mark.asyncio
    async def test_extract_facts_basic(self, agent):
        """Test basic fact extraction with valid response."""
        # Arrange
        content = "2024年全国机场信息汇总如下...机场名 | 客流 ... 武汉天河机场 | 3000万"
        topic = "湖北机场吞吐量"

        mock_response = {
            "messages": [
                MagicMock(
                    content='[{"fact": "武汉天河机场2024年的客流吞吐量为3000万", "references": [{"offset": 31, "length": 14}]}]'
                )
            ]
        }
        agent.agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        facts = await agent.extract_facts(content, topic)

        # Assert
        assert len(facts) == 1
        assert facts[0].fact == "武汉天河机场2024年的客流吞吐量为3000万"
        assert len(facts[0].references) == 1
        assert facts[0].references[0].offset == 31
        assert facts[0].references[0].length == 14

    @pytest.mark.asyncio
    async def test_extract_facts_multiple_facts(self, agent):
        """Test extraction of multiple facts."""
        # Arrange
        content = "武汉天河机场客流3000万。湖北花湖机场客流500万。"
        topic = "湖北机场"

        mock_response = {
            "messages": [
                MagicMock(
                    content='[{"fact": "武汉天河机场客流3000万", "references": [{"offset": 0, "length": 12}]}, {"fact": "湖北花湖机场客流500万", "references": [{"offset": 13, "length": 12}]}]'
                )
            ]
        }
        agent.agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        facts = await agent.extract_facts(content, topic)

        # Assert
        assert len(facts) == 2
        assert facts[0].fact == "武汉天河机场客流3000万"
        assert facts[1].fact == "湖北花湖机场客流500万"

    @pytest.mark.asyncio
    async def test_extract_facts_empty_content(self, agent):
        """Test with empty content."""
        # Act
        facts = await agent.extract_facts("", "topic")

        # Assert
        assert len(facts) == 0
        agent.agent.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_facts_empty_topic(self, agent):
        """Test with empty topic."""
        # Act
        facts = await agent.extract_facts("some content", "")

        # Assert
        assert len(facts) == 0
        agent.agent.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_facts_invalid_json_response(self, agent):
        """Test handling of invalid JSON response."""
        # Arrange
        content = "test content"
        topic = "test topic"

        mock_response = {"messages": [MagicMock(content="This is not JSON")]}
        agent.agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        facts = await agent.extract_facts(content, topic)

        # Assert
        assert len(facts) == 0

    @pytest.mark.asyncio
    async def test_extract_facts_reference_validation(self, agent):
        """Test reference validation (offset/length bounds checking)."""
        # Arrange
        content = "短文本"
        topic = "test"

        # Invalid reference: offset + length exceeds content length
        mock_response = {
            "messages": [
                MagicMock(
                    content='[{"fact": "test fact", "references": [{"offset": 0, "length": 100}]}]'
                )
            ]
        }
        agent.agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        facts = await agent.extract_facts(content, topic)

        # Assert - should fix the length
        assert len(facts) == 1
        assert facts[0].references[0].length == len(content)

    @pytest.mark.asyncio
    async def test_extract_facts_llm_error(self, agent):
        """Test error handling when LLM fails."""
        # Arrange
        content = "test content"
        topic = "test topic"

        agent.agent.ainvoke = AsyncMock(side_effect=Exception("LLM connection failed"))

        # Act & Assert
        with pytest.raises(Exception, match="LLM service error"):
            await agent.extract_facts(content, topic)

    @pytest.mark.asyncio
    async def test_extract_facts_with_multiple_references(self, agent):
        """Test fact with multiple references."""
        # Arrange
        content = "武汉机场在湖北。天河机场也在武汉。"
        topic = "武汉机场"

        # Note: Chinese characters are correctly indexed
        # "武汉机场在湖北。天河机场也在武汉。"
        # 武(0)汉(1)机(2)场(3)在(4)湖(5)北(6)。(7)天(8)河(9)机(10)场(11)也(12)在(13)武(14)汉(15)。(16)
        mock_response = {
            "messages": [
                MagicMock(
                    content='[{"fact": "武汉有机场", "references": [{"offset": 0, "length": 4}, {"offset": 14, "length": 2}]}]'
                )
            ]
        }
        agent.agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        facts = await agent.extract_facts(content, topic)

        # Assert
        assert len(facts) == 1
        assert len(facts[0].references) == 2
        assert facts[0].references[0].offset == 0
        assert facts[0].references[0].length == 4
        assert facts[0].references[1].offset == 14
        assert facts[0].references[1].length == 2

    def test_initialization_without_api_key(self):
        """Test agent initialization fails without API key."""
        # Arrange
        with patch("app.agents.facts_extractor.config") as mock_cfg:
            mock_cfg.DASHSCOPE_API_KEY = None

            # Act & Assert
            with pytest.raises(ValueError, match="DASHSCOPE_API_KEY is required"):
                FactsExtractorAgent()

    @pytest.mark.asyncio
    async def test_parse_llm_response_with_extra_text(self, agent):
        """Test parsing LLM response that includes extra text around JSON."""
        # Arrange
        content = "test content"
        topic = "test"

        mock_response = {
            "messages": [
                MagicMock(
                    content='Here are the facts:\n[{"fact": "test", "references": [{"offset": 0, "length": 4}]}]\nHope this helps!'
                )
            ]
        }
        agent.agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        facts = await agent.extract_facts(content, topic)

        # Assert
        assert len(facts) == 1
        assert facts[0].fact == "test"

    @pytest.mark.asyncio
    async def test_extract_facts_negative_offset(self, agent):
        """Test handling of invalid negative offset."""
        # Arrange
        content = "test content"
        topic = "test"

        mock_response = {
            "messages": [
                MagicMock(
                    content='[{"fact": "test", "references": [{"offset": -1, "length": 4}]}]'
                )
            ]
        }
        agent.agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        facts = await agent.extract_facts(content, topic)

        # Assert - invalid reference should be filtered out
        assert len(facts) == 1
        assert len(facts[0].references) == 0
