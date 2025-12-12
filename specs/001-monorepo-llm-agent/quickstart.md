# Quickstart: Monorepo LLM Agent

**Feature**: 001-monorepo-llm-agent | **Last Updated**: 2025-12-12

Get the monorepo running locally in under 10 minutes.

## Prerequisites

- **Python**: 3.10 or higher
- **Bun**: Latest version (install from [bun.sh](https://bun.sh))
- **OS**: macOS or Linux
- **Optional**: Aliyun Dashscope API key for LLM integration

---

## Quick Start

### 1. Clone & Navigate

```bash
cd /path/to/langchain-demo
git checkout 001-monorepo-llm-agent
```

### 2. Start the Server

```bash
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional: Configure Aliyun LLM (skip for fallback mode)
export DASHSCOPE_API_KEY="your-api-key-here"

# Start server
uvicorn app.main:app --reload --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
```

**Test endpoint**:
```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello, who are you?"}'
```

Expected response:
```json
{"answer":"[Generated response from LLM or fallback message]"}
```

### 3. Start the UI (New Terminal)

```bash
cd ui
bun install
bun run dev
```

**Expected output**:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

### 4. Open Browser

Navigate to [http://localhost:5173](http://localhost:5173)

**What to expect**:
1. Single-page interface with text input and submit button
2. Type a prompt (e.g., "What is TypeScript?")
3. Click submit → See loading spinner
4. Response appears in the UI (LLM answer or fallback)

---

## Configuration

### Environment Variables (Server)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DASHSCOPE_API_KEY` | No | - | Aliyun Dashscope API key for LLM access |
| `DASHSCOPE_MODEL` | No | `qwen-turbo` | Model to use (qwen-turbo, qwen-plus, qwen-max) |
| `PORT` | No | `8000` | Server port |

### Configuration Files

- **server/requirements.txt**: Python dependencies
- **ui/package.json**: Node dependencies and scripts
- **ui/tsconfig.json**: TypeScript compiler options

---

## Verification Tests

### Server Functional Tests

```bash
cd server
pytest tests/test_api.py -v
```

Expected: All tests pass, covering:
- ✅ POST /agent returns 200 with valid prompt
- ✅ POST /agent returns 422 with empty prompt
- ✅ GET /health returns service status

### UI Tests

```bash
cd ui
bun test
```

Expected: Component and API service tests pass

### Manual Integration Test

1. Server running on port 8000
2. UI running on port 5173
3. Submit prompt "Test integration"
4. Verify response displays without CORS errors
5. Verify loading spinner shows during request
6. Verify timeout after 6 minutes (optional long test)

---

## Troubleshooting

### Issue: CORS errors in browser console

**Solution**: Ensure server is running and CORS middleware is configured (should be automatic)

### Issue: "Module not found" errors (Server)

**Solution**: 
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Issue: Bun command not found (UI)

**Solution**: Install Bun:
```bash
curl -fsSL https://bun.sh/install | bash
```

### Issue: Timeout errors in UI

**Expected behavior**: 6-minute timeout is intentional. Verify:
1. Server is responding (test with curl)
2. Network connection is stable
3. LLM API (if configured) is accessible

### Issue: Import errors with langchain

**Solution**: Install langchain-community separately:
```bash
pip install langchain-community dashscope
```

---

## Next Steps

After verifying the basic setup:

1. **Customize LLM behavior**: Edit `server/app/agent.py` to modify langchain chains
2. **Enhance UI**: Add features in `ui/src/App.tsx`
3. **Add tests**: Expand test coverage in both packages
4. **Deploy**: Follow production deployment guide (TBD)

---

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐
│   Browser UI    │         │  FastAPI Server  │
│  (React + TS)   │ ◄─────► │  (Python 3.10+)  │
│  localhost:5173 │  HTTP   │  localhost:8000  │
└─────────────────┘         └────────┬─────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Aliyun Dashscope│
                            │  (Qwen Models)  │
                            └─────────────────┘
```

**Request Flow**:
1. User enters prompt in UI
2. UI sends POST to `/agent` with JSON
3. Server validates request
4. Agent processes via langchain + Aliyun LLM
5. Server returns JSON response
6. UI displays answer

**Error Flow**:
1. LLM unavailable → Server returns HTTP 503
2. UI displays error message
3. User can retry

---

## Reference

- **API Documentation**: See [contracts/openapi.yaml](contracts/openapi.yaml)
- **Data Models**: See [data-model.md](data-model.md)
- **Research Decisions**: See [research.md](research.md)
- **Full Spec**: See [spec.md](spec.md)
