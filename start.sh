#!/bin/bash
# Render startup script with unbuffered output

cd app
# -u flag: unbuffered output (forces immediate log flushing)
python -u -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
