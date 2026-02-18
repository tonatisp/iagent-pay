# 📋 GitHub & PyPI Metadata (v2.1.0)

Copy and paste these details into your project settings.

## 1. GitHub Repository Settings

**About / Description:**
> The Universal Payment Standard for AI Agents. Now with "Dual-Core" engine (EVM + Solana), Social Tipping, and Auto-Swaps.

**Website:**
> https://agentpay.ai (or your landing page)

**Topics / Tags:**
> `ai-agents` `payment-sdk` `solana` `ethereum` `defi` `web3` `memecoins` `python`

---

## 2. GitHub Release (Create New Release)

**Tag version:** `v2.1.0`
**Release Title:** `v2.1.0 - The Universal Update (EVM + Solana)`

**Description (Paste this):**
```markdown
## 🚀 iAgentPay v2.1.0 (The "Universal" Update)

**iAgentPay is now multi-chain.** This release introduces the "Dual-Core" engine, allowing agents to operate seamlessly on both **EVM (Ethereum/Base/Polygon)** and **SVM (Solana)** networks simultaneously.

### ✨ New Features
*   **🟣 Solana Support (Beta):** Native SOL transfers and SPL Token support (USDC, BONK, WIF).
*   **🎁 Social Tipping:** Resolve ENS (`.eth`) and SNS (`.sol`) handles automatically.
*   **🔄 Auto-Swap Engine:** Built-in method `agent.swap("SOL", "BONK")` to exchange assets on-chain.
*   **🧾 Invoice Protocol (AIP-1):** Standardized JSON protocol for Agent-to-Agent billing.
*   **⛽ Gas Guardrails:** Protects agents from high fees.

### 📦 Installation
```bash
pip install iagent-pay==2.1.0
```

### 📄 Full Changelog
See `RELEASE_NOTES_v2.1.0.md` for details.
```

---

## 3. PyPI Update Command

You have already built the package. To push this description to PyPI:

```bash
twine upload dist/iagent_pay-2.1.0*
```
*(Requires your PyPI username/password or token)*
