# FastAPI LLM Agent Server

Python FastAPI server with LangChain/LangGraph integration for LLM agent functionality.

## Features

- FastAPI-based REST API
- LangChain integration with Aliyun Dashscope (Qwen models)
- Graceful fallback when LLM credentials are not configured
- CORS enabled for development
- Comprehensive error handling

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Install uv (if not already installed):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

2. Create a virtual environment and install dependencies:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

3. Configure environment (optional):

Create a `.env` file in the `server/` directory:

```bash
DASHSCOPE_API_KEY=your-aliyun-dashscope-key
DASHSCOPE_MODEL=qwen-turbo  # or qwen-plus, qwen-max
```

**Note**: The server works without credentials in fallback mode.

## Running the Server

### Development Mode

Quick start with the included script:

```bash
./dev.sh
```

Or run directly:

```bash
uv run python -m uvicorn app.main:app --reload --port 8000
```

Or with activated virtual environment:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

The server will be available at <http://localhost:8000>

### Production Mode

```bash
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### POST /agent

Process a prompt with the LLM agent.

**Request:**

```json
{
  "prompt": "What is the capital of France?"
}
```

**Response (Success):**

```json
{
  "answer": "Paris is the capital of France."
}
```

**Response (Fallback Mode):**

```json
{
  "answer": "[Fallback Mode] Echo: What is the capital of France?... (LLM not configured. Set DASHSCOPE_API_KEY to enable AI responses.)"
}
```

**Response (Error - 503):**

```json
{
  "error": "LLM service temporarily unavailable. Please try again later.",
  "code": "LLM_UNAVAILABLE"
}
```

### GET /health

Check service health and configuration status.

**Response:**

```json
{
  "status": "healthy",
  "llm_configured": true
}
```

### GET /

uv run pytest tests/ -v
```

Run with coverage:

```bash
uv run ```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DASHSCOPE_API_KEY` | No | - | Aliyun Dashscope API key |
| `DASHSCOPE_MODEL` | No | `qwen-turbo` | Qwen model to use |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8000` | Server port |

## Project Structure

```
server/
├── app/
│   ├── __init__.py       # Package initialization
│   ├── main.py           # FastAPI app and routes
│   ├── models.py         # Pydantic schemas
│   ├── agent.py          # LangChain agent logic
│   └── config.py         # Configuration management
├── tests/
│   ├── test_api.py       # API endpoint tests
│   ├── test_agent.py     # Agent behavior tests
│   └── test_fallback.py  # Fallback mode tests
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

uv 
### Import Errors

If you encounter import errors with langchain:

```bash
pip install --upgrade pip
pip install langchain langchain-community dashscope --force-reinstall
```

### LLM Connection Issues

1. Verify your API key is correct
2. Check network connectivity to Aliyun services
3. Try a different model (qwen-plus, qwen-max)
4. Check the Dashscope service status
 run uv
### Port Already in Use

If port 8000 is already in use, specify a different port:

```bash
uv run python -m uvicorn app.main:app --reload --port 8001
```

## Development

### Code Style

Follow PEP 8 guidelines. Format code with:

```bash
black app/
uv run black app/
uv run isort app/
```

### Type Checking

Run mypy for type checking:

```bash
uv run ```

## License

See repository root for license information.
