# Research: Monorepo LLM Agent

**Feature**: 001-monorepo-llm-agent | **Date**: 2025-12-12

## Research Tasks

### 1. UI Testing Framework for Bun + React + TypeScript

**Context**: Need to determine the appropriate testing framework for the TypeScript React frontend running on Bun.

**Decision**: Vitest + React Testing Library

**Rationale**:
- **Vitest**: Native ESM support, excellent Bun compatibility, fast execution, Jest-compatible API
- **React Testing Library**: Industry standard for React component testing, encourages accessibility-focused tests
- **TypeScript integration**: First-class TypeScript support in both tools
- **Bun optimization**: Vitest leverages Bun's speed advantages better than Jest
- **Developer experience**: Familiar Jest-like syntax reduces learning curve

**Alternatives Considered**:
1. **Jest + React Testing Library**: Traditional choice but slower, requires additional config for ESM/Bun
2. **Bun's built-in test runner**: Still maturing, lacks React-specific utilities, smaller ecosystem
3. **Cypress/Playwright**: Overkill for this simple single-page scaffold, better for E2E than component tests

**Implementation Notes**:
- Install: `bun add -d vitest @testing-library/react @testing-library/user-event jsdom`
- Configure vitest.config.ts with React environment
- Add test scripts to package.json: `"test": "vitest"`, `"test:ui": "vitest --ui"`

---

### 2. Aliyun LLM SDK Integration Best Practices

**Context**: Need to integrate Aliyun's LLM services with langchain/langgraph for the agent backend.

**Decision**: Use `langchain-community` with Aliyun Dashscope integration

**Rationale**:
- **Dashscope**: Aliyun's unified AI service platform supporting Qwen models
- **Langchain integration**: `langchain-community` package includes `Tongyi` (通义) LLM wrapper
- **Compatibility**: Works seamlessly with langgraph for agent orchestration
- **Authentication**: Simple API key-based auth via environment variables
- **Fallback**: Easy to detect missing credentials and return deterministic responses

**Alternatives Considered**:
1. **Direct Aliyun SDK**: More control but bypasses langchain ecosystem benefits
2. **OpenAI-compatible endpoint**: Aliyun supports this but adds translation layer complexity
3. **Custom langchain wrapper**: Unnecessary reinvention, community package is maintained

**Implementation Notes**:
- Install: `pip install langchain langchain-community dashscope`
- Environment variable: `DASHSCOPE_API_KEY`
- Example usage:
  ```python
  from langchain_community.llms import Tongyi
  
  llm = Tongyi(
      model_name="qwen-turbo",  # or qwen-plus, qwen-max
      dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
  )
  ```
- Fallback detection: Check if `DASHSCOPE_API_KEY` is set before initializing LLM

---

### 3. CORS Configuration with FastAPI

**Context**: Clarified requirement to allow all origins (*) for local development flexibility.

**Decision**: Use FastAPI's `CORSMiddleware` with permissive settings

**Rationale**:
- **Simplicity**: Built-in middleware, no external dependencies
- **Development focus**: Spec explicitly states this is a dev scaffold
- **Flexibility**: Allows UI to run on any port without configuration changes

**Implementation Notes**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Considerations** (not in scope):
- Would restrict to specific origins
- Would implement proper authentication
- Would use environment-based configuration

---

### 4. HTTP Client Timeout Configuration (UI)

**Context**: 6-minute (360s) timeout requirement for agent responses.

**Decision**: Use `fetch` API with `AbortController`

**Rationale**:
- **Native support**: No additional dependencies needed
- **Standard approach**: Web platform standard
- **Cancellation**: Clean timeout implementation with AbortController
- **TypeScript friendly**: Well-typed in standard DOM types

**Implementation Notes**:
```typescript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 360000); // 6 minutes

try {
  const response = await fetch(url, {
    signal: controller.signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  });
  clearTimeout(timeoutId);
  // ... handle response
} catch (error) {
  if (error.name === 'AbortError') {
    // Handle timeout
  }
}
```

**Alternatives Considered**:
1. **Axios**: Adds dependency, timeout config slightly simpler but unnecessary overhead
2. **Custom Promise wrapper**: More complex than AbortController pattern

---

## Summary

All technical unknowns resolved:
- ✅ UI testing: Vitest + React Testing Library
- ✅ Aliyun LLM: langchain-community with Tongyi/Dashscope
- ✅ CORS: FastAPI CORSMiddleware with allow_origins=["*"]
- ✅ Timeout: fetch API with AbortController (360s)

Ready to proceed to Phase 1 (data model and contracts).
