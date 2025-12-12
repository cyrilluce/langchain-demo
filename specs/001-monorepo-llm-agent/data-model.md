# Data Model: Monorepo LLM Agent

**Feature**: 001-monorepo-llm-agent | **Date**: 2025-12-12

## Entities

### 1. Prompt

**Description**: User input text sent to the LLM agent for processing.

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `prompt` | string | Yes | 1-10000 chars | The text query from the user |

**State**: Stateless (not persisted)

**Relationships**: Input to Agent processing

---

### 2. Answer

**Description**: Generated response from the LLM agent.

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `answer` | string | Yes | Non-empty | The agent's generated response text |

**State**: Stateless (not persisted)

**Relationships**: Output from Agent processing

---

### 3. ErrorResponse

**Description**: Error information returned when agent processing fails.

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `error` | string | Yes | Non-empty | Human-readable error message |
| `code` | string | No | - | Optional error code (e.g., "LLM_UNAVAILABLE") |

**State**: Ephemeral (request-scoped)

---

### 4. Agent (Internal)

**Description**: LLM orchestration layer using langchain/langgraph.

**Properties**:
- LLM provider: Aliyun Dashscope (Tongyi)
- Model: Configurable (default: qwen-turbo)
- Credentials: DASHSCOPE_API_KEY environment variable

**State Transitions**:
1. **Initialized**: Agent created with valid credentials
2. **Fallback**: Agent created without credentials (deterministic mode)
3. **Processing**: Agent executing LLM chain
4. **Completed**: Response generated
5. **Failed**: LLM API error (timeout, rate limit, etc.)

**Behavior**:
- Accept Prompt → Process via langchain chain → Return Answer
- On missing credentials → Return fallback Answer
- On LLM failure → Raise exception (handled by API layer as HTTP 503)

---

## Type Definitions

### TypeScript (UI)

```typescript
// src/types/index.ts

export interface AgentRequest {
  prompt: string;
}

export interface AgentResponse {
  answer: string;
}

export interface ErrorResponse {
  error: string;
  code?: string;
}

export type LoadingState = 'idle' | 'loading' | 'success' | 'error' | 'timeout';
```

### Python (Server)

```python
# server/app/models.py

from pydantic import BaseModel, Field

class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)

class AgentResponse(BaseModel):
    answer: str = Field(..., min_length=1)

class ErrorResponse(BaseModel):
    error: str
    code: str | None = None
```

---

## Validation Rules

### Prompt Validation
- **Length**: 1-10000 characters
- **Format**: Plain text (no binary data)
- **Required**: Cannot be null or empty string

### Answer Validation
- **Non-empty**: Must contain at least one character
- **Format**: UTF-8 text

### Error Handling
- Invalid prompt → HTTP 422 (Unprocessable Entity)
- LLM unavailable → HTTP 503 (Service Unavailable)
- Timeout → Client-side error display (no server response)

---

## Persistence

**Current Scope**: No persistence required. All data is request-scoped.

**Future Considerations** (out of scope):
- Session history storage
- Conversation threading
- Usage analytics
