"""
iAgentPay — Human-in-the-Loop (HITL)
Pauses agent payments that exceed a threshold and waits for human approval.
Supports: Console, Webhook (Telegram, Slack, Email).

Usage:
    from iagent_pay.human_loop import HumanApproval, HumanLoopConfig

    hitl = HumanApproval(HumanLoopConfig(
        threshold_usd=20.0,
        timeout_seconds=300,
        notify_webhook="https://hooks.slack.com/...",
    ))

    approved = hitl.request_approval(
        amount=25.0, currency="USDC", recipient="0xBob...", reason="Pay for API"
    )
    if approved:
        # proceed with payment
"""
import time
import threading
import logging
import json
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

import requests

logger = logging.getLogger("iagentpay.human_loop")


class ApprovalStatus(Enum):
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT  = "timeout"


@dataclass
class HumanLoopConfig:
    threshold_usd: float = 20.0          # Require human above this amount
    timeout_seconds: int = 300           # Seconds to wait before auto-canceling
    auto_reject_on_timeout: bool = True  # If True, timeout = reject

    # Notification channels (optional)
    notify_webhook: Optional[str] = None  # Generic webhook URL
    notify_telegram_token: Optional[str] = None
    notify_telegram_chat_id: Optional[str] = None

    # Console approval (for development/testing)
    allow_console_approval: bool = True


class PendingApproval:
    """Represents a payment waiting for human decision."""

    def __init__(self, approval_id: str, amount: float, currency: str,
                 recipient: str, reason: str):
        self.approval_id = approval_id
        self.amount      = amount
        self.currency    = currency
        self.recipient   = recipient
        self.reason      = reason
        self.created_at  = time.time()
        self.status      = ApprovalStatus.PENDING
        self._event      = threading.Event()

    def approve(self):
        self.status = ApprovalStatus.APPROVED
        self._event.set()

    def reject(self):
        self.status = ApprovalStatus.REJECTED
        self._event.set()

    def wait(self, timeout: int) -> ApprovalStatus:
        self._event.wait(timeout=timeout)
        if self.status == ApprovalStatus.PENDING:
            self.status = ApprovalStatus.TIMEOUT
        return self.status


class HumanApproval:
    """
    Human-in-the-Loop payment approval system.
    Pauses execution and notifies a human when a payment is too large.
    """

    def __init__(self, config: Optional[HumanLoopConfig] = None):
        self.config   = config or HumanLoopConfig()
        self._pending: dict[str, PendingApproval] = {}
        self._counter = 0

    def _generate_id(self) -> str:
        self._counter += 1
        return f"HITL-{int(time.time())}-{self._counter:04d}"

    def _notify(self, pending: PendingApproval):
        """Send notification to configured channels."""
        message = (
            f"⚠️ iAgentPay: Human Approval Required\n"
            f"ID:        {pending.approval_id}\n"
            f"Amount:    {pending.amount} {pending.currency}\n"
            f"Recipient: {pending.recipient}\n"
            f"Reason:    {pending.reason}\n"
            f"Timeout:   {self.config.timeout_seconds}s\n"
            f"Approve with: iagent-pay approve {pending.approval_id}"
        )

        # Webhook notification
        if self.config.notify_webhook:
            try:
                requests.post(self.config.notify_webhook,
                              json={"text": message}, timeout=10)
                logger.info(f"[HITL] Webhook notified for {pending.approval_id}")
            except Exception as e:
                logger.warning(f"[HITL] Webhook failed: {e}")

        # Telegram notification
        if self.config.notify_telegram_token and self.config.notify_telegram_chat_id:
            try:
                url = f"https://api.telegram.org/bot{self.config.notify_telegram_token}/sendMessage"
                requests.post(url, json={
                    "chat_id": self.config.notify_telegram_chat_id,
                    "text": message,
                }, timeout=10)
                logger.info(f"[HITL] Telegram notified for {pending.approval_id}")
            except Exception as e:
                logger.warning(f"[HITL] Telegram failed: {e}")

        # Console fallback
        if self.config.allow_console_approval:
            print(f"\n{'='*60}")
            print(message)
            print(f"{'='*60}")

    def request_approval(
        self,
        amount: float,
        currency: str,
        recipient: str,
        reason: str = "Agent payment",
        usd_price: float = 1.0,
    ) -> bool:
        """
        Requests human approval for a payment.

        If amount_usd < threshold: auto-approves (no interruption).
        If amount_usd >= threshold: pauses and waits for human decision.

        Returns True if approved, False if rejected or timed out.
        """
        amount_usd = amount * usd_price

        if amount_usd < self.config.threshold_usd:
            logger.debug(f"[HITL] Auto-approved ${amount_usd:.2f} (below threshold)")
            return True

        approval_id = self._generate_id()
        pending = PendingApproval(
            approval_id=approval_id,
            amount=amount,
            currency=currency,
            recipient=recipient,
            reason=reason,
        )
        self._pending[approval_id] = pending

        logger.warning(
            f"[HITL] 🔴 Payment ${amount_usd:.2f} requires human approval (ID: {approval_id})"
        )
        self._notify(pending)

        # In console mode: prompt user directly if attached to a terminal
        import sys
        if self.config.allow_console_approval and sys.stdin and sys.stdin.isatty():
            try:
                answer = input(f"\n→ Approve payment {approval_id}? [y/N]: ").strip().lower()
                if answer == "y":
                    pending.approve()
                else:
                    pending.reject()
            except (EOFError, KeyboardInterrupt):
                pending.reject()
        else:
            if self.config.allow_console_approval and (not sys.stdin or not sys.stdin.isatty()):
                logger.warning("[HITL] Console approval enabled but running in headless mode. Waiting for external webhook/API approval.")

            # Wait for external approval via approve()/reject() methods
            status = pending.wait(timeout=self.config.timeout_seconds)
            logger.info(f"[HITL] {approval_id} → {status.value}")

            if status == ApprovalStatus.TIMEOUT and self.config.auto_reject_on_timeout:
                logger.warning(f"[HITL] {approval_id} timed out — auto-rejected")
                return False

        del self._pending[approval_id]
        return pending.status == ApprovalStatus.APPROVED

    def approve(self, approval_id: str) -> bool:
        """Approve a pending payment (called externally, e.g., from a webhook handler)."""
        if approval_id in self._pending:
            self._pending[approval_id].approve()
            logger.info(f"[HITL] {approval_id} approved.")
            return True
        return False

    def reject(self, approval_id: str) -> bool:
        """Reject a pending payment."""
        if approval_id in self._pending:
            self._pending[approval_id].reject()
            logger.info(f"[HITL] {approval_id} rejected.")
            return True
        return False

    def list_pending(self) -> list:
        """Returns all pending approvals."""
        return [
            {
                "id":        p.approval_id,
                "amount":    p.amount,
                "currency":  p.currency,
                "recipient": p.recipient,
                "reason":    p.reason,
                "age_secs":  int(time.time() - p.created_at),
            }
            for p in self._pending.values()
        ]
