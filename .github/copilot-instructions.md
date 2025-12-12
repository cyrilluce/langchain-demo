# Copilot Instructions for langchain-demo

## Architecture Overview

This is a **monorepo** with two independent services communicating via HTTP:

- **server/**: Python FastAPI backend with LangChain integration for LLM orchestration (Aliyun Dashscope/Qwen models)
- **ui/**: React TypeScript frontend using Vite + Bun runtime + Vercel AI SDK for streaming

**Critical architectural decision**: The server operates in **fallback mode** when `DASHSCOPE_API_KEY` is not configured, returning echo responses instead of failing. This enables development without LLM credentials.

## Project Structure & Key Files

```
server/
  app/
    main.py         # FastAPI routes: /agent (non-streaming), /agent/stream (streaming), /health
    agent.py        # LLMAgent class - uses LangChain chain (PromptTemplate | LLM)
    config.py       # Environment config with .env support via python-dotenv
    models.py       # Pydantic request/response schemas
  pyproject.toml    # Uses `uv` package manager (not pip)
  dev.sh           # Quick start script: ./dev.sh

ui/
  src/
    App.tsx         # Main component - uses @ai-sdk/react useChat hook
    services/api.ts # HTTP client for non-streaming endpoint
  package.json      # Bun as package manager and runtime

specs/001-monorepo-llm-agent/  # Complete feature specs, API contracts, implementation plans
```

## Critical Developer Workflows

### Server Development
```bash
cd server
# Uses 'uv' NOT pip - install via: curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv && source .venv/bin/activate
uv pip install -e .  # or: uv pip install -r requirements.txt

# Quick start
./dev.sh  # Runs uvicorn with hot-reload on :8000

# Optional: Set LLM credentials
export DASHSCOPE_API_KEY="sk-..."
export DASHSCOPE_MODEL="qwen-turbo"  # or qwen-plus, qwen-max
```

### UI Development
```bash
cd ui
bun install  # NOT npm/yarn - uses Bun
bun run dev  # Vite dev server on :5173

# Environment config
# Create .env.local: VITE_API_BASE_URL=http://localhost:8000
```

### Testing
- **Server**: `cd server && pytest tests/ -v`
- **UI**: `cd ui && bun test`

## LangChain Integration Patterns

**Current implementation** (after recent fixes):
- **SIMPLIFIED**: Not using `AgentExecutor` or `create_react_agent` due to import issues
- Uses basic **LangChain chain**: `PromptTemplate | Tongyi LLM`
- Chain invocation: `await chain.ainvoke({"input": prompt})` or `chain.astream(...)`

**Critical imports** (must use these exact paths):
```python
from langchain_community.llms import Tongyi  # Aliyun LLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import BaseMessage
```

**DO NOT import**: `langchain.agents.AgentExecutor`, `langchain.agents.create_react_agent` (not available in current setup)

## API Contract Patterns

### Non-Streaming Endpoint (`POST /agent`)
```python
# Request: PromptRequest
{"prompt": "user question"}

# Response: AgentResponse (200)
{"answer": "generated response"}

# Error: ErrorResponse (503)
{"error": "LLM service temporarily unavailable", "code": "LLM_UNAVAILABLE"}
```

### Streaming Endpoint (`POST /agent/stream`)
- **Input format**: Vercel AI SDK `UIMessage` format with `messages` array
- **Extracts**: Last user message from `parts[].text` or fallback to `content`
- **Output**: Server-Sent Events stream compatible with `@ai-sdk/react` `useChat` hook
- **Format**: `0:"text chunk"\n` (Vercel AI SDK streaming protocol)

## Project-Specific Conventions

### Error Handling
- **Always return HTTP 503** (not 500) for LLM failures - client expects this specific code
- **Never throw unhandled exceptions** in agent code - wrap in try/except and raise `Exception(f"LLM service error: {str(e)}")`
- FastAPI handler catches and converts to 503 with structured error JSON

### Type Safety
- **Python**: Use `Optional[Type]` for nullable fields, `Union[str, Dict, BaseMessage]` for flexible inputs
- **TypeScript**: Strict mode enabled, all props must be typed
- **RunnableConfig**: Use `from langchain_core.runnables import RunnableConfig` for LangChain config params

### BaseMessage.content Handling
```python
# WRONG - crashes if content is list
return input.content  

# CORRECT - handle str | list type
content = input.content
return content if isinstance(content, str) else str(content)
```

## External Dependencies

- **Aliyun Dashscope**: Requires `DASHSCOPE_API_KEY` env var, model names: `qwen-turbo`, `qwen-plus`, `qwen-max`
- **Package managers**: `uv` for Python (NOT pip directly), `bun` for UI (NOT npm/yarn)
- **LangChain versions**: `langchain>=0.1.0`, `langchain-community>=0.0.10` (specified in pyproject.toml)

## CORS Configuration
- **Permissive for local dev**: `allow_origins=["*"]` in `main.py`
- Enables UI on any port to call backend - essential for Vite HMR

## Streaming Implementation Notes

The streaming endpoint bridges two protocols:
1. **Client → Server**: Vercel AI SDK `UIMessage` format
2. **Server → Client**: SSE format with `0:"chunk"\n` protocol

UI uses `useChat` hook from `@ai-sdk/react` which handles:
- Message state management
- Automatic streaming connection
- Loading/error states via `status` and `error` props

## Common Pitfalls

1. **Don't use pip install** - use `uv pip install` in server
2. **Don't import AgentExecutor** - simplified chain approach only
3. **Check fallback mode first** - test without API key before debugging LLM issues
4. **Use type: ignore** for chain piping - `self.chain = prompt | self.llm  # type: ignore`
5. **Timeout is 6 minutes** - UI configured for long-running queries, not 30s default

## Debugging Entry Points

- Health check: `curl http://localhost:8000/health` - shows LLM config status
- Test non-streaming: `curl -X POST http://localhost:8000/agent -H "Content-Type: application/json" -d '{"prompt":"test"}'`
- Check logs: Server prints LLM initialization errors to stdout
- Fallback mode message: Responses prefixed with `[Fallback Mode] Echo:` when no API key

## Specification-Driven Development

This project uses **detailed specs** in `specs/001-monorepo-llm-agent/`:
- **Always reference spec.md** for requirements before implementing features
- **plan.md** contains phase-based implementation strategy
- **contracts/openapi.yaml** defines API contract
- Follow the established pattern: spec → plan → implementation → validation
