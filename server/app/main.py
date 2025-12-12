"""
FastAPI application entry point.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import PromptRequest, AgentResponse, ErrorResponse, HealthResponse
from .agent import agent
from .config import config

# Initialize FastAPI app
app = FastAPI(
    title="Monorepo LLM Agent API",
    description="Minimal LLM agent using langchain/langgraph with Aliyun Dashscope",
    version="1.0.0"
)

# Configure CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/agent", response_model=AgentResponse, responses={
    503: {"model": ErrorResponse, "description": "LLM service unavailable"}
})
async def process_agent_request(request: PromptRequest) -> AgentResponse:
    """
    Process a prompt with the LLM agent.
    
    - **prompt**: User's text input (1-10000 characters)
    
    Returns the agent's generated response or fallback message.
    """
    try:
        answer = await agent.process_prompt(request.prompt)
        return AgentResponse(answer=answer)
    except Exception as e:
        # Return HTTP 503 for LLM failures
        raise HTTPException(
            status_code=503,
            detail={
                "error": "LLM service temporarily unavailable. Please try again later.",
                "code": "LLM_UNAVAILABLE"
            }
        )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns service status and LLM configuration state.
    """
    return HealthResponse(
        status="healthy",
        llm_configured=config.is_llm_configured()
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Monorepo LLM Agent API",
        "version": "1.0.0",
        "endpoints": {
            "agent": "POST /agent",
            "health": "GET /health"
        }
    }

