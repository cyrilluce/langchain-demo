#!/bin/bash
# Development server startup script

cd "$(dirname "$0")"
uv run uvicorn app.main:app --reload --port 5001
