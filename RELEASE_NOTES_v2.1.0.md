# 🚀 Release Notes: iAgentPay v2.1.0 (The "Universal" Update)

## Headline
**iAgentPay is now multi-chain.** This release introduces the "Dual-Core" engine, allowing agents to operate seamlessly on both **EVM (Ethereum/Base/Polygon)** and **SVM (Solana)** networks simultaneously.

## ✨ New Features
*   **🟣 Solana Support (Beta):** Native SOL transfers and SPL Token support (USDC, BONK, WIF).
*   **🎁 Social Tipping:** Resolve ENS (`.eth`) and SNS (`.sol`) handles automatically.
*   **🔄 Auto-Swap Engine:** Built-in method `agent.swap("SOL", "BONK")` to exchange assets on-chain (integrates with Jupiter/Uniswap logic).
*   **🧾 Invoice Protocol (AIP-1):** Standardized JSON protocol for Agent-to-Agent billing (`create_invoice` / `pay_invoice`).
*   **⛽ Gas Guardrails:** Protects agents from high fees with `max_gas_gwei` parameter.

## 🛠️ API Changes
*   **New:** `AgentPay(chain_name="SOL_MAINNET")` initializes the Solana driver.
*   **New:** `agent.pay_token(token="BONK")` automatically finds the correct mint address.
*   **New:** `iagent_pay.invoice_manager` module added.

## 🐛 Bug Fixes
*   Fixed `AttributeError` in legacy `WalletManager` usage.
*   Fixed indentation error in `pay_token` retry logic.
*   Fixed case-sensitivity issue in `SocialResolver` that corrupted Solana addresses.

## 📦 Contributors
*   Rafix @ iAgent Team
