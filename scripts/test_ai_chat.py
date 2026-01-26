"""Test AI chat directly to see what's happening."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.ai import AIReplyService

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

print("=" * 60)
print("Testing AI Chat Service")
print("=" * 60)

# Check key
key = (os.getenv("OPENAI_API_KEY") or "").strip()
if not key:
    print("[ERROR] OPENAI_API_KEY not found in .env")
    sys.exit(1)

print(f"[OK] API Key found: {key[:20]}...{key[-10:]}\n")

# Create service
svc = AIReplyService()
print(f"Service available: {svc.is_available()}\n")

if not svc.is_available():
    print("[ERROR] Service not available - check OPENAI_API_KEY")
    sys.exit(1)

# Test call
print("Testing AI reply generation...")
print("-" * 60)

try:
    reply = svc.generate_reply(
        user_message="Bhejde bhai",
        post_context="Kitten playing with yarn",
        account_username="mr_tony.87",
        link="https://example.com/file.pdf"
    )
    
    print(f"\n[OK] Reply generated:")
    print(f"  {reply}")
    print(f"\n  Length: {len(reply)} chars")
    
    if reply == "Thanks for your comment! 💙":
        print("\n[WARNING] Using FALLBACK_REPLY - AI call failed (check logs above)")
        print("  Common reasons:")
        print("  - Quota exceeded (add billing at https://platform.openai.com/account/billing)")
        print("  - Invalid API key")
        print("  - Network error")
    else:
        print("\n[SUCCESS] AI generated a custom reply!")
        
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
