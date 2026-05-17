"""
iAgentPay — Sub-Agents
Create child agents with independent budgets, API keys, and billing.
Enterprise feature inspired by AgentPayment.network and Coinbase Agentic Wallets.

Use cases:
  - Multi-agent teams where each specialist has its own spending limit
  - Delegated spending: parent agent spawns sub-agents for tasks
  - Audit trail: each sub-agent has isolated transaction history

Usage:
    from iagent_pay.sub_agents import SubAgentManager

    manager = SubAgentManager(master_budget_usd=500.0)

    # Create sub-agents
    researcher = manager.create("researcher", daily_limit_usd=20.0)
    writer     = manager.create("writer",     daily_limit_usd=10.0)

    # Use sub-agent's safety kernel
    researcher.kernel.check(amount=5.0, recipient="0xDataAPI...")
    researcher.spend(5.0, "USDC", "Paid for data API")

    # Parent can pause/terminate sub-agents
    manager.pause("researcher")
    manager.get_status()
"""
import time
import threading
import logging
import secrets
from typing import Optional, Dict, List
from dataclasses import dataclass, field

from .safety_kernel import SafetyKernel, SafetyConfig

logger = logging.getLogger("iagentpay.sub_agents")


@dataclass
class SubAgentConfig:
    name: str
    daily_limit_usd: float = 10.0
    weekly_limit_usd: float = 50.0
    session_limit_usd: float = 5.0
    max_tx_usd: float = 2.0
    max_tx_per_minute: int = 5
    allowed_recipients: List[str] = field(default_factory=list)


class SubAgent:
    """
    An isolated child agent with its own budget, API key, and transaction history.
    """

    def __init__(self, config: SubAgentConfig, parent_name: str = "master"):
        self.name        = config.name
        self.parent_name = parent_name
        self.api_key     = f"iap_sub_{secrets.token_urlsafe(24)}"
        self.created_at  = time.time()
        self.is_active   = True
        self.kernel      = SafetyKernel(SafetyConfig(
            daily_limit_usd=config.daily_limit_usd,
            weekly_limit_usd=config.weekly_limit_usd,
            session_limit_usd=config.session_limit_usd,
            max_tx_usd=config.max_tx_usd,
            max_tx_per_minute=config.max_tx_per_minute,
            allowed_recipients=config.allowed_recipients,
        ))
        self._tx_history: list = []
        self._lock = threading.Lock()

    def spend(self, amount: float, currency: str = "USDC",
              description: str = "", recipient: str = "unknown") -> bool:
        """
        Record a spend for this sub-agent (after payment is made).
        Returns True if recorded successfully.
        """
        if not self.is_active:
            logger.warning(f"[SubAgent:{self.name}] Attempted spend on paused agent.")
            return False

        with self._lock:
            self._tx_history.append({
                "timestamp":   time.time(),
                "amount":      amount,
                "currency":    currency,
                "description": description,
                "recipient":   recipient,
            })
        logger.info(f"[SubAgent:{self.name}] Spent {amount} {currency}: {description}")
        return True

    def pause(self):
        """Pause this sub-agent (blocks new spends)."""
        self.is_active = False
        logger.info(f"[SubAgent:{self.name}] Paused.")

    def resume(self):
        """Resume a paused sub-agent."""
        self.is_active = True
        logger.info(f"[SubAgent:{self.name}] Resumed.")

    def get_status(self) -> dict:
        """Returns full status of this sub-agent."""
        kernel_status = self.kernel.get_status()
        return {
            "name":       self.name,
            "parent":     self.parent_name,
            "is_active":  self.is_active,
            "api_key":    f"{self.api_key[:12]}...{self.api_key[-4:]}",  # Masked
            "created_at": self.created_at,
            "tx_count":   len(self._tx_history),
            "kernel":     kernel_status,
        }

    def get_history(self, limit: int = 20) -> list:
        """Returns transaction history for this sub-agent."""
        return self._tx_history[-limit:]


class SubAgentManager:
    """
    Manages a fleet of sub-agents with a shared master budget.
    The master budget is the total across ALL sub-agents.
    """

    def __init__(self, master_budget_usd: float = 100.0, master_name: str = "master"):
        self.master_name       = master_name
        self.master_budget_usd = master_budget_usd
        self._agents: Dict[str, SubAgent] = {}
        self._lock = threading.Lock()

    def create(
        self,
        name: str,
        daily_limit_usd: float = 10.0,
        weekly_limit_usd: float = 50.0,
        session_limit_usd: float = 5.0,
        max_tx_usd: float = 2.0,
        allowed_recipients: Optional[List[str]] = None,
    ) -> SubAgent:
        """
        Create a new sub-agent.

        Args:
            name:               Unique name for this sub-agent
            daily_limit_usd:    Max daily spend
            weekly_limit_usd:   Max weekly spend
            session_limit_usd:  Max per-session spend
            max_tx_usd:         Max per single transaction
            allowed_recipients: Whitelist of allowed recipient addresses

        Returns:
            SubAgent instance ready to use
        """
        config = SubAgentConfig(
            name=name,
            daily_limit_usd=daily_limit_usd,
            weekly_limit_usd=weekly_limit_usd,
            session_limit_usd=session_limit_usd,
            max_tx_usd=max_tx_usd,
            allowed_recipients=allowed_recipients or [],
        )
        agent = SubAgent(config=config, parent_name=self.master_name)
        with self._lock:
            self._agents[name] = agent
        logger.info(
            f"[SubAgentManager] Created sub-agent '{name}' "
            f"(daily: ${daily_limit_usd}, tx_cap: ${max_tx_usd})"
        )
        return agent

    def get(self, name: str) -> Optional[SubAgent]:
        """Get a sub-agent by name."""
        return self._agents.get(name)

    def pause(self, name: str) -> bool:
        """Pause a sub-agent by name."""
        agent = self._agents.get(name)
        if agent:
            agent.pause()
            return True
        return False

    def resume(self, name: str) -> bool:
        """Resume a paused sub-agent."""
        agent = self._agents.get(name)
        if agent:
            agent.resume()
            return True
        return False

    def terminate(self, name: str) -> bool:
        """Permanently remove a sub-agent."""
        with self._lock:
            if name in self._agents:
                del self._agents[name]
                logger.info(f"[SubAgentManager] Terminated sub-agent '{name}'")
                return True
        return False

    def get_total_spent(self) -> float:
        """Returns total USD spent across ALL sub-agents."""
        total = 0.0
        for agent in self._agents.values():
            status = agent.kernel.get_status()
            total += status.get("session_spent", 0.0)
        return round(total, 4)

    def get_status(self) -> dict:
        """Returns status of master and all sub-agents."""
        total_spent = self.get_total_spent()
        return {
            "master_name":       self.master_name,
            "master_budget_usd": self.master_budget_usd,
            "total_spent_usd":   total_spent,
            "remaining_usd":     round(self.master_budget_usd - total_spent, 4),
            "sub_agents":        [a.get_status() for a in self._agents.values()],
            "active_count":      sum(1 for a in self._agents.values() if a.is_active),
            "total_count":       len(self._agents),
        }

    def list_agents(self) -> List[str]:
        """Returns names of all sub-agents."""
        return list(self._agents.keys())
