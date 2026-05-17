"""
iAgentPay — Safety Kernel
Atomic spending guards for AI agents. Prevents runaway spending,
hallucination-induced transactions, and unauthorized transfers.

Inspired by OmniAgentPay's Safety Kernel + Coinbase Agentic Wallets guardrails.

Guards available:
  - BudgetGuard:         Daily/weekly/session spending cap
  - RateLimit:           Max N transactions per time window
  - TransactionCap:      Max amount per single transaction
  - RecipientWhitelist:  Only pay approved addresses

Usage:
    from iagent_pay.safety_kernel import SafetyKernel, SafetyConfig

    kernel = SafetyKernel(SafetyConfig(
        daily_limit_usd=100.0,
        max_tx_usd=10.0,
        max_tx_per_minute=5,
        allowed_recipients=["0xAlice...", "0xBob..."],
    ))

    # Before every payment:
    kernel.check(amount=2.50, recipient="0xAlice...", currency="USDC")
    # Raises SafetyViolation if any rule is broken
"""
import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Optional, List
from collections import deque

logger = logging.getLogger("iagentpay.safety")


class SafetyViolation(Exception):
    """Raised when a payment violates a safety rule."""
    pass


class BudgetExceeded(SafetyViolation):
    pass


class RateLimitExceeded(SafetyViolation):
    pass


class TransactionCapExceeded(SafetyViolation):
    pass


class RecipientNotAllowed(SafetyViolation):
    pass


@dataclass
class SafetyConfig:
    """
    Configuration for the Safety Kernel.
    All USD amounts are approximate (converted at time of check).
    """
    # Budget Guards
    daily_limit_usd: float = 50.0       # Max spend per 24h
    weekly_limit_usd: float = 200.0     # Max spend per 7 days
    session_limit_usd: float = 10.0     # Max spend per session (since init)

    # Transaction Cap
    max_tx_usd: float = 5.0             # Max amount per single transaction

    # Rate Limits
    max_tx_per_minute: int = 10         # Max transactions per 60 seconds
    max_tx_per_hour: int = 50           # Max transactions per 3600 seconds

    # Recipient Whitelist (empty = allow all)
    allowed_recipients: List[str] = field(default_factory=list)

    # Human-in-the-loop threshold
    human_approval_threshold_usd: float = 20.0  # Require human above this amount

    # Enabled flags
    enable_budget_guard: bool = True
    enable_rate_limit: bool = True
    enable_tx_cap: bool = True
    enable_whitelist: bool = False      # Disabled by default (opt-in)


class SafetyKernel:
    """
    Thread-safe atomic safety kernel for AI agent payments.

    All checks are performed atomically using threading.Lock to prevent
    race conditions in multi-threaded or async agent environments.
    """

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or SafetyConfig()
        self._lock = threading.Lock()

        # Spending trackers
        self._session_spent: float = 0.0
        self._daily_spent: float = 0.0
        self._weekly_spent: float = 0.0
        self._daily_reset: float = time.time() + 86400
        self._weekly_reset: float = time.time() + 604800

        # Rate limiting (sliding window)
        self._tx_timestamps_minute: deque = deque()
        self._tx_timestamps_hour: deque = deque()

        # Audit log
        self._audit_log: list = []

    def _reset_budgets_if_needed(self):
        """Reset daily/weekly budgets when their windows expire."""
        now = time.time()
        if now > self._daily_reset:
            self._daily_spent = 0.0
            self._daily_reset = now + 86400
            logger.info("[SafetyKernel] Daily budget reset.")
        if now > self._weekly_reset:
            self._weekly_spent = 0.0
            self._weekly_reset = now + 604800
            logger.info("[SafetyKernel] Weekly budget reset.")

    def _clean_rate_windows(self):
        """Remove timestamps outside the sliding windows."""
        now = time.time()
        while self._tx_timestamps_minute and (now - self._tx_timestamps_minute[0]) > 60:
            self._tx_timestamps_minute.popleft()
        while self._tx_timestamps_hour and (now - self._tx_timestamps_hour[0]) > 3600:
            self._tx_timestamps_hour.popleft()

    def check(
        self,
        amount: float,
        recipient: str,
        currency: str = "USDC",
        usd_price: float = 1.0,  # For non-stablecoin: pass current USD price
    ) -> bool:
        """
        Atomically checks all safety rules before a payment.

        Args:
            amount:    Amount to send (in the currency unit)
            recipient: Destination address
            currency:  Token symbol (USDC, SOL, ETH, XRP)
            usd_price: USD value of 1 unit of currency (1.0 for USDC)

        Returns:
            True if all checks pass.

        Raises:
            SafetyViolation subclass if any rule is broken.
        """
        amount_usd = amount * usd_price

        with self._lock:
            self._reset_budgets_if_needed()
            self._clean_rate_windows()
            now = time.time()

            # 1. Transaction Cap
            if self.config.enable_tx_cap:
                if amount_usd > self.config.max_tx_usd:
                    raise TransactionCapExceeded(
                        f"Transaction of ${amount_usd:.2f} exceeds max_tx_usd=${self.config.max_tx_usd:.2f}"
                    )

            # 2. Budget Guards
            if self.config.enable_budget_guard:
                if self._session_spent + amount_usd > self.config.session_limit_usd:
                    raise BudgetExceeded(
                        f"Session budget exceeded: ${self._session_spent:.2f} + ${amount_usd:.2f} "
                        f"> ${self.config.session_limit_usd:.2f}"
                    )
                if self._daily_spent + amount_usd > self.config.daily_limit_usd:
                    raise BudgetExceeded(
                        f"Daily budget exceeded: ${self._daily_spent:.2f} + ${amount_usd:.2f} "
                        f"> ${self.config.daily_limit_usd:.2f}"
                    )
                if self._weekly_spent + amount_usd > self.config.weekly_limit_usd:
                    raise BudgetExceeded(
                        f"Weekly budget exceeded: ${self._weekly_spent:.2f} + ${amount_usd:.2f} "
                        f"> ${self.config.weekly_limit_usd:.2f}"
                    )

            # 3. Rate Limits
            if self.config.enable_rate_limit:
                if len(self._tx_timestamps_minute) >= self.config.max_tx_per_minute:
                    raise RateLimitExceeded(
                        f"Rate limit: max {self.config.max_tx_per_minute} tx/min exceeded"
                    )
                if len(self._tx_timestamps_hour) >= self.config.max_tx_per_hour:
                    raise RateLimitExceeded(
                        f"Rate limit: max {self.config.max_tx_per_hour} tx/hour exceeded"
                    )

            # 4. Recipient Whitelist
            if self.config.enable_whitelist and self.config.allowed_recipients:
                norm_recipient = recipient.lower().strip()
                allowed = [r.lower().strip() for r in self.config.allowed_recipients]
                if norm_recipient not in allowed:
                    raise RecipientNotAllowed(
                        f"Recipient {recipient} is not in the allowed_recipients list"
                    )

            # All checks passed — record the transaction
            self._session_spent += amount_usd
            self._daily_spent   += amount_usd
            self._weekly_spent  += amount_usd
            self._tx_timestamps_minute.append(now)
            self._tx_timestamps_hour.append(now)

            self._audit_log.append({
                "timestamp":  now,
                "amount":     amount,
                "amount_usd": amount_usd,
                "currency":   currency,
                "recipient":  recipient,
                "status":     "approved",
            })

            logger.info(
                f"[SafetyKernel] ✅ Approved ${amount_usd:.2f} to {recipient[:10]}... "
                f"(session: ${self._session_spent:.2f} / ${self.config.session_limit_usd:.2f})"
            )
            return True

    def needs_human_approval(self, amount_usd: float) -> bool:
        """Returns True if this amount requires human approval."""
        return amount_usd >= self.config.human_approval_threshold_usd

    def get_status(self) -> dict:
        """Returns current spending status across all windows."""
        with self._lock:
            self._reset_budgets_if_needed()
            return {
                "session_spent":    round(self._session_spent, 4),
                "session_limit":    self.config.session_limit_usd,
                "daily_spent":      round(self._daily_spent, 4),
                "daily_limit":      self.config.daily_limit_usd,
                "weekly_spent":     round(self._weekly_spent, 4),
                "weekly_limit":     self.config.weekly_limit_usd,
                "tx_last_minute":   len(self._tx_timestamps_minute),
                "tx_last_hour":     len(self._tx_timestamps_hour),
                "total_tx":         len(self._audit_log),
            }

    def get_audit_log(self) -> list:
        """Returns full audit log of all checked transactions."""
        return list(self._audit_log)

    def reset_session(self):
        """Resets session-level counters (daily/weekly persist)."""
        with self._lock:
            self._session_spent = 0.0
            logger.info("[SafetyKernel] Session reset.")
