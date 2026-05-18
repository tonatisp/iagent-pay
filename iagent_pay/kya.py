"""
iAgentPay — Know Your Agent (KYA)
Decentralized identity and trust verification for AI agents.
Uses DIDs (Decentralized Identifiers) and Verifiable Credentials.

Why KYA?
  - Prevents impersonation attacks between agents
  - Enables trust-based payment routing (pay trusted agents faster)
  - Regulatory compliance for enterprise deployments
  - Integrates with iAgentPay's ART Reputation System

Inspired by: Coinbase Agentic Wallets (TEE + MPC identity),
             W3C DID standard, Verifiable Credentials spec.

Usage:
    from iagent_pay.kya import AgentIdentity, KYARegistry

    # Create a verifiable agent identity
    identity = AgentIdentity.create(
        name="ResearchBot-7",
        owner_address="0xAlice...",
        capabilities=["web_search", "payments", "data_analysis"],
    )
    print(identity.did)  # did:iagent:0x1a2b3c...

    # Register and verify agents
    registry = KYARegistry()
    registry.register(identity)
    trust = registry.get_trust_level("did:iagent:0x1a2b3c...")
"""
import time
import hashlib
import secrets
import logging
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("iagentpay.kya")


class TrustLevel(Enum):
    """
    Trust levels for agents.
    Higher trust = faster payments, higher limits, less friction.
    """
    UNKNOWN    = 0   # Never seen before
    BASIC      = 1   # Self-registered, unverified
    VERIFIED   = 2   # Owner address confirmed on-chain
    TRUSTED    = 3   # Good ART score + verified + >10 successful tx
    ELITE      = 4   # Verified + ART >= 95 + KYA credential issued
    BLACKLISTED = -1 # Do not pay — flagged for fraud


@dataclass
class AgentCredential:
    """A verifiable credential issued to an agent."""
    credential_id: str
    issuer_did: str
    subject_did: str
    credential_type: str        # "PaymentCapability", "IdentityVerification", etc.
    issued_at: float
    expires_at: float
    claims: Dict[str, Any] = field(default_factory=dict)
    revoked: bool = False

    def is_valid(self) -> bool:
        return not self.revoked and time.time() < self.expires_at

    def to_dict(self) -> dict:
        return {
            "id":         self.credential_id,
            "issuer":     self.issuer_did,
            "subject":    self.subject_did,
            "type":       self.credential_type,
            "issued_at":  self.issued_at,
            "expires_at": self.expires_at,
            "claims":     self.claims,
            "valid":      self.is_valid(),
        }


class AgentIdentity:
    """
    Decentralized identity for an AI agent.
    Format: did:iagent:<fingerprint>
    """

    DID_METHOD = "iagent"

    def __init__(
        self,
        name: str,
        owner_address: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
    ):
        self.name           = name
        self.owner_address  = owner_address.lower()
        self.capabilities   = capabilities or []
        self.metadata       = metadata or {}
        self.created_at     = time.time()
        self.credentials:   List[AgentCredential] = []

        # Generate deterministic DID from owner + name + timestamp
        fingerprint = hashlib.sha256(
            f"{owner_address}{name}{self.created_at}".encode()
        ).hexdigest()[:32]
        self.did = f"did:{self.DID_METHOD}:{fingerprint}"

        # DID Document (W3C compliant)
        self.did_document = {
            "@context":    ["https://www.w3.org/ns/did/v1"],
            "id":          self.did,
            "created":     self.created_at,
            "controller":  owner_address,
            "service": [{
                "id":              f"{self.did}#iagentpay",
                "type":            "iAgentPayEndpoint",
                "serviceEndpoint": "https://agentpay.ai/resolve",
            }],
            "iAgentPay": {
                "name":         self.name,
                "capabilities": self.capabilities,
                "version":      "5.0.0",
            },
        }

    @classmethod
    def create(
        cls,
        name: str,
        owner_address: str,
        capabilities: Optional[List[str]] = None,
    ) -> "AgentIdentity":
        """Factory method to create a new agent identity."""
        identity = cls(name=name, owner_address=owner_address, capabilities=capabilities)
        logger.info(f"[KYA] Created identity: {identity.did} ({name})")
        return identity

    def add_credential(self, credential: AgentCredential):
        self.credentials.append(credential)

    def get_valid_credentials(self) -> List[AgentCredential]:
        return [c for c in self.credentials if c.is_valid()]

    def to_dict(self) -> dict:
        return {
            "did":          self.did,
            "name":         self.name,
            "owner":        self.owner_address,
            "capabilities": self.capabilities,
            "created_at":   self.created_at,
            "credentials":  len(self.get_valid_credentials()),
            "did_document": self.did_document,
        }


class KYARegistry:
    """
    On-memory registry of known agent identities and their trust levels.
    In production, this would persist to a database or on-chain registry.
    """

    # Weights for trust score calculation
    _TRUST_THRESHOLDS = {
        TrustLevel.ELITE:       95,
        TrustLevel.TRUSTED:     70,
        TrustLevel.VERIFIED:    40,
        TrustLevel.BASIC:       10,
        TrustLevel.UNKNOWN:     0,
    }

    def __init__(self):
        self._agents:      Dict[str, AgentIdentity]  = {}   # did → identity
        self._trust:       Dict[str, TrustLevel]     = {}   # did → trust
        self._art_scores:  Dict[str, float]          = {}   # did → ART score (0-100)
        self._tx_counts:   Dict[str, int]            = {}   # did → successful tx count
        self._blacklist:   set                       = set()

    def register(self, identity: AgentIdentity) -> bool:
        """Register an agent identity in the registry."""
        if identity.did in self._blacklist:
            logger.warning(f"[KYA] Blocked registration for blacklisted DID: {identity.did}")
            return False

        self._agents[identity.did]     = identity
        self._trust[identity.did]      = TrustLevel.BASIC
        self._art_scores[identity.did] = 50.0  # Start at 50/100
        self._tx_counts[identity.did]  = 0
        logger.info(f"[KYA] Registered: {identity.did} ({identity.name})")
        return True

    def resolve(self, did: str) -> Optional[AgentIdentity]:
        """Resolve a DID to an AgentIdentity."""
        return self._agents.get(did)

    def get_trust_level(self, did: str) -> TrustLevel:
        """Get the current trust level for an agent."""
        if did in self._blacklist:
            return TrustLevel.BLACKLISTED
        return self._trust.get(did, TrustLevel.UNKNOWN)

    def get_art_score(self, did: str) -> float:
        """Get the ART (Agent Reputation Token) score for an agent."""
        return self._art_scores.get(did, 0.0)

    def update_after_payment(self, did: str, success: bool, amount_usd: float):
        """
        Update trust metrics after a payment.
        Called by the payment flow to build agent reputation.
        """
        if did not in self._agents:
            return

        if success:
            self._tx_counts[did] = self._tx_counts.get(did, 0) + 1
            # Increase ART score (max 100)
            bonus = min(2.0, amount_usd * 0.1)
            self._art_scores[did] = min(100.0, self._art_scores.get(did, 50.0) + bonus)
        else:
            # Decrease ART score (min 0)
            penalty = 5.0
            self._art_scores[did] = max(0.0, self._art_scores.get(did, 50.0) - penalty)

        # Recalculate trust level
        self._recalculate_trust(did)

    def _recalculate_trust(self, did: str):
        """Recalculate trust level based on ART score and tx count."""
        art    = self._art_scores.get(did, 0)
        tx     = self._tx_counts.get(did, 0)

        if art >= 95 and tx >= 50:
            level = TrustLevel.ELITE
        elif art >= 70 and tx >= 10:
            level = TrustLevel.TRUSTED
        elif art >= 40:
            level = TrustLevel.VERIFIED
        else:
            level = TrustLevel.BASIC

        old_level = self._trust.get(did)
        if old_level != level:
            logger.info(f"[KYA] Trust upgrade: {did[:20]}... → {level.name} (ART:{art:.1f})")
            if level == TrustLevel.ELITE:
                self._mint_soulbound_token(did)
                
        self._trust[did] = level

    def _mint_soulbound_token(self, did: str):
        """
        Simulates minting an On-Chain Soulbound Token (NFT) to immortalize the agent's identity.
        In production, this would call a Smart Contract on Base or Solana.
        """
        agent = self._agents.get(did)
        if not agent:
            return
            
        tx_hash = f"0x_sbt_mint_{secrets.token_hex(16)}"
        logger.info(f"[KYA-OnChain] 🏆 Minting Soulbound Identity NFT for {agent.name}")
        logger.info(f"[KYA-OnChain] Transaction Hash: {tx_hash}")
        
        # We attach the claim to their credentials
        self.issue_credential(
            did, 
            credential_type="OnChainIdentitySBT", 
            claims={"tx_hash": tx_hash, "network": "BASE_MAINNET"}
        )

    def blacklist(self, did: str, reason: str = ""):
        """Blacklist an agent (blocks all future payments)."""
        self._blacklist.add(did)
        self._trust[did] = TrustLevel.BLACKLISTED
        logger.warning(f"[KYA] BLACKLISTED: {did} — {reason}")

    def issue_credential(
        self,
        subject_did: str,
        credential_type: str = "PaymentCapability",
        claims: Optional[dict] = None,
        valid_days: int = 365,
    ) -> Optional[AgentCredential]:
        """Issue a verifiable credential to an agent."""
        agent = self._agents.get(subject_did)
        if not agent:
            return None

        cred = AgentCredential(
            credential_id=f"cred_{secrets.token_hex(16)}",
            issuer_did="did:iagent:registry",
            subject_did=subject_did,
            credential_type=credential_type,
            issued_at=time.time(),
            expires_at=time.time() + (valid_days * 86400),
            claims=claims or {},
        )
        agent.add_credential(cred)
        logger.info(f"[KYA] Issued '{credential_type}' credential to {subject_did[:20]}...")
        return cred

    def get_full_report(self, did: str) -> dict:
        """Returns a full KYA report for an agent."""
        agent = self._agents.get(did)
        if not agent:
            return {"error": f"Unknown DID: {did}"}

        return {
            "did":         did,
            "name":        agent.name,
            "owner":       agent.owner_address,
            "trust_level": self.get_trust_level(did).name,
            "art_score":   round(self.get_art_score(did), 2),
            "tx_count":    self._tx_counts.get(did, 0),
            "credentials": [c.to_dict() for c in agent.get_valid_credentials()],
            "capabilities": agent.capabilities,
            "blacklisted": did in self._blacklist,
        }

    def get_registry_stats(self) -> dict:
        """Returns summary statistics of the registry."""
        trust_counts = {}
        for level in TrustLevel:
            trust_counts[level.name] = sum(
                1 for t in self._trust.values() if t == level
            )
        return {
            "total_agents":  len(self._agents),
            "blacklisted":   len(self._blacklist),
            "trust_distribution": trust_counts,
            "avg_art_score": round(
                sum(self._art_scores.values()) / max(1, len(self._art_scores)), 2
            ),
        }


# Global registry instance (singleton)
_global_registry: Optional[KYARegistry] = None


def get_registry() -> KYARegistry:
    """Get or create the global KYA registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = KYARegistry()
    return _global_registry
