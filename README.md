# 🤖 iAgentPay SDK v2.1 (Beta)

**The Universal Payment Standard for AI Agents.**
*Build autonomous agents that can Buy, Sell, Swap, and Tip across any blockchain.*

[![PyPI version](https://badge.fury.io/py/iagent-pay.svg)](https://badge.fury.io/py/iagent-pay)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Why iAgentPay?
Most crypto SDKs are too complex for AI. **iAgentPay** abstracts 1000s of lines of blockchain code into simple English commands.

*   ✅ **Multi-Chain:** Ethereum, Base, Polygon, **Solana**.
*   ✅ **Universal Tokens:** Pay in ETH, SOL, USDC, USDT, BONK, PEPE.
*   ✅ **Social Tipping:** `agent.pay("vitalik.eth", 10)`
*   ✅ **Auto-Swap:** `agent.swap("SOL", "BONK")` (DeFi Integration).
*   ✅ **Gas Guardrails:** Protect your agent from high fees.

---

## 📦 Installation

```bash
pip install iagent-pay
```

---

## ⚡ Quick Start

### 1. Initialize (Dual-Core Engine)
```python
from iagent_pay import AgentPay, WalletManager

# Create Wallet (Auto-Saved securely)
wm = WalletManager()
wallet = wm.get_or_create_wallet(password="MySecurePassword")

# 🟢 Connect to Base (L2 - Fast & Cheap)
agent_evm = AgentPay(wallet, chain_name="BASE")

# 🟣 Connect to Solana (High Frequency)
agent_sol = AgentPay(wallet, chain_name="SOL_MAINNET")
```

### 2. Simple Payments (The "Hello World")
```python
# Pay 0.01 ETH on Base
agent_evm.pay_agent("0x123...", 0.01)

# Pay 0.1 SOL on Solana
agent_sol.pay_agent("4jjCQ...", 0.1)
```

### 3. Retail & Memecoins (New in v2.1!) 🐕
Don't worry about contract addresses. We handle them.
```python
# Send USDC (Stablecoin)
agent_evm.pay_token("CLIENT_ADDRESS", 100.0, token="USDC")

# Send BONK (Meme - Solana)
agent_sol.pay_token("FRIEND_ADDRESS", 1000.0, token="BONK")

# Send PEPE (Meme - Ethereum)
agent_evm.pay_token("DEGEN_ADDRESS", 5000.0, token="PEPE")
```

### 4. Social Tipping 🎁
Human-readable names auto-resolve to addresses.
```python
# Resolves .eth (ENS) or .sol (SNS)
agent_evm.pay_agent("vitalik.eth", 0.05)
agent_sol.pay_token("tobby.sol", 50.0, token="USDC")
```

### 5. Auto-Swap (DeFi) 🔄
Agent earning in SOL but wants to hold BONK?
```python
# Buys BONK with 1 SOL instantly
result = agent_sol.swap(input="SOL", output="BONK", amount=1.0)
print(f"Swapped! Hash: {result['tx_hash']}")
```

---

## 🛡️ Business Features

### Dynamic Pricing
Update your agent's service fees remotely without redeploying code.
```python
from iagent_pay import PricingManager
pm = PricingManager("https://api.myagent.com/pricing.json")
fee = pm.get_price()
```

### Gas Guardrails ⛽
Prevent your agent from burning money when the network is congested.
```python
# Aborts if Gas > 20 Gwei
try:
    agent_evm.pay_agent("Bob", 0.1, max_gas_gwei=20)
except ValueError:
    print("Gas too high, sleeping...")
```

---

## 🛠️ Configuration
Dual-Treasury support for collecting fees in both ecosystems.
**`pricing_config.json`**:
```json
{
  "treasury": {
      "EVM": "0xYourEthWallet...",
      "SOLANA": "YourSolanaWallet..."
  },
  "trial_days": 60,
  "subscription_price_usd": 26.00
}
```

---

## 📄 License
MIT License. Built for the Agent Economy.
