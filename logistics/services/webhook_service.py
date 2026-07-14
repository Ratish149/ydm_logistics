import hashlib
import hmac
import json
import logging
import threading
import urllib.error
import urllib.request
from datetime import datetime

from django.conf import settings

logger = logging.getLogger(__name__)


def _build_payload(order, new_status: str) -> dict:
    """Build the webhook payload dict for a status change event."""
    return {
        "event": "status_changed",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "tracking_number": order.tracking_number,
            "external_order_code": order.external_order_code,
            "new_status": new_status,
        },
    }


def _sign_payload(payload_bytes: bytes) -> str:
    """
    Generate an HMAC-SHA256 signature using SECRET_KEY so the receiving
    end can verify the request came from YDM.

    Header sent: X-YDM-Signature: sha256=<hex_digest>
    """
    secret = settings.SECRET_KEY.encode()
    signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


def _dispatch(webhook_url: str, payload: dict) -> None:
    """
    Perform the actual HTTP POST to the client's webhook URL.
    Called from a daemon thread so it never blocks the API response.
    """
    try:
        payload_bytes = json.dumps(payload).encode("utf-8")
        signature = _sign_payload(payload_bytes)

        req = urllib.request.Request(
            url=webhook_url,
            data=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-YDM-Signature": signature,
                "User-Agent": "YDM-Webhook/1.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info("Webhook delivered to %s — HTTP %s", webhook_url, resp.status)

    except urllib.error.HTTPError as exc:
        logger.warning(
            "Webhook to %s failed — HTTP %s: %s", webhook_url, exc.code, exc.reason
        )
    except urllib.error.URLError as exc:
        logger.warning("Webhook to %s unreachable — %s", webhook_url, exc.reason)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected webhook error for %s: %s", webhook_url, exc)


def fire_status_change_webhook(order, new_status: str, webhook_url: str) -> None:
    """
    Entry point called by the order service after a status update.

    Dispatches the webhook in a background daemon thread so the API
    response is never held up by the outbound HTTP request.
    """
    if not webhook_url:
        return

    payload = _build_payload(order, new_status)
    thread = threading.Thread(
        target=_dispatch,
        args=(webhook_url, payload),
        daemon=True,
        name=f"webhook-{order.tracking_number}",
    )
    thread.start()
