"""
LLM agent implementation using langchain with Aliyun Dashscope.
"""

from typing import Optional
from langchain_community.llms import Tongyi
from .config import config


class LLMAgent:
    """LLM agent with Aliyun Dashscope integration and fallback support."""
    
    def __init__(self):
        """Initialize the agent with LLM or fallback mode."""
        self.llm: Optional[Tongyi] = None
        self.fallback_mode = not config.is_llm_configured()
        
        if not self.fallback_mode:
            try:
                self.llm = Tongyi(
                    model_name=config.DASHSCOPE_MODEL,
                    dashscope_api_key=config.DASHSCOPE_API_KEY,
                )
            except Exception as e:
                print(f"Failed to initialize LLM: {e}")
                self.fallback_mode = True
    
    async def process_prompt(self, prompt: str) -> str:
        """
        Process a prompt and return the agent's response.
        
        Args:
            prompt: User's input text
            
        Returns:
            Generated response from LLM or fallback message
            
        Raises:
            Exception: If LLM processing fails (non-fallback mode)
        """
        if self.fallback_mode:
            return self._fallback_response(prompt)
        
        try:
            # Use langchain to process the prompt
            response = await self.llm.ainvoke(prompt)
            return response
        except Exception as e:
            # Re-raise LLM errors to be handled by the API layer
            raise Exception(f"LLM service error: {str(e)}")
    
    def _fallback_response(self, prompt: str) -> str:
        """Generate a fallback response when LLM is not configured."""
        return (
            f"[Fallback Mode] Echo: {prompt[:100]}... "
            f"(LLM not configured. Set DASHSCOPE_API_KEY to enable AI responses.)"
        )
    
    def is_ready(self) -> bool:
        """Check if the agent is ready to process requests."""
        return True  # Agent is always ready (fallback mode or LLM mode)


# Global agent instance
agent = LLMAgent()
