#!/bin/bash
# Render startup script

cd app
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
