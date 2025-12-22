"""
Configuration management for the LLM agent.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # Aliyun Dashscope configuration
    DASHSCOPE_API_KEY: Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    DASHSCOPE_MODEL: str = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")

    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5001"))

    @classmethod
    def is_llm_configured(cls) -> bool:
        """Check if LLM credentials are configured."""
        return cls.DASHSCOPE_API_KEY is not None and len(cls.DASHSCOPE_API_KEY) > 0


config = Config()
