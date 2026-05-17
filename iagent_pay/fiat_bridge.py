"""
iAgentPay — Fiat Bridge (Stripe + ACH)
Connects AI agents to traditional payment rails.
Inspired by: OpenAgentPay, AgentPayment.network.

Supported rails:
  - Stripe: Credit/debit cards, international payments
  - ACH:    US bank transfers (via Stripe ACH)
  - Hybrid: Auto-route between crypto and fiat based on amount/recipient

Use cases:
  - Agent needs to pay a human freelancer (fiat preferred)
  - Agent receives payment from non-crypto users
  - Hybrid payments: small amounts via USDC, large via ACH

Setup:
    pip install "iagent-pay[fiat]"
    export STRIPE_SECRET_KEY="sk_live_..."

Usage:
    from iagent_pay.fiat_bridge import FiatBridge

    bridge = FiatBridge()

    # Send money via Stripe (to a connected account)
    result = bridge.send_stripe(
        amount_usd=50.00,
        stripe_account_id="acct_...",
        description="Payment for research task",
    )

    # Create a payment link for humans to pay your agent
    link = bridge.create_payment_link(amount_usd=9.99, description="API Access")
    print(link.url)  # Share this with the payer
"""
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("iagentpay.fiat")


@dataclass
class FiatPaymentResult:
    success: bool
    rail: str                          # "stripe", "ach", "crypto"
    amount_usd: float
    reference_id: str
    status: str
    message: str
    raw: Optional[Dict[str, Any]] = None


class FiatBridge:
    """
    Unified fiat payment bridge for AI agents.
    Supports Stripe (cards) and ACH (bank transfers).
    """

    def __init__(self, stripe_key: Optional[str] = None):
        self._stripe_key = stripe_key or os.getenv("STRIPE_SECRET_KEY", "")
        self._stripe = None

        if self._stripe_key:
            try:
                import stripe
                stripe.api_key = self._stripe_key
                self._stripe = stripe
                logger.info("[FiatBridge] Stripe initialized.")
            except ImportError:
                logger.warning(
                    "[FiatBridge] Stripe not installed. "
                    "Run: pip install 'iagent-pay[fiat]'"
                )

    def _require_stripe(self):
        if not self._stripe:
            raise RuntimeError(
                "Stripe not configured. Set STRIPE_SECRET_KEY env var "
                "and run: pip install 'iagent-pay[fiat]'"
            )

    # ─── Send Payments ────────────────────────────────────────────────────────

    def send_stripe(
        self,
        amount_usd: float,
        stripe_account_id: str,
        description: str = "iAgentPay payment",
        currency: str = "usd",
    ) -> FiatPaymentResult:
        """
        Transfer funds to a Stripe Connected Account.
        Useful for paying human freelancers or vendors.

        Args:
            amount_usd:        Amount in USD
            stripe_account_id: Recipient's Stripe account ID (acct_...)
            description:       Payment description for the receipt
        """
        self._require_stripe()
        try:
            amount_cents = int(amount_usd * 100)
            transfer = self._stripe.Transfer.create(
                amount=amount_cents,
                currency=currency,
                destination=stripe_account_id,
                description=description,
                metadata={"source": "iagentpay", "version": "5.0.0"},
            )
            logger.info(
                f"[FiatBridge] Stripe transfer: ${amount_usd} → {stripe_account_id} "
                f"(id: {transfer.id})"
            )
            return FiatPaymentResult(
                success=True,
                rail="stripe",
                amount_usd=amount_usd,
                reference_id=transfer.id,
                status=transfer.get("status", "pending"),
                message=f"Stripe transfer created: {transfer.id}",
                raw=dict(transfer),
            )
        except Exception as e:
            logger.error(f"[FiatBridge] Stripe transfer failed: {e}")
            return FiatPaymentResult(
                success=False, rail="stripe", amount_usd=amount_usd,
                reference_id="", status="failed", message=str(e),
            )

    def send_ach(
        self,
        amount_usd: float,
        bank_account_id: str,
        description: str = "iAgentPay ACH payment",
    ) -> FiatPaymentResult:
        """
        Send via ACH bank transfer (US only).
        Lower fees than cards, 1-3 business day settlement.
        """
        self._require_stripe()
        try:
            amount_cents = int(amount_usd * 100)
            payout = self._stripe.Payout.create(
                amount=amount_cents,
                currency="usd",
                method="standard",
                description=description,
                metadata={"source": "iagentpay", "rail": "ach"},
            )
            return FiatPaymentResult(
                success=True,
                rail="ach",
                amount_usd=amount_usd,
                reference_id=payout.id,
                status=payout.status,
                message=f"ACH payout initiated: {payout.id}",
                raw=dict(payout),
            )
        except Exception as e:
            logger.error(f"[FiatBridge] ACH payout failed: {e}")
            return FiatPaymentResult(
                success=False, rail="ach", amount_usd=amount_usd,
                reference_id="", status="failed", message=str(e),
            )

    # ─── Receive Payments ─────────────────────────────────────────────────────

    def create_payment_link(
        self,
        amount_usd: float,
        description: str = "iAgentPay Service",
        currency: str = "usd",
        metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe Payment Link for humans to pay your agent.
        Returns a URL you can share with clients.

        Example:
            link = bridge.create_payment_link(9.99, "Premium API Access")
            print(link["url"])  # → https://buy.stripe.com/...
        """
        self._require_stripe()
        try:
            price = self._stripe.Price.create(
                unit_amount=int(amount_usd * 100),
                currency=currency,
                product_data={"name": description},
            )
            link = self._stripe.PaymentLink.create(
                line_items=[{"price": price.id, "quantity": 1}],
                metadata=metadata or {"source": "iagentpay"},
            )
            logger.info(f"[FiatBridge] Payment link created: {link.url}")
            return {
                "url":       link.url,
                "link_id":   link.id,
                "amount":    amount_usd,
                "currency":  currency.upper(),
                "active":    link.active,
            }
        except Exception as e:
            logger.error(f"[FiatBridge] Payment link failed: {e}")
            return {"error": str(e)}

    def create_invoice(
        self,
        customer_email: str,
        amount_usd: float,
        description: str,
        due_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Create and send a Stripe Invoice to a customer email.
        Useful for recurring agent services.
        """
        self._require_stripe()
        try:
            customer = self._stripe.Customer.create(email=customer_email)
            self._stripe.InvoiceItem.create(
                customer=customer.id,
                amount=int(amount_usd * 100),
                currency="usd",
                description=description,
            )
            invoice = self._stripe.Invoice.create(
                customer=customer.id,
                collection_method="send_invoice",
                days_until_due=due_days,
            )
            self._stripe.Invoice.finalize_invoice(invoice.id)
            self._stripe.Invoice.send_invoice(invoice.id)
            return {
                "invoice_id":    invoice.id,
                "hosted_url":    invoice.hosted_invoice_url,
                "amount":        amount_usd,
                "customer":      customer_email,
                "due_days":      due_days,
                "status":        invoice.status,
            }
        except Exception as e:
            logger.error(f"[FiatBridge] Invoice failed: {e}")
            return {"error": str(e)}

    # ─── Smart Router ─────────────────────────────────────────────────────────

    def smart_send(
        self,
        amount_usd: float,
        recipient: str,
        description: str = "",
        prefer_crypto: bool = True,
    ) -> FiatPaymentResult:
        """
        Automatically routes payment to best rail:
        - Small amounts (<$50) + crypto address → USDC on Base
        - Large amounts or email → ACH/Stripe

        Args:
            recipient:     Crypto address (0x...) or email
            prefer_crypto: If True, use USDC for crypto-compatible recipients
        """
        is_crypto_address = recipient.startswith("0x") or len(recipient) == 44

        if prefer_crypto and is_crypto_address and amount_usd <= 50.0:
            logger.info(f"[FiatBridge] Smart routing: USDC (${amount_usd})")
            return FiatPaymentResult(
                success=True, rail="usdc", amount_usd=amount_usd,
                reference_id="use_usdc_driver", status="routed",
                message=f"Route to USDCDriver.send({recipient}, {amount_usd})",
            )

        if "@" in recipient:
            logger.info(f"[FiatBridge] Smart routing: Stripe Invoice (${amount_usd})")
            result = self.create_invoice(recipient, amount_usd, description)
            return FiatPaymentResult(
                success="error" not in result, rail="stripe_invoice",
                amount_usd=amount_usd,
                reference_id=result.get("invoice_id", ""),
                status=result.get("status", "unknown"),
                message=result.get("hosted_url", result.get("error", "")),
            )

        return FiatPaymentResult(
            success=False, rail="none", amount_usd=amount_usd,
            reference_id="", status="unroutable",
            message=f"Cannot route to: {recipient}. Use crypto address or email.",
        )
