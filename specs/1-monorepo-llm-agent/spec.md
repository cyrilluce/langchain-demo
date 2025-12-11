# Feature: Monorepo LLM Agent

Summary
-------

Create a minimal monorepo skeleton containing two top-level packages:

- `server`: a Python FastAPI-based LLM Agent application using `langchain` and `langgraph`.
- `ui`: a Bun + React frontend that can interact with the agent.

This spec defines the user scenarios, functional requirements, success criteria, key entities, and assumptions for the initial scaffold (no production hardening).

User Scenarios & Testing
-------------------------

- Scenario 1 — Developer runs the server locally:
  - Steps: install Python deps, start FastAPI server, call `POST /agent` with a prompt.
  - Expected: server returns a JSON response containing an `answer` string.

- Scenario 2 — Developer runs the UI locally:
  - Steps: install UI deps with Bun, start dev server, open browser, send a prompt from UI.
  - Expected: UI displays the response returned by the server.

Functional Requirements (Testable)
---------------------------------

1. Server exposes an HTTP endpoint `POST /agent` that accepts JSON `{ "prompt": "..." }` and returns `{ "answer": "..." }`.
   - Test: `curl -X POST http://localhost:8000/agent -d '{"prompt":"hi"}'` returns 200 and JSON with `answer`.

2. Server includes minimal integration example using `langchain` / `langgraph` APIs (safely guarded if libs are missing).
   - Test: running with libraries installed demonstrates a chained agent invocation. Without libs installed the endpoint returns a deterministic fallback response.

3. UI provides a single-page interface with an input box and a submit button that posts to the server endpoint and displays the `answer`.
   - Test: submitting a prompt updates the UI with the server response.

4. Project structure is a monorepo with two folders: `server/` and `ui/` and a top-level `README.md`.
   - Test: Listed files and README exist.

Success Criteria
----------------

- Developers can scaffold and run both server and UI locally within the repository in under 10 minutes following the README.
- `POST /agent` returns an answer for a sample prompt; measurable by automated curl check.
- UI can send a prompt and display the returned answer; verifiable manually in browser.

Key Entities
------------

- Prompt: the text input provided by the user to the agent.
- Answer: the generated output returned by the agent.
- Agent: the LLM orchestration layer (via `langchain`/`langgraph`) that consumes prompts and produces answers.

Assumptions
-----------

- This scaffold is for development/demo purposes only — no production secrets handling or deployment automation is included.
- Users will have Python 3.10+ (or compatible) and Bun installed to run server and UI respectively.
- Network access to third-party LLM providers is optional; the server includes a deterministic fallback when LLM SDKs or credentials are not present.

Security and Privacy
--------------------

- This scaffold does not store user prompts persistently. Any persistence would require additional specification.

Open Questions
--------------

- None for the initial scaffold. If you want authentication, rate limits, or persistence, mark these as follow-up features.

Spec created for: monorepo-llm-agent
