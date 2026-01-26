"""Instagram webhook parsing and forwarding. Logs all payloads, forwards comments/messages to existing services."""

from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


def _normalize_payload(body: Any) -> Dict[str, Any]:
    """Ensure payload is a dict. Meta may send { object, entry } or [ { object, entry } ]."""
    if isinstance(body, list) and body:
        return body[0] if isinstance(body[0], dict) else {}
    return body if isinstance(body, dict) else {}


def _account_id_for_ig_business(ig_business_id: str, app: Any) -> Optional[str]:
    """Resolve InstaForge account_id from Instagram business account ID."""
    if not app or not getattr(app, "account_service", None):
        return None
    for acc in app.account_service.list_accounts():
        if getattr(acc, "instagram_business_id", None) == ig_business_id:
            return acc.account_id
        if acc.account_id == ig_business_id:
            return acc.account_id
    return None


def _webhook_comment_to_service_format(value: Dict[str, Any]) -> Dict[str, Any]:
    """Map webhook comment value to shape expected by process_new_comments_for_dm (id, text, username, from)."""
    from_obj = value.get("from") or {}
    media_obj = value.get("media") or {}
    return {
        "id": value.get("id"),
        "text": value.get("text") or "",
        "username": from_obj.get("username") or "",
        "from": {"id": from_obj.get("id"), "username": from_obj.get("username")},
        "media": {"id": media_obj.get("id")},
    }


def _media_id_from_comment_value(value: Dict[str, Any]) -> Optional[str]:
    """Get media ID from a comment change value."""
    media = value.get("media")
    if isinstance(media, dict) and media.get("id"):
        return str(media["id"])
    return None


def process_webhook_payload(body: Any, app: Any) -> None:
    """
    Parse Instagram webhook payload, log it, forward comments to comment-to-DM service
    and messages to logging. Does not modify comment logic.
    """
    payload = _normalize_payload(body)
    logger.info("Instagram webhook payload received", payload=payload)

    obj = payload.get("object")
    if obj != "instagram":
        logger.debug("Instagram webhook ignored: object is not instagram", object=obj)
        return

    entries = payload.get("entry") or []
    for entry in entries:
        ig_id = entry.get("id")
        if not ig_id:
            continue
        account_id = _account_id_for_ig_business(str(ig_id), app)

        for change in entry.get("changes") or []:
            field = change.get("field")
            value = change.get("value")
            if not isinstance(value, dict):
                continue

            if field in ("comments", "live_comments"):
                comment = _webhook_comment_to_service_format(value)
                media_id = _media_id_from_comment_value(value)
                if not media_id:
                    logger.warning(
                        "Instagram webhook comment missing media id",
                        entry_id=ig_id,
                        comment_id=comment.get("id"),
                    )
                    continue
                comments = [comment]
                if account_id and app and getattr(app, "comment_to_dm_service", None):
                    try:
                        app.comment_to_dm_service.process_new_comments_for_dm(
                            account_id=account_id,
                            media_id=media_id,
                            comments=comments,
                            post_caption=None,
                        )
                        logger.info(
                            "Instagram webhook comment forwarded to comment-to-DM",
                            account_id=account_id,
                            media_id=media_id,
                            comment_id=comment.get("id"),
                        )
                    except Exception as e:
                        logger.exception(
                            "Instagram webhook comment forward failed",
                            account_id=account_id,
                            media_id=media_id,
                            error=str(e),
                        )
                else:
                    logger.debug(
                        "Instagram webhook comment not forwarded (no account or service)",
                        ig_id=ig_id,
                        account_id=account_id,
                    )

            elif field == "messages":
                logger.info(
                    "Instagram webhook messages event",
                    entry_id=ig_id,
                    account_id=account_id,
                    value=value,
                )
