"""Vercel serverless entrypoint — exposes the FastAPI app as an ASGI function.

Vercel's Python runtime detects the module-level `app` (ASGI) and serves it.
All /api/* routes are rewritten here (see vercel.json).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import app  # noqa: E402,F401  (re-exported for Vercel)
