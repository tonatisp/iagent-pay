# 🚀 Release Notes: iAgentPay v2.0.0-alpha (Solana Edition)

**"The Dual-Core Update"**

This release marks the biggest architectural shift in `iagent-pay` history. We have moved from an EVM-only SDK to a **Chain-Agnostic** payment rail for AI Agents.

---

## 🌟 New Features

### 1. Solana (SVM) Support
The SDK now natively speaks the Solana protocol.
*   **New Driver:** `iagent_pay.solana_driver` handles Ed25519 signing and RPC comms.
*   **Dual-Core Engine:** `AgentPay` automatically switches between `Web3.py` (EVM) and `Solders` (Solana) based on the `chain_name` argument.
*   **Separate Wallets:** Automatically manages a separate `solana_id.json` keystore for your Agent's SOL funds.

### 2. Auto-Airdrop (Devnet)
The new driver includes a helper `agent.solana.request_airdrop(1.0)` to instantly fund test wallets (subject to network availability).

---

## 🛠 Usage Guide

### Install Dependencies
You must install the new Rust-based libraries:
```bash
pip install solana solders
```

### Code Example
```python
from iagent_pay.agent_pay import AgentPay

# 1. Initialize for Solana
agent = AgentPay(chain_name="SOL_DEVNET")

# 2. Check Balance
print(f"Balance: {agent.get_balance()} SOL")

# 3. Pay Agent
tx = agent.pay_agent("B1tCoin...Recip1ent", amount=0.01)
print(f"Tx: {tx}")
```

---

## ⚠️ Known Limitations (Alpha)
*   **No SPL Tokens Yet:** `pay_token()` raises `NotImplementedError` on Solana. Currently only native SOL transfers are supported.
*   **Devnet Conjestion:** The public Solana Faucet fails frequently (Error 429). Use `SOL_TESTNET` or fund manually if this happens.
*   **Pricing Oracle:** The USD conversion logic currently uses a hardcoded placeholder for SOL price.
