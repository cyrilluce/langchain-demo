# Tasks: Monorepo LLM Agent

**Input**: Design documents from `/specs/001-monorepo-llm-agent/`
**Prerequisites**: plan.md (✅), spec.md (✅), research.md (✅), data-model.md (✅), contracts/ (✅)

**Tests**: Tests are NOT required per the feature specification. This is a development scaffold focused on basic functionality.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- All file paths are absolute from repository root

## Path Conventions

This is a **web application** monorepo:

- Server: `server/app/`, `server/tests/`
- UI: `ui/src/`, `ui/tests/`
- Documentation: `specs/001-monorepo-llm-agent/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic monorepo structure

- [X] T001 Create top-level README.md with setup instructions
- [X] T002 [P] Initialize Python server structure in server/
- [X] T003 [P] Initialize TypeScript UI structure in ui/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create server/requirements.txt with FastAPI, langchain, langchain-community, dashscope dependencies
- [X] T005 Create server/app/**init**.py
- [X] T006 Create ui/package.json with React, TypeScript, Vite dependencies
- [X] T007 Create ui/tsconfig.json with TypeScript configuration
- [X] T008 [P] Create server/app/models.py with Pydantic schemas (PromptRequest, AgentResponse, ErrorResponse)
- [X] T009 [P] Create ui/src/types/index.ts with TypeScript interfaces (AgentRequest, AgentResponse, ErrorResponse, LoadingState)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Server LLM Agent API (Priority: P1) 🎯 MVP

**Goal**: Developer can run FastAPI server locally and call POST /agent endpoint to get LLM responses

**Independent Test**:

```bash
curl -X POST http://localhost:5001/agent -H "Content-Type: application/json" -d '{"prompt":"Hello"}'
# Expected: {"answer": "..."}
```

### Implementation for User Story 1

- [X] T010 [P] [US1] Create server/app/config.py with environment variable handling (DASHSCOPE_API_KEY, model config)
- [X] T011 [P] [US1] Create server/app/agent.py with langchain/langgraph Aliyun integration
- [X] T012 [US1] Implement fallback logic in server/app/agent.py when credentials missing
- [X] T013 [US1] Create server/app/main.py with FastAPI app initialization
- [X] T014 [US1] Add CORS middleware to server/app/main.py (allow_origins=["*"])
- [X] T015 [US1] Implement POST /agent endpoint in server/app/main.py
- [X] T016 [US1] Add HTTP 503 error handling for LLM failures in server/app/main.py
- [X] T017 [US1] Implement GET /health endpoint in server/app/main.py
- [X] T018 [US1] Create server/README.md with installation and run instructions

**Checkpoint**: Server should be runnable via `uvicorn app.main:app` and respond to /agent requests

---

## Phase 4: User Story 2 - React TypeScript UI (Priority: P2)

**Goal**: Developer can run UI locally and interact with agent through browser interface with loading states and error handling

**Independent Test**:

1. Open <http://localhost:5173>
2. Enter prompt and click submit
3. See loading spinner → response appears
4. Try with server down → see error message

### Implementation for User Story 2

- [X] T019 [P] [US2] Create ui/src/services/api.ts with fetch API and AbortController for 360s timeout
- [X] T020 [P] [US2] Implement error handling in ui/src/services/api.ts for HTTP 503 and timeout
- [X] T021 [US2] Create ui/src/App.tsx with state management (prompt, answer, loadingState, error)
- [X] T022 [US2] Implement input form in ui/src/App.tsx (textarea for prompt, submit button)
- [X] T023 [US2] Implement loading spinner UI in ui/src/App.tsx (disabled controls during loading)
- [X] T024 [US2] Implement answer display in ui/src/App.tsx
- [X] T025 [US2] Implement error display in ui/src/App.tsx (HTTP errors and timeout)
- [X] T026 [US2] Create ui/src/main.tsx with React root rendering
- [X] T027 [US2] Create ui/index.html as entry point
- [X] T028 [US2] Configure Vite in ui/package.json scripts (dev, build, preview)
- [X] T029 [US2] Create ui/README.md with installation and run instructions

**Checkpoint**: UI should be runnable via `bun run dev` and successfully communicate with server

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] Add detailed quickstart verification steps to README.md
- [X] T031 [P] Add environment variable documentation to server/README.md
- [X] T032 [P] Add troubleshooting section to top-level README.md
- [X] T033 Verify server can run without DASHSCOPE_API_KEY (fallback mode)
- [X] T034 Verify UI timeout works correctly (6-minute threshold)
- [X] T035 Verify CORS allows UI on any port to access server
- [X] T036 Run full integration test: UI → Server → LLM (if credentials available)
- [X] T037 Verify both packages match structure in specs/001-monorepo-llm-agent/plan.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (Server) and User Story 2 (UI) can proceed in parallel
  - Or sequentially: US1 first (server), then US2 (UI)
- **Polish (Phase 5)**: Depends on both US1 and US2 being complete

### User Story Dependencies

- **User Story 1 (Server - P1)**: Can start after Foundational (Phase 2) - No dependencies on US2
- **User Story 2 (UI - P2)**: Can start after Foundational (Phase 2) - Works best with US1 complete for testing, but can develop in parallel with mock responses

### Within User Story 1 (Server)

1. Foundation: T010 (config), T011-T012 (agent with fallback)
2. API Setup: T013-T014 (FastAPI app, CORS)
3. Endpoints: T015-T017 (POST /agent, error handling, GET /health)
4. Documentation: T018 (README)

### Within User Story 2 (UI)

1. API Service: T019-T020 (fetch with timeout, error handling)
2. React Component: T021 (state management) → T022-T025 (UI elements)
3. Entry Points: T026-T027 (main.tsx, index.html)
4. Config & Docs: T028-T029 (Vite config, README)

### Parallel Opportunities

#### Phase 1 (Setup)

- T002, T003 can run in parallel (different directories)

#### Phase 2 (Foundational)

- T008, T009 can run in parallel (different languages/files)

#### Phase 3 (User Story 1 - Server)

- T010, T011 can run in parallel (config vs agent logic)

#### Phase 4 (User Story 2 - UI)

- T019, T020 can happen together (same file, sequential edits)

#### Phase 5 (Polish)

- T030, T031, T032 can run in parallel (different documentation files)

#### Across User Stories

- Once Foundational (Phase 2) completes, Phase 3 (US1) and Phase 4 (US2) can proceed in parallel with different developers

---

## Parallel Example: Foundational Phase

```bash
# After Phase 1 (Setup) completes:

# Developer A:
Create server/app/models.py [T008]

# Developer B (simultaneously):
Create ui/src/types/index.ts [T009]

# Result: Both schema definitions ready for their respective user stories
```

## Parallel Example: User Stories

```bash
# After Phase 2 (Foundational) completes:

# Developer A works on US1 (Server):
T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018

# Developer B works on US2 (UI) in parallel:
T019 → T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028 → T029

# Result: Both server and UI complete simultaneously
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Include for MVP**: User Story 1 (Server) ONLY

- Gets the agent working end-to-end
- Testable via curl commands
- Demonstrates LLM integration with fallback

**Add Next**: User Story 2 (UI)

- Provides user-friendly interface
- Demonstrates full monorepo value
- Enables manual testing in browser

### Incremental Delivery

1. **Milestone 1**: Phase 1 + Phase 2 (Project scaffolding)
   - Deliverable: Empty but properly structured monorepo

2. **Milestone 2**: Phase 3 complete (Server functional)
   - Deliverable: Working API that can be tested with curl

3. **Milestone 3**: Phase 4 complete (UI functional)
   - Deliverable: Full monorepo with browser interface

4. **Milestone 4**: Phase 5 complete (Polish)
   - Deliverable: Production-ready scaffold with documentation

### Validation Per Phase

- **After Phase 2**: Verify file structure matches plan.md
- **After Phase 3**: Run `curl http://localhost:5001/agent -X POST -d '{"prompt":"test"}'`
- **After Phase 4**: Open browser to <http://localhost:5173> and submit prompt
- **After Phase 5**: Follow quickstart.md from scratch in clean environment

---

## Task Statistics

- **Total Tasks**: 37
- **Setup Tasks**: 3 (Phase 1)
- **Foundational Tasks**: 6 (Phase 2)
- **User Story 1 Tasks**: 9 (Phase 3)
- **User Story 2 Tasks**: 11 (Phase 4)
- **Polish Tasks**: 8 (Phase 5)
- **Parallelizable Tasks**: 8 marked with [P]

**Estimated MVP Completion**: Phase 1 + Phase 2 + Phase 3 = 18 tasks
**Estimated Full Feature**: All 37 tasks

---

## Next Steps

1. Review and approve task breakdown
2. Begin Phase 1 (Setup)
3. Complete Phase 2 (Foundational) - GATE for user stories
4. Implement US1 (Server) for MVP
5. Implement US2 (UI) for complete feature
6. Polish and validate against quickstart.md

**Ready to implement**: Start with T001 ✅
