"""
iAgent-Pay — Session Keys & Zero-Custody Swap Module
Protects user funds by giving AI agents restricted ephemeral keys with strict bounds.
"""

import time
import json
import logging
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount
from typing import List, Optional, Dict, Any

logger = logging.getLogger("iagentpay.session")

class SessionKeyError(Exception):
    """Raised when session key verification or usage fails."""
    pass

class SessionKeyExpired(SessionKeyError):
    pass

class SessionKeyLimitExceeded(SessionKeyError):
    pass

class SessionKeyUnauthorized(SessionKeyError):
    pass


class SessionKey:
    """
    Represents a secure Session Key (Clave de Sesión) for AI Agents.
    Contains the ephemeral private key and restriction bounds signed by the owner.
    """

    def __init__(
        self,
        session_private_key: str,
        owner_address: str,
        allowed_tokens: List[str],
        daily_limit_usd: float,
        max_tx_usd: float,
        expiry: float,
        allowed_destinations: Optional[List[str]] = None,
        owner_signature: Optional[str] = None
    ):
        # Handle 0x prefix for private key
        key_hex = session_private_key
        if key_hex.startswith("0x"):
            key_hex = key_hex[2:]
        self.session_private_key = key_hex
        self.session_account: LocalAccount = Account.from_key(self.session_private_key)
        self.session_address = self.session_account.address
        self.owner_address = owner_address
        self.allowed_tokens = [t.upper() for t in allowed_tokens]
        self.daily_limit_usd = daily_limit_usd
        self.max_tx_usd = max_tx_usd
        self.expiry = expiry
        self.allowed_destinations = [d.lower().strip() for d in allowed_destinations] if allowed_destinations else []
        self.owner_signature = owner_signature
        
        # Spending trackers
        self.spent_usd_today = 0.0
        self.last_spend_timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_private_key": self.session_private_key,
            "session_address": self.session_address,
            "owner_address": self.owner_address,
            "allowed_tokens": self.allowed_tokens,
            "daily_limit_usd": self.daily_limit_usd,
            "max_tx_usd": self.max_tx_usd,
            "expiry": self.expiry,
            "allowed_destinations": self.allowed_destinations,
            "owner_signature": self.owner_signature
        }

    def get_message_hash(self) -> bytes:
        """
        Creates a deterministic hash of the session parameters to sign.
        """
        payload = {
            "session_address": self.session_address.lower(),
            "owner_address": self.owner_address.lower(),
            "allowed_tokens": sorted(self.allowed_tokens),
            "daily_limit_usd": float(self.daily_limit_usd),
            "max_tx_usd": float(self.max_tx_usd),
            "expiry": int(self.expiry),
            "allowed_destinations": sorted(self.allowed_destinations)
        }
        message_str = json.dumps(payload, sort_keys=True)
        return encode_defunct(text=message_str)

    def verify_signature(self) -> bool:
        """
        Verifies that the owner signed these exact session parameters.
        """
        if not self.owner_signature:
            return False
        try:
            msg_hash = self.get_message_hash()
            recovered_addr = Account.recover_message(msg_hash, signature=self.owner_signature)
            return recovered_addr.lower() == self.owner_address.lower()
        except Exception:
            return False

    def validate_payment(self, amount_usd: float, token: str, recipient: str):
        """
        Validates a payment against all strict session bounds.
        """
        # 1. Expiry Check
        if time.time() > self.expiry:
            raise SessionKeyExpired(f"Session key expired at {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(self.expiry))} UTC")

        # 2. Token Check
        if token.upper() not in self.allowed_tokens:
            raise SessionKeyUnauthorized(f"Token '{token}' is not pre-approved for this session. Approved: {self.allowed_tokens}")

        # 3. Destination Check
        if self.allowed_destinations:
            norm_recipient = recipient.lower().strip()
            if norm_recipient not in self.allowed_destinations:
                raise SessionKeyUnauthorized(f"Recipient {recipient} is not in the allowed destinations for this session.")

        # 4. Single transaction limit
        if amount_usd > self.max_tx_usd:
            raise SessionKeyLimitExceeded(f"Amount ${amount_usd:.2f} exceeds maximum single transaction limit of ${self.max_tx_usd:.2f}")

        # Reset daily limit tracker if new day
        now = time.time()
        if now - self.last_spend_timestamp > 86400:
            self.spent_usd_today = 0.0
            self.last_spend_timestamp = now

        # 5. Cumulative Daily Limit
        if self.spent_usd_today + amount_usd > self.daily_limit_usd:
            raise SessionKeyLimitExceeded(
                f"Daily session limit exceeded: Spent ${self.spent_usd_today:.2f} + ${amount_usd:.2f} "
                f"> Limit ${self.daily_limit_usd:.2f}"
            )

    def record_spend(self, amount_usd: float):
        """Records a successful payment's spend."""
        self.spent_usd_today += amount_usd
        self.last_spend_timestamp = time.time()


class SessionKeyManager:
    """
    Creates, signs, and registers session keys for agents.
    Allows zero-custody swaps where agent acts on owner's behalf within constraints.
    """

    @classmethod
    def generate(
        cls,
        max_amount_usd: float,
        duration_hours: float = 1.0,
        owner_account: Optional[LocalAccount] = None,
        allowed_tokens: Optional[List[str]] = None,
        allowed_destinations: Optional[List[str]] = None
    ) -> SessionKey:
        """
        Simplified wrapper for creating a session key.
        Matches the expected simplified API signature from documentation.
        """
        if owner_account is None:
            # Fallback for testing/simplified usage
            owner_account = Account.create()
        if allowed_tokens is None:
            allowed_tokens = ["USDC", "USDT", "ETH", "SOL", "XRP"]
            
        return cls.create_session(
            owner_account=owner_account,
            allowed_tokens=allowed_tokens,
            daily_limit_usd=max_amount_usd * 10.0,
            max_tx_usd=max_amount_usd,
            validity_seconds=int(duration_hours * 3600),
            allowed_destinations=allowed_destinations
        )

    @staticmethod
    def create_session(
        owner_account: LocalAccount,
        allowed_tokens: List[str],
        daily_limit_usd: float,
        max_tx_usd: float,
        validity_seconds: int = 3600 * 2,  # 2 hours default
        allowed_destinations: Optional[List[str]] = None
    ) -> SessionKey:
        """
        Creates and signs a new restricted Session Key.
        """
        # --- CLIENT RESPONSIBILITY WARNING ---
        if daily_limit_usd > 10000.0 or max_tx_usd > 5000.0:
            logger.warning(
                f"\n⚠️ [CLIENT RESPONSIBILITY] You are setting very high limits (Daily: ${daily_limit_usd}, Max Tx: ${max_tx_usd}). "
                "iAgentPay does NOT enforce global protocol limits to allow maximum scale. "
                "YOU are solely responsible for the limits you grant to this AI Agent.\n"
            )

        # Generate new ephemeral private key for the session
        session_acc = Account.create()
        expiry = time.time() + validity_seconds
        
        # If no allowed_destinations is provided, default to only allowing sending back to the owner
        if allowed_destinations is None:
            allowed_destinations = [owner_account.address]

        session = SessionKey(
            session_private_key=session_acc.key.hex(),
            owner_address=owner_account.address,
            allowed_tokens=allowed_tokens,
            daily_limit_usd=daily_limit_usd,
            max_tx_usd=max_tx_usd,
            expiry=expiry,
            allowed_destinations=allowed_destinations
        )

        # Master signs the bounds payload
        msg_hash = session.get_message_hash()
        signed_msg = owner_account.sign_message(msg_hash)
        session.owner_signature = signed_msg.signature.hex()

        logger.info(f"[SessionKeyManager] Registered session {session.session_address} for owner {owner_account.address}")
        return session
