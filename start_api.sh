#!/bin/bash
source venv/bin/activate && uvicorn api.server:app --reload --port 8000
