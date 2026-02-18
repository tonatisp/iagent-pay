# 🛡️ iAgentPay v2.1.1: Security Hardening Release

This patch release focuses on **Operational Security** and **B2B Capabilities**.

## 🌟 New Features
*   **Capital Guard:** Daily spending limits for ETH/SOL to prevent wallet draining.
    *   `agent = AgentPay(..., daily_limit=10.0)`
    *   Blocks transactions if the 24h rolling limit is exceeded.
*   **Billing Protocol (AIP-1):** Standardized Invoicing.
    *   `agent.create_invoice(...)` and `agent.pay_invoice(...)`.
*   **Documentation:** Comprehensive `README.md` now acts as the Master Manual.

## 🐛 Bug Fixes
*   **Replay Attack:** Fixed a vulnerability where invoices could be paid multiple times.
*   **Solana Resolver:** Fixed case-sensitivity issue for base58 addresses.
*   **RPC Privacy:** prioritizing `ETH_RPC_URL` and `SOLANA_RPC_URL` env vars.

## 📦 Upgrade
```bash
pip install iagent-pay --upgrade
```
