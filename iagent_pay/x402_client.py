"""
iAgentPay — x402 Protocol Client
Implements the HTTP 402 "Payment Required" standard for AI agent payments.
Compatible with the x402 Foundation specification (x402.org).

Adopted by: Google, AWS, Coinbase, Anthropic, Cloudflare, Stripe.
165M+ transactions processed as of May 2026.

Usage:
    client = X402Client(private_key="0x...", network="BASE_SEPOLIA")
    response = client.get("https://api.example.com/premium-data")
    # Automatically pays if server returns 402 and retries
"""
import json
import time
import hashlib
import hmac
import logging
from typing import Optional, Dict, Any
from decimal import Decimal

import requests

from .usdc_driver import USDCDriver

logger = logging.getLogger("iagentpay.x402")


class X402PaymentRequired(Exception):
    """Raised when a 402 response is received but payment fails."""
    pass


class X402BudgetExceeded(Exception):
    """Raised when the requested payment exceeds the configured max amount."""
    pass


class X402Client:
    """
    HTTP client that automatically handles 402 Payment Required responses.

    When a server returns HTTP 402, this client will:
    1. Parse the payment instructions from the response headers.
    2. Validate the amount is within the configured limit.
    3. Execute the USDC payment on the specified chain.
    4. Retry the original request with the payment proof header.

    Example:
        client = X402Client(
            private_key=os.getenv("ETH_PRIVATE_KEY"),
            network="BASE_SEPOLIA",
            max_amount_usdc=1.0,  # Never pay more than $1 per request
        )
        data = client.get("https://premium-api.com/search?q=AI+agents")
    """

    # x402 Standard Headers
    HEADER_PAYMENT_REQUIRED  = "X-Payment-Required"
    HEADER_PAYMENT_SIGNATURE = "X-Payment-Signature"
    HEADER_PAYMENT_RECEIPT   = "X-Payment-Receipt"

    def __init__(
        self,
        private_key: str,
        network: str = "BASE_SEPOLIA",
        max_amount_usdc: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        self.private_key = private_key
        self.network = network
        self.max_amount_usdc = max_amount_usdc
        self.max_retries = max_retries
        self.timeout = timeout
        self._usdc = USDCDriver(network=network)
        self._session = requests.Session()
        self._payment_history: list = []

    def _parse_payment_instructions(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse x402 payment instructions from a 402 response.
        Checks both headers and body for payment details.
        """
        instructions = {}

        # Check X-Payment-Required header (primary method)
        header_val = response.headers.get(self.HEADER_PAYMENT_REQUIRED)
        if header_val:
            try:
                instructions = json.loads(header_val)
            except json.JSONDecodeError:
                pass

        # Fallback: check response body
        if not instructions:
            try:
                body = response.json()
                if "payment" in body:
                    instructions = body["payment"]
                elif "amount" in body:
                    instructions = body
            except Exception:
                pass

        return instructions

    def _build_payment_signature(
        self,
        url: str,
        amount: float,
        currency: str,
        nonce: str,
    ) -> str:
        """
        Creates a cryptographic signature proving payment intent.
        Format: HMAC-SHA256(url + amount + currency + nonce, private_key_hash)
        """
        key = hashlib.sha256(self.private_key.encode()).hexdigest()
        message = f"{url}:{amount}:{currency}:{nonce}"
        sig = hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()
        return sig

    def _execute_payment(
        self,
        to_address: str,
        amount_usdc: float,
        url: str,
    ) -> dict:
        """Execute the actual USDC payment and return receipt."""
        logger.info(f"[x402] Paying {amount_usdc} USDC to {to_address} for {url}")
        result = self._usdc.send(
            private_key=self.private_key,
            to=to_address,
            amount_usdc=amount_usdc,
        )
        self._payment_history.append({
            "url":       url,
            "amount":    amount_usdc,
            "currency":  "USDC",
            "tx_hash":   result.get("tx_hash"),
            "timestamp": time.time(),
            "network":   self.network,
        })
        return result

    def request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> requests.Response:
        """
        Makes an HTTP request, automatically handling 402 responses.

        If the server returns 402:
        1. Parses payment instructions
        2. Validates amount <= max_amount_usdc
        3. Pays in USDC
        4. Retries with payment proof header
        """
        kwargs.setdefault("timeout", self.timeout)

        for attempt in range(self.max_retries):
            response = self._session.request(method, url, **kwargs)

            if response.status_code != 402:
                return response

            # --- Handle 402 ---
            logger.info(f"[x402] Got 402 from {url} (attempt {attempt + 1})")
            instructions = self._parse_payment_instructions(response)

            if not instructions:
                raise X402PaymentRequired(
                    f"Server returned 402 but no payment instructions found at {url}"
                )

            amount   = float(instructions.get("amount", 0))
            currency = instructions.get("currency", "USDC").upper()
            to_addr  = instructions.get("address") or instructions.get("to")
            nonce    = instructions.get("nonce", str(int(time.time())))

            if currency != "USDC":
                raise X402PaymentRequired(
                    f"iAgentPay x402 client only supports USDC (got {currency})"
                )

            if amount > self.max_amount_usdc:
                raise X402BudgetExceeded(
                    f"Server requested {amount} USDC but max_amount_usdc={self.max_amount_usdc}. "
                    f"Increase max_amount_usdc or decline this request."
                )

            if not to_addr:
                raise X402PaymentRequired(
                    f"No payment address in 402 response from {url}"
                )

            # Execute payment
            receipt = self._execute_payment(to_addr, amount, url)
            sig = self._build_payment_signature(url, amount, currency, nonce)

            # Retry with payment proof
            headers = kwargs.get("headers", {})
            headers[self.HEADER_PAYMENT_SIGNATURE] = sig
            headers[self.HEADER_PAYMENT_RECEIPT]   = receipt.get("tx_hash", "")
            kwargs["headers"] = headers

            logger.info(f"[x402] Payment sent (tx: {receipt.get('tx_hash')}). Retrying request...")

        raise X402PaymentRequired(
            f"Failed after {self.max_retries} attempts (402) for {url}"
        )

    # ─── Convenience Methods ──────────────────────────────────────────────────

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        return self.request("PUT", url, **kwargs)

    # ─── Utility ─────────────────────────────────────────────────────────────

    def get_payment_history(self) -> list:
        """Returns all payments made in this session."""
        return self._payment_history

    def get_total_spent(self) -> Decimal:
        """Returns total USDC spent in this session."""
        return Decimal(sum(p["amount"] for p in self._payment_history))

    def get_balance(self, address: str) -> Decimal:
        """Returns current USDC balance for the given address."""
        return self._usdc.balance(address)
