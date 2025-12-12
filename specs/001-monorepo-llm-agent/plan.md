# Implementation Plan: Monorepo LLM Agent

**Branch**: `001-monorepo-llm-agent` | **Date**: 2025-12-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-monorepo-llm-agent/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a minimal monorepo with Python FastAPI server (langchain/langgraph with Aliyun LLM) and Bun+React+TypeScript UI. Server exposes POST /agent endpoint accepting prompts, returns answers via Aliyun LLM integration. UI provides input interface with loading state, error handling, and 6-minute timeout. Development scaffold with permissive CORS for local testing.

## Technical Context

**Language/Version**: Python 3.10+ (server), uv runtime, TypeScript 5.x+ (UI), bun runtime
**Primary Dependencies**: FastAPI, langchain, langgraph, Aliyun SDK (server); React 18+, Bun runtime (UI)  
**Storage**: N/A (no persistence in initial scaffold)  
**Testing**: pytest (server), Vitest + React Testing Library (UI)  
**Target Platform**: macOS/Linux development environment (local server + browser)  
**Project Type**: web (separate backend + frontend packages)  
**Performance Goals**: <6 minute response time for LLM agent queries  
**Constraints**: 360-second client-side timeout, CORS allow-all for dev, HTTP 503 on LLM failures  
**Scale/Scope**: Single developer local scaffold, 2-3 API endpoints, <500 LOC total, 1 UI page

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file is a template placeholder without specific principles defined. No gates to enforce at this time. This monorepo follows standard patterns: web application structure (backend + frontend), no unusual complexity, straightforward testing approach.

**Status**: ✅ PASS (no constitution violations detected)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
server/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, routes
│   ├── models.py            # Request/response schemas
│   ├── agent.py             # Langchain/langgraph integration
│   └── config.py            # Aliyun credentials, settings
├── tests/
│   ├── test_api.py          # Endpoint contract tests
│   ├── test_agent.py        # Agent behavior tests
│   └── test_fallback.py     # No-credential fallback tests
├── requirements.txt
└── README.md

ui/
├── src/
│   ├── main.tsx             # Entry point
│   ├── App.tsx              # Main component with input/submit
│   ├── services/
│   │   └── api.ts           # Server communication logic
│   └── types/
│       └── index.ts         # TypeScript interfaces
├── tests/
│   └── [testing framework TBD]
├── package.json
├── tsconfig.json
└── README.md

README.md                    # Top-level setup instructions
```

**Structure Decision**: Web application pattern with separate backend (Python FastAPI) and frontend (TypeScript React). Each package is independently runnable and testable. Monorepo structure enables shared documentation while maintaining clear service boundaries.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No complexity violations. This is a standard web application scaffold with expected structure and dependencies.

---

## Phase Completion Status

### Phase 0: Outline & Research ✅

**Output**: [research.md](research.md)

Resolved all technical unknowns:

- UI testing framework → Vitest + React Testing Library
- Aliyun LLM integration → langchain-community with Tongyi/Dashscope
- CORS configuration → FastAPI CORSMiddleware with allow_origins=["*"]
- Timeout handling → fetch API with AbortController (360s)

### Phase 1: Design & Contracts ✅

**Outputs**:

- [data-model.md](data-model.md) - Entities: Prompt, Answer, ErrorResponse, Agent
- [contracts/openapi.yaml](contracts/openapi.yaml) - OpenAPI 3.0 spec with /agent and /health endpoints
- [quickstart.md](quickstart.md) - Setup and verification guide
- [.github/agents/copilot-instructions.md](../../.github/agents/copilot-instructions.md) - Updated agent context

**Constitution Re-check**: ✅ PASS (no violations after design)

### Phase 2: Task Breakdown 🚫

**Status**: Not executed (per speckit.plan scope)

**Next Command**: Run `/speckit.tasks` to generate implementation tasks.md

---

**Plan Generation Complete** | 2025-12-12
