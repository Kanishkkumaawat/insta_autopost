"""Verify OPENAI_API_KEY from .env by calling OpenAI API."""

import os
import sys

# Load from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

key = (os.getenv("OPENAI_API_KEY") or "").strip()
if not key:
    print("FAIL: OPENAI_API_KEY not set in .env")
    sys.exit(1)

print("Checking OpenAI API key...")
try:
    from openai import OpenAI, AuthenticationError

    client = OpenAI(api_key=key)
    # Minimal call to validate key (cheap)
    list(client.models.list())[:1]
    print("OK: OpenAI API key is valid.")
except AuthenticationError as e:
    print(f"FAIL: Invalid API key — {e}")
    print("  Get a key at https://platform.openai.com/api-keys")
    print("  Put it in .env as OPENAI_API_KEY=sk-...")
    sys.exit(1)
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
