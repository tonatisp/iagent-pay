# 🚀 Release Notes: iAgentPay v2.1.0-beta (USDC SPL)

**"The Stablecoin Update"**

Following the massive V2.0 architectural shift, we are proud to enable **USDC on Solana**.

---

## 🌟 New Features

### 1. Solana SPL Token Support
You can now send stablecoins on Solana with the same ease as on Ethereum.
*   **Method:** `agent.pay_token(recipient, amount, token="USDC")`
*   **Automatic ATA Management:** The SDK automatically detects if the recipient needs an Associated Token Account (ATA) and creates it if necessary (idempotent).
*   **Decimals:** Handling of 6 decimals for USDC is automatic.

### 2. Verified Mint Addresses
The SDK comes pre-configured with official Mint Addresses:
*   **Mainnet:** `EPjFWdd...` (Circle Official)
*   **Devnet:** `4zMMC9...` (Standard Devnet USDC)

---

## 🛠 Usage Guide

```python
from iagent_pay.agent_pay import AgentPay

# 1. Initialize (Devnet)
agent = AgentPay(chain_name="SOL_DEVNET")

# 2. Check USDC Balance
# (Currently via driver directly)
bal = agent.solana.get_token_balance()
print(f"USDC: {bal}")

# 3. Pay Agent
# Generates "Create ATA" + "Transfer" instructions automatically
tx = agent.pay_token("GuiQKy...Recipient", amount=10.0, token="USDC")
print(f"Tx: {tx}")
```

---

## ⚠️ Known Limitations
*   **Gas (Rent):** Creating an ATA for a new recipient costs ~0.002 SOL. Ensure your wallet has SOL, not just USDC.
*   **Mock Pricing:** The USD value of SOL transaction fees is not yet tracked in the `usage_history.db`.

---

## 🔮 What's Next?
*   **Unified Pricing Oracle:** Real-time SOL price feeds.
*   **Swap Integration:** Jupiter Aggregator integration for swapping SOL <-> USDC.
