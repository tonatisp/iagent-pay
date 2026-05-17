"""
iAgentPay — CrewAI Integration
Native payment tool for CrewAI multi-agent systems.

Usage:
    from iagent_pay.integrations.crewai import iAgentPayCrewTool
    from crewai import Agent, Task, Crew

    pay_tool = iAgentPayCrewTool(chain="BASE", max_amount_usdc=5.0)

    treasurer = Agent(
        role="Treasurer",
        goal="Manage payments between crew members",
        tools=[pay_tool],
    )
"""
import os
from typing import Optional, Type

try:
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field

    class PaymentInput(BaseModel):
        to_address: str = Field(..., description="Recipient wallet address")
        amount: float   = Field(..., description="Amount to send")
        currency: str   = Field(default="USDC", description="Currency: USDC, ETH, SOL, XRP")
        memo: str       = Field(default="", description="Optional payment memo")

    class iAgentPayCrewTool(BaseTool):
        """
        CrewAI tool that gives any agent the ability to send payments.
        Supports USDC (Base), ETH, SOL, and XRP.
        """
        name: str = "iAgentPay Payment Tool"
        description: str = (
            "Send crypto payments to any address. Supports USDC on Base (fastest, cheapest), "
            "ETH, SOL, and XRP. Use when you need to pay for services or settle invoices."
        )
        args_schema: Type[BaseModel] = PaymentInput

        def __init__(self, chain: str = "BASE", max_amount_usdc: float = 10.0, **kwargs):
            super().__init__(**kwargs)
            self._chain = chain
            self._max_amount = max_amount_usdc

        def _run(self, to_address: str, amount: float,
                 currency: str = "USDC", memo: str = "") -> str:
            if amount > self._max_amount:
                return (f"❌ Payment blocked: {amount} {currency} exceeds "
                        f"max_amount_usdc={self._max_amount}")
            try:
                if currency == "USDC":
                    from iagent_pay.usdc_driver import USDCDriver
                    driver = USDCDriver(network=f"{self._chain}_SEPOLIA")
                    result = driver.send(os.getenv("ETH_PRIVATE_KEY", ""), to_address, amount)
                else:
                    from iagent_pay.agent_pay import AgentPay
                    agent  = AgentPay()
                    result = agent.send_payment(to_address=to_address, amount=amount, chain=currency)
                return (f"✅ Payment sent: {amount} {currency} → {to_address[:10]}...\n"
                        f"TX: {result.get('tx_hash', 'N/A')}\nMemo: {memo or 'none'}")
            except Exception as e:
                return f"❌ Payment failed: {str(e)}"

    CREWAI_AVAILABLE = True

except ImportError:
    CREWAI_AVAILABLE = False

    class iAgentPayCrewTool:  # type: ignore
        """Stub when CrewAI is not installed."""
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "CrewAI not installed. Run: pip install crewai\n"
                "Then: from iagent_pay.integrations.crewai import iAgentPayCrewTool"
            )
