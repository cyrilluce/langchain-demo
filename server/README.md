# server

Python FastAPI-based LLM Agent demo.

Quick start

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the server:

```bash
uvicorn app.main:app --reload --port 8000
```

3. Example request:

```bash
curl -X POST http://localhost:8000/agent -H "Content-Type: application/json" -d '{"prompt":"Hello"}'
```
