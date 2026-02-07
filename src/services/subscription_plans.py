"""Subscription plan definitions and limits for Razorpay."""

from typing import Dict, Any

# Plan IDs must match Razorpay plan IDs if using subscriptions
PLAN_FREE = "free"
PLAN_STARTER = "starter"
PLAN_PRO = "pro"

# Razorpay price IDs (create these in Razorpay Dashboard)
RAZORPAY_PLAN_IDS = {
    PLAN_STARTER: "plan_starter_999",  # Replace with actual Razorpay plan ID
    PLAN_PRO: "plan_pro_2999",         # Replace with actual Razorpay plan ID
}

# Amounts in paise (1 INR = 100 paise)
RAZORPAY_AMOUNTS = {
    PLAN_STARTER: 99900,   # Rs 999
    PLAN_PRO: 299900,      # Rs 2,999
}

PLAN_LIMITS: Dict[str, Dict[str, Any]] = {
    PLAN_FREE: {
        "name": "Free",
        "price": 0,
        "price_display": "Rs 0",
        "accounts": 1,
        "scheduled_posts_per_month": 5,
        "ai_dm": False,
        "batch_upload": False,
        "batch_upload_max_files": 0,
        "warmup_automation": False,
        "comment_to_dm": False,
    },
    PLAN_STARTER: {
        "name": "Starter",
        "price": 999,
        "price_display": "Rs 999",
        "accounts": 3,
        "scheduled_posts_per_month": 30,
        "ai_dm": True,
        "batch_upload": True,
        "batch_upload_max_files": 10,
        "warmup_automation": True,
        "comment_to_dm": True,
    },
    PLAN_PRO: {
        "name": "Pro",
        "price": 2999,
        "price_display": "Rs 2,999",
        "accounts": 10,
        "scheduled_posts_per_month": -1,  # unlimited
        "ai_dm": True,
        "batch_upload": True,
        "batch_upload_max_files": 31,
        "warmup_automation": True,
        "comment_to_dm": True,
    },
}


def get_plan_limits(plan: str) -> Dict[str, Any]:
    """Return limits for a plan. Defaults to free if unknown."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[PLAN_FREE]).copy()


def can_use_feature(plan: str, feature: str, current_count: int = 0) -> bool:
    """Check if user's plan allows a feature."""
    limits = get_plan_limits(plan)
    if feature == "accounts":
        return current_count < limits["accounts"]
    if feature == "scheduled_posts":
        if limits["scheduled_posts_per_month"] == -1:
            return True
        return current_count < limits["scheduled_posts_per_month"]
    if feature == "ai_dm":
        return limits["ai_dm"]
    if feature == "batch_upload":
        return limits["batch_upload"]
    if feature == "batch_upload_files":
        return current_count <= limits["batch_upload_max_files"]
    if feature == "warmup_automation":
        return limits["warmup_automation"]
    if feature == "comment_to_dm":
        return limits["comment_to_dm"]
    return False
