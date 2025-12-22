# Langchain Demo - Monorepo LLM Agent

A minimal development scaffold featuring a Python FastAPI backend with LangChain/LangGraph integration and a React TypeScript frontend.

## Project Structure

```
.
├── server/          # Python FastAPI LLM Agent
├── ui/              # React TypeScript Frontend
└── specs/           # Feature specifications
```

## Quick Start

### Prerequisites

- Python 3.10+
- Bun (latest version)
- Optional: Aliyun Dashscope API key

### 1. Start the Server

```bash
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional: Configure Aliyun LLM
export DASHSCOPE_API_KEY="your-api-key-here"

# Start server
uvicorn app.main:app --reload --port 5001
```

Server will be available at http://localhost:5001

### 2. Start the UI

```bash
cd ui
bun install
bun run dev
```

UI will be available at http://localhost:5173

### 3. Test the Integration

Open http://localhost:5173 in your browser and submit a prompt to the LLM agent.

## API Endpoints

- `POST /agent` - Submit a prompt to the LLM agent
- `GET /health` - Check service health status

## Development

### Server Tests

```bash
cd server
pytest tests/ -v
```

### UI Tests

```bash
cd ui
bun test
```

## Configuration

### Server Environment Variables

- `DASHSCOPE_API_KEY` - Aliyun Dashscope API key (optional, uses fallback if not set)
- `DASHSCOPE_MODEL` - Model name (default: qwen-turbo)

## Features

- **FastAPI Backend**: High-performance async Python web framework
- **LangChain Integration**: LLM orchestration with langchain/langgraph
- **Aliyun Dashscope**: Integration with Qwen models
- **React UI**: Modern TypeScript React frontend with Vite
- **Graceful Fallback**: Works without LLM credentials for development
- **Error Handling**: Comprehensive error handling with HTTP 503 for LLM failures
- **Long Timeouts**: 6-minute client-side timeout for complex queries

## Documentation

See `specs/001-monorepo-llm-agent/` for detailed feature specifications:
- `spec.md` - Feature requirements
- `plan.md` - Implementation plan
- `quickstart.md` - Detailed setup guide
- `contracts/openapi.yaml` - API specification

## Troubleshooting

### CORS Errors

Ensure the server is running. CORS is configured to allow all origins for development.

### Import Errors

```bash
# Server
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# UI
bun install --force
```

### Timeout Issues

The UI has a 6-minute timeout for LLM responses. For faster responses:
- Use a more powerful model (qwen-plus or qwen-max)
- Simplify your prompts
- Check your network connection

## License

This is a development scaffold. See your organization's licensing requirements.
