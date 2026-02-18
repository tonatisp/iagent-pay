# 📋 GitHub & PyPI Metadata (v2.1.0)
# 📋 GitHub & PyPI Metadata (v2.1.1)

Copy and paste these details into your project settings.

## 1. GitHub Repository Settings


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
