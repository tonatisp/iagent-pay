try:
    from langchain.tools import BaseTool
except ImportError:
    # Minimal fallback for type hinting if langchain is not installed
    class BaseTool: pass

from typing import Optional, Type, Any
from pydantic import BaseModel, Field
from iagent_pay.agent_pay import AgentPay

class PayToolInput(BaseModel):
    recipient: str = Field(description="The wallet address of the recipient (EVM or Solana)")
    amount: float = Field(description="The amount of native tokens (ETH/SOL) to send")
    chain: Optional[str] = Field(default="BASE", description="The blockchain to use (e.g., BASE, SOLANA, POLYGON)")
    token: Optional[str] = Field(default=None, description="Optional: Symbol of the token to send (e.g., USDC, USDT)")

class iAgentPayTool(BaseTool):
    name = "iagent_pay_tool"
    description = "Useful for sending crypto payments to other agents or services. Supports ETH, SOL, XRP and Stablecoins."
    args_schema: Type[BaseModel] = PayToolInput
    
    # Instance of the SDK
    agent: Optional[AgentPay] = None

    def __init__(self, agent: Optional[AgentPay] = None, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent or AgentPay()

    def _run(self, recipient: str, amount: float, chain: str = "BASE", token: Optional[str] = None) -> str:
        """Use the tool."""
        try:
            # Shift chain if needed
            if chain.upper() != self.agent.chain_name:
                self.agent = AgentPay(chain_name=chain.upper())
            
            if token:
                tx = self.agent.pay_token(recipient, amount, token=token)
            else:
                tx = self.agent.pay_agent(recipient, amount)
            
            return f"✅ Payment Successful! Transaction Hash: {tx}"
        except Exception as e:
            return f"❌ Payment Failed: {str(e)}"

    async def _arun(self, *args, **kwargs) -> str:
        """Use the tool asynchronously."""
        # For now, we fallback to sync
        return self._run(*args, **kwargs)
