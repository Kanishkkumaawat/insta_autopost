"""Razorpay payment integration helper."""

import os
import hmac
import hashlib
from typing import Optional, Dict, Any

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "").strip()
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()


def is_razorpay_configured() -> bool:
    """Return True if Razorpay credentials are set."""
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


def create_order(amount_paise: int, currency: str, receipt: str, notes: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """Create a Razorpay order. Returns order dict or None on failure."""
    if not is_razorpay_configured():
        return None
    try:
        import razorpay
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        data = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
        }
        if notes:
            data["notes"] = notes
        order = client.order.create(data=data)
        return {
            "id": order.get("id"),
            "amount": order.get("amount"),
            "currency": order.get("currency"),
            "key_id": RAZORPAY_KEY_ID,
        }
    except Exception:
        return None


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature."""
    if not RAZORPAY_KEY_SECRET:
        return False
    try:
        import razorpay
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
        return True
    except Exception:
        return False


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Razorpay webhook signature."""
    if not RAZORPAY_WEBHOOK_SECRET:
        return False
    try:
        expected = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False
