from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI(title="LLM Agent Demo")


class PromptRequest(BaseModel):
    prompt: str


@app.post("/agent")
async def agent_endpoint(req: PromptRequest) -> Dict[str, str]:
    """Simple agent endpoint.

    Tries to use langchain/langgraph if available; otherwise returns a deterministic fallback.
    """
    prompt = req.prompt
    # Guard imports so server remains runnable without LLM deps
    try:
        # Example placeholder for real langchain/langgraph usage
        from langchain import OpenAI  # noqa: F401
        from langgraph import Flow  # noqa: F401
        # TODO: implement agent orchestration using langchain/langgraph here
        answer = f"(demo) processed prompt: {prompt}"
    except Exception:
        # Fallback deterministic behavior
        answer = f"fallback-answer: {prompt[::-1]}"

    return {"answer": answer}
