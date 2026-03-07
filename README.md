# 🤖 iAgentPay SDK v3.6 "Titan" (Production Ready)

**The Universal Banking & Payment Standard for AI Agents.**
*The most resilient, secure, and disruptive infrastructure for the autonomous economy.*

[![PyPI version](https://badge.fury.io/py/iagent-pay.svg)](https://badge.fury.io/py/iagent-pay)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🏛️ The Titan Difference
iAgentPay v3.6 is more than a wallet—it's a financial operating system for AI. Built following a **Level 7 "God Mode"** stress test, it is designed to survive total network failures and Sybil attacks.

| Feature | Titan Power |
| :--- | :--- |
| **Resilience** | **Self-Healing Pricing**: If Oracles fail, we fetch prices directly from On-Chain DEX pools. |
| **Trust Layer** | **Autonomous Reputation (ART)**: Agents rate each other. Trust scores are used for dynamic discounts. |
| **AI-Bank** | **Active Treasury**: Automated yield generation on Aave (Base) for idle funds. |
| **Cross-Chain** | **Dual-Engine**: Native drivers for EVM (Base, Polygon, ETH) and Solana (SPL tokens). |
| **God-Mode Secure**| **Multi-RPC Fallback**: Automatically rotates between pool of nodes to ensure 100% uptime. |

---

## 📦 Installation
```bash
pip install iagent-pay
```

---

## ⚡ Titan Quick Start

### 1. Robust Initialization
```python
from iagent_pay import AgentPay

# Multi-RPC fallback is active by default in Titan v3.6
agent = AgentPay(chain_name="BASE")
```

### 2. Trust-Based Pricing (Discounts!) 💎
Titan incentivizes good behavior. Agents with high trust scores automatically get discounts on payments.
```python
# Rate a peer agent after a good service
agent.rate_agent("0xRecipient...", 5.0)

# Future invoices to this recipient will apply a trust discount automatically
agent.pay_invoice(invoice_json)
```

### 3. Self-Healing Pricing 🏦
Never let a dead API stop your agent.
```python
# If Coinbase/Binance are down, Titan fetches prices from Uniswap v3 contracts
eth_price = agent.pricing.get_eth_price()
```

### 4. AI-Bank (Active Treasury) 🏦
```python
# Put idle USDC to work in Aave
agent.enable_auto_yield(protocol="aave")
agent.yield_manager.deposit("USDC", 100.0)
```

---

## 🛡️ Validation: The Nivel 7 Audit
iAgentPay v3.6 has been hardened through a simulated "God Mode" scenario:
- **Sybil Resistance:** Validated reputation integrity under 100+ bot attacks.
- **Blackout Recovery:** Verified 100% recovery after total RPC isolation.
- **Integrity Shield:** Rejection of malicious/corrupt state bundle injections.

---

## 📄 License
MIT License. Built for the Sovereign Agentic Future.
