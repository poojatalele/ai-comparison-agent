"""ASGI entry point.

Run with:

    uvicorn server.main:app --reload --port 8000
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# Load server/.env BEFORE anything reads Settings.from_env().
load_dotenv(Path(__file__).resolve().parent / ".env")

from .app import create_app  # noqa: E402  (must run after load_dotenv)

app = create_app()
