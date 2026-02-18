"""
Example 2: Solana & Memecoins
Use this to pay in SOL or Tokens (USDC, BONK, WIF).
"""
from iagent_pay import AgentPay, WalletManager

wm = WalletManager()
wallet = wm.get_or_create_wallet()

# 1. Connect to Solana
agent = AgentPay(wallet, chain_name="SOL_MAINNET")

print(f"☀️ Solana Address: {agent.my_address}")

# 2. Send SOL
agent.pay_agent("4jjCQ...", 0.1)

# 3. Send BONK (Meme)
# No need to look up contract addresses!
agent.pay_token("4jjCQ...", 1000.0, token="BONK")

# 4. Social Tipping
# Send to a .sol handle
agent.pay_token("tobby.sol", 50.0, token="USDC")
