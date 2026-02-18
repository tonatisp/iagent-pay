"""
Example 1: Basic ETH Payment (EVM)
Use this to pay another agent on Ethereum, Base, or Polygon.
"""
from iagent_pay import AgentPay, WalletManager

# 1. Load Wallet
wm = WalletManager()
# To create a new wallet, run: wm.get_or_create_wallet("password")
wallet = wm.get_or_create_wallet() 

# 2. Connect to Base (Fast & Cheap)
agent = AgentPay(wallet, chain_name="BASE")

print(f"🤖 Agent Address: {agent.my_address}")
print(f"💰 Balance: {agent.get_balance()} ETH")

# 3. Pay Recipient
recipient = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e" # Example
try:
    tx = agent.pay_agent(recipient, 0.0001)
    print(f"✅ Payment Sent! Hash: {tx}")
except Exception as e:
    print(f"❌ Payment Failed: {e}")
