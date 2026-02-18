from iagent_pay import AgentPay, WalletManager, ChainConfig
import time

from eth_account import Account

# 1. Setup
# For this demo, we use a fresh ephemeral wallet to avoid password prompts
wallet = Account.create()
print(f"🔐 Temporary Demo Wallet: {wallet.address}")

# Pass private key explicitly to override default wallet
agent = AgentPay(treasury_address=wallet.address, chain_name="LOCAL", private_key=wallet.key.hex(), daily_limit=1.0)

# Fund the wallet for the demo (Local Only)
genesis = agent.w3.eth.accounts[0]
agent.w3.eth.send_transaction({
    'from': genesis,
    'to': wallet.address,
    'value': agent.w3.to_wei(10, 'ether')
})
print("💰 Wallet funded with 10 ETH (Testnet)")

print(f"🛡️ Current Daily Limit: {agent.daily_limit} ETH\n")

# 2. Try to spend WITHIN limit
try:
    print("Attempting to send 0.5 ETH...")
    agent.pay_agent("0x1234567890123456789012345678901234567890", 0.5)
    print("✅ Success!")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n... Sending another 0.8 ETH (Total would be 1.3)...\n")

# 3. Try to EXCEED limit
try:
    agent.pay_agent("0x1234567890123456789012345678901234567890", 0.8)
    print("❌ DANGER: This should have failed!")
except ValueError as e:
    print(f"✅ BLOCKED BY GUARD: {e}")

# 4. Admin Override
print("\n🔧 Admin increasing limit to 5.0 ETH...")
agent.set_daily_limit(5.0)

try:
    agent.pay_agent("0x1234567890123456789012345678901234567890", 0.8)
    print("✅ Success! New limit worked.")
except Exception as e:
    print(f"❌ Still Failed: {e}")
