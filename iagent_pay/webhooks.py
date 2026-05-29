"""
iAgentPay — Webhooks with HMAC-SHA256
Enterprise-grade event system for agent payment notifications.
Industry standard used by: Stripe, AgentPayment.network, OpenAgentPay.

Events emitted:
  - payment.completed    : Payment confirmed on-chain
  - payment.failed       : Payment attempt failed
  - budget.exceeded      : Safety kernel blocked a payment
  - human.approval_needed: Payment waiting for human approval
  - human.approved       : Human approved a pending payment
  - human.rejected       : Human rejected a pending payment

Usage:
    from iagent_pay.webhooks import WebhookManager

    wm = WebhookManager(secret="my-shared-secret")
    wm.register("https://myserver.com/iagentpay-events")

    # Emit from payment flow
    wm.emit("payment.completed", {
        "tx_hash": "0xabc...",
        "amount":  5.0,
        "currency": "USDC",
        "to": "0xBob..."
    })

    # Verify incoming webhook (on your server side)
    is_valid = WebhookManager.verify_signature(
        payload=request.body,
        signature=request.headers["X-iAgentPay-Signature"],
        secret="my-shared-secret"
    )
"""
import hmac
import hashlib
import json
import time
import logging
import threading
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field

import requests
import urllib3.util.connection

logger = logging.getLogger("iagentpay.webhooks")

# Thread-local storage for DNS pinning
_dns_pinning = threading.local()

# Original urllib3 create_connection
_orig_create_connection = urllib3.util.connection.create_connection

def _patched_create_connection(address, *args, **kwargs):
    # address is (host, port)
    host, port = address
    pinned_ip = getattr(_dns_pinning, 'pinned_ip', None)
    pinned_host = getattr(_dns_pinning, 'pinned_host', None)
    if pinned_ip and pinned_host == host:
        return _orig_create_connection((pinned_ip, port), *args, **kwargs)
    return _orig_create_connection(address, *args, **kwargs)

urllib3.util.connection.create_connection = _patched_create_connection

# All supported event types
WEBHOOK_EVENTS = [
    "payment.completed",
    "payment.failed",
    "payment.pending",
    "budget.exceeded",
    "budget.warning",       # At 80% of budget
    "human.approval_needed",
    "human.approved",
    "human.rejected",
    "swap.completed",
    "swap.failed",
    "x402.paid",
    "x402.failed",
    "agent.created",
    "agent.paused",
]


@dataclass
class WebhookEndpoint:
    url: str
    secret: str
    events: List[str] = field(default_factory=lambda: ["*"])  # "*" = all events
    enabled: bool = True
    retry_count: int = 3
    timeout: int = 10


@dataclass
class WebhookEvent:
    event_type: str
    data: Dict[str, Any]
    event_id: str = ""
    timestamp: float = 0.0
    version: str = "5.0.0"

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"evt_{int(time.time() * 1000)}"
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "id":         self.event_id,
            "type":       self.event_type,
            "created_at": self.timestamp,
            "version":    self.version,
            "data":       self.data,
        }


class WebhookManager:
    """
    Manages webhook endpoints and delivers signed events.
    Uses HMAC-SHA256 for request authentication (same standard as Stripe).
    """

    SIGNATURE_HEADER = "X-iAgentPay-Signature"
    TIMESTAMP_HEADER = "X-iAgentPay-Timestamp"
    EVENT_HEADER     = "X-iAgentPay-Event"

    def __init__(self, default_secret: str = ""):
        self._endpoints: List[WebhookEndpoint] = []
        self._default_secret = default_secret
        self._local_handlers: Dict[str, List[Callable]] = {}
        self._delivery_log: list = []
        self._lock = threading.Lock()

    # ─── Registration ─────────────────────────────────────────────────────────

    def register(
        self,
        url: str,
        secret: Optional[str] = None,
        events: Optional[List[str]] = None,
    ) -> WebhookEndpoint:
        """Register a new webhook endpoint."""
        # SSRF Mitigation: Validate URL and ensure it only resolves to public, non-local/non-private IPs.
        import socket
        import ipaddress
        from urllib.parse import urlparse

        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL structure.")
            
            host = parsed_url.hostname
            if not host:
                raise ValueError("Invalid hostname.")
                
            # Resolve all IPs for the hostname
            addr_info = socket.getaddrinfo(host, None)
            for addr in addr_info:
                ip_str = addr[4][0]
                ip = ipaddress.ip_address(ip_str)
                # Check for loopback, private, link-local, multicast, etc.
                if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                    raise ValueError(f"URL resolves to non-public/private IP: {ip_str}")
        except Exception as e:
            raise ValueError(f"Webhook URL validation failed: {e}")

        endpoint = WebhookEndpoint(
            url=url,
            secret=secret or self._default_secret,
            events=events or ["*"],
        )
        with self._lock:
            self._endpoints.append(endpoint)
        logger.info(f"[Webhooks] Registered endpoint: {url} (events: {events or ['*']})")
        return endpoint

    def on(self, event_type: str, handler: Callable):
        """Register a local in-process event handler (no HTTP)."""
        if event_type not in self._local_handlers:
            self._local_handlers[event_type] = []
        self._local_handlers[event_type].append(handler)
        logger.debug(f"[Webhooks] Local handler registered for: {event_type}")

    def unregister(self, url: str):
        """Remove a webhook endpoint."""
        with self._lock:
            self._endpoints = [e for e in self._endpoints if e.url != url]
        logger.info(f"[Webhooks] Unregistered: {url}")

    # ─── Signature ────────────────────────────────────────────────────────────

    @staticmethod
    def sign(payload: str, secret: str, timestamp: Optional[str] = None) -> str:
        """
        Creates HMAC-SHA256 signature for a webhook payload.
        Format: t={timestamp},v1={signature}
        (Same format as Stripe webhooks for familiarity)
        """
        ts = timestamp or str(int(time.time()))
        signed_payload = f"{ts}.{payload}"
        sig = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"t={ts},v1={sig}"

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str,
                         tolerance_seconds: int = 300) -> bool:
        """
        Verifies an incoming webhook signature.
        Returns True if valid, False if tampered or expired.

        Use on your server to validate incoming iAgentPay webhooks:
            is_valid = WebhookManager.verify_signature(
                payload=request.body.decode(),
                signature=request.headers["X-iAgentPay-Signature"],
                secret="my-shared-secret"
            )
        """
        try:
            parts = dict(p.split("=", 1) for p in signature.split(","))
            ts  = parts.get("t", "0")
            sig = parts.get("v1", "")

            # Check timestamp freshness
            if abs(time.time() - int(ts)) > tolerance_seconds:
                logger.warning("[Webhooks] Signature expired (too old)")
                return False

            expected = hmac.new(
                secret.encode("utf-8"),
                f"{ts}.{payload}".encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(expected, sig)
        except Exception as e:
            logger.error(f"[Webhooks] Signature verification error: {e}")
            return False

    # ─── Delivery ─────────────────────────────────────────────────────────────

    def emit(self, event_type: str, data: Dict[str, Any], async_delivery: bool = True):
        """
        Emit an event to all registered endpoints and local handlers.

        Args:
            event_type:     Event name (e.g., "payment.completed")
            data:           Event payload dict
            async_delivery: If True, deliver in background thread (non-blocking)
        """
        event = WebhookEvent(event_type=event_type, data=data)

        # Local handlers (synchronous, in-process)
        for handler in self._local_handlers.get(event_type, []):
            try:
                handler(event.to_dict())
            except Exception as e:
                logger.error(f"[Webhooks] Local handler error for {event_type}: {e}")
        for handler in self._local_handlers.get("*", []):
            try:
                handler(event.to_dict())
            except Exception as e:
                logger.error(f"[Webhooks] Local wildcard handler error: {e}")

        # HTTP endpoints
        endpoints_to_notify = [
            ep for ep in self._endpoints
            if ep.enabled and ("*" in ep.events or event_type in ep.events)
        ]

        if not endpoints_to_notify:
            return

        if async_delivery:
            thread = threading.Thread(
                target=self._deliver_to_all,
                args=(event, endpoints_to_notify),
                daemon=True,
            )
            thread.start()
        else:
            self._deliver_to_all(event, endpoints_to_notify)

    def _deliver_to_all(self, event: WebhookEvent, endpoints: List[WebhookEndpoint]):
        """Deliver an event to multiple endpoints."""
        for endpoint in endpoints:
            self._deliver(event, endpoint)

    def _deliver(self, event: WebhookEvent, endpoint: WebhookEndpoint):
        """Deliver a single event to one endpoint with retries."""
        # Resolve, validate, and pin IP address to prevent SSRF and DNS Rebinding (TOCTOU)
        from urllib.parse import urlparse
        import socket
        import ipaddress

        try:
            parsed_url = urlparse(endpoint.url)
            host = parsed_url.hostname
            if not host:
                raise ValueError("Invalid URL structure.")
            
            # Resolve DNS
            addr_info = socket.getaddrinfo(host, parsed_url.port or (443 if parsed_url.scheme == 'https' else 80))
            if not addr_info:
                raise ValueError("No DNS records found.")
            
            # Check all resolved IPs to ensure they are all public.
            for addr in addr_info:
                ip_str = addr[4][0]
                ip = ipaddress.ip_address(ip_str)
                if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                    raise ValueError(f"IP {ip_str} is private/reserved.")
            
            # Pin the first resolved IP
            ip_str = addr_info[0][4][0]
        except Exception as e:
            logger.error(f"[Webhooks] SSRF/DNS Rebinding prevention: Webhook target URL resolution failed: {e}")
            with self._lock:
                self._delivery_log.append({
                    "event_id":   event.event_id,
                    "event_type": event.event_type,
                    "url":        endpoint.url,
                    "status":     "failed",
                    "http_code":  400,
                    "attempt":    1,
                    "timestamp":  time.time(),
                })
            return

        payload_str = json.dumps(event.to_dict())
        ts          = str(int(event.timestamp))
        signature   = self.sign(payload_str, endpoint.secret, ts)

        headers = {
            "Content-Type":         "application/json",
            self.SIGNATURE_HEADER:  signature,
            self.TIMESTAMP_HEADER:  ts,
            self.EVENT_HEADER:      event.event_type,
            "User-Agent":           "iAgentPay-Webhooks/5.0.0",
        }

        # Set the thread-local DNS pinning values
        _dns_pinning.pinned_host = host
        _dns_pinning.pinned_ip = ip_str

        try:
            for attempt in range(1, endpoint.retry_count + 1):
                try:
                    response = requests.post(
                        endpoint.url,
                        data=payload_str,
                        headers=headers,
                        timeout=endpoint.timeout,
                    )
                    status = "success" if response.status_code < 300 else "failed"
                    logger.info(
                        f"[Webhooks] {event.event_type} → {endpoint.url} "
                        f"({response.status_code}) attempt {attempt}"
                    )
                    with self._lock:
                        self._delivery_log.append({
                            "event_id":   event.event_id,
                            "event_type": event.event_type,
                            "url":        endpoint.url,
                            "status":     status,
                            "http_code":  response.status_code,
                            "attempt":    attempt,
                            "timestamp":  time.time(),
                        })
                    if response.status_code < 300:
                        return  # Success — no retry needed
                except requests.RequestException as e:
                    logger.warning(
                        f"[Webhooks] Delivery failed (attempt {attempt}/{endpoint.retry_count}): {e}"
                    )
                    if attempt < endpoint.retry_count:
                        time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
        finally:
            # Clean up the thread-local cache
            if hasattr(_dns_pinning, 'pinned_host'):
                del _dns_pinning.pinned_host
            if hasattr(_dns_pinning, 'pinned_ip'):
                del _dns_pinning.pinned_ip

        logger.error(
            f"[Webhooks] All {endpoint.retry_count} attempts failed for "
            f"{event.event_type} → {endpoint.url}"
        )

    def get_delivery_log(self, limit: int = 50) -> list:
        """Returns recent webhook delivery log."""
        return self._delivery_log[-limit:]

    def list_endpoints(self) -> list:
        """Returns all registered endpoints."""
        return [
            {"url": e.url, "events": e.events, "enabled": e.enabled}
            for e in self._endpoints
        ]
