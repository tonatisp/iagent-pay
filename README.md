# 🤖 iAgentPay SDK v1.0

**The Standard Payment Layer for Autonomous AI Agents.**

[![PyPI version](https://badge.fury.io/py/iagent-pay.svg)](https://badge.fury.io/py/iagent-pay)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AgentPay is a Python SDK designed to allow AI Agents (AutoGPT, LangChain, BabyAGI) to send and receive micropayments securely.

## 🚀 Features

*   **⚡ High-Frequency Trading:** Capable of 750+ transactions per minute.
*   **🔐 Military-Grade Security:** Encrypted JSON Keystores (AES-128).
*   **🔐 Military-Grade Security:** Encrypted JSON Keystores (AES-128).
*   **🌍 Multi-Chain Support (EVM):**
    *   ✅ **Ethereum** (Mainnet & Sepolia)
    *   ✅ **Base** (Coinbase L2)
    *   ✅ **Polygon** (Low fees)
    *   ✅ **Arbitrum** & **Optimism**
    *   🚧 *Solana (Coming Soon in v2.0)*
*   **🛡️ Reliability Engine:** Auto-manages Nonces and Gas Fees to prevent stuck transactions.
*   **🛡️ Reliability Engine:** Auto-manages Nonces and Gas Fees to prevent stuck transactions.
*   **💸 Dynamic Pricing:** Update your agent's service fees remotely without code changes.
*   **🎁 60-Day Free Trial:** Start building risk-free with our extended beta program.
*   **📊 Audit Logs:** Built-in SQLite transaction history.

## 📦 Installation

```bash
pip install iagent-pay
```

## ⚡ Quick Start

### 1. Initialize Wallet
```python
from iagent_pay import WalletManager

# Create or Load Wallet (Securely)
wm = WalletManager()
wallet = wm.get_or_create_wallet(password="SuperSecurePassword")
print(f"My Agent Address: {wallet.address}")
```

### 2. Send a Payment (Sepolia)
```python
from iagent_pay import AgentPay

# Connect to Sepolia (or BASE, POLYGON, LOCAL)
agent = AgentPay(wallet, chain_name="SEPOLIA")

# Pay another agent 0.001 ETH
tx_hash = agent.pay_agent(
    recipient_address="0x123...", 
    amount=0.001, 
    wait=True  # Wait for confirmation
)

print(f"Payment Successful! Hash: {tx_hash}")
```

### 3. High-Frequency Mode (No Waiting)
```python
# Send 10 payments instantly
for i in range(10):
    agent.pay_agent("0x123...", 0.0001, wait=False)
```

## 🛠️ Configuration

To enable remote pricing updates, create a `pricing_config.json` locally or host it online:

```json
{
  "trial_days": 14,
  "subscription_price_eth": 0.01
}
```

```python
from iagent_pay import PricingManager

pm = PricingManager(config_url="https://mysite.com/pricing.json")
price = pm.get_config()['subscription_price_eth']
```

## 📄 License
MIT
