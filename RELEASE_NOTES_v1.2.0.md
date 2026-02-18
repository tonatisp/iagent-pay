# 🚀 iAgentPay v1.2.0: The "Universal" Update

**Release Date:** Feb 17, 2026
**Tagline:** "The First Multi-Chain, Multi-Asset Treasury for AI Agents."

---

## 🌟 What's Same?
We kept the simple, intuitive API you love:
```python
agent.pay("0xRecipient...", 25.0, token="USDC")
```

## 🆕 What's New?
This is our biggest update yet, transforming `iagent-pay` from a niche ETH tool into a global financial layer.

### 1. 🌍 BNB Chain Support
We have added full support for the **Binance Smart Chain (BSC)**.
*   **Why?** Extremely low fees ($0.03) and massive liquidity.
*   **Chain ID:** 56
*   **Assets:** BNB, BUSD (via USDT wrapper), DAI.

### 2. 💵 The "Big 5" Stablecoins
Your Agents are no longer exposed to crypto volatility. We now natively support:
*   **USDC (USD Coin):** The standard for regulated business.
*   **USDT (Tether):** The king of volume.
*   **DAI:** Decentralized, censorship-resistant dollars.
*   **EURC (Euro Coin):** For our European agents/markets.
*   **WETH (Wrapped Ether):** For DeFi interoperability.

### 3. 🛡️ Robust Pricing Oracle V2
Using a single price source is risky. v1.2.0 introduces **Triangulated Pricing**:
*   We query **CoinGecko + Coinbase + Binance** simultaneously.
*   We take the **Median** price.
*   **Benefit:** If one API fails or lies, your subscription price remains accurate. 100% uptime design.

### 4. 🔒 Enterprise Security Hardening
*   **Global Registry:** Prevents "Trial Reset" exploits by tracking machine ID fingerprints locally.
*   **Strict Typing:** Enhanced error handling for invalid addresses.

---

## 📦 How to Upgrade
```bash
pip install --upgrade iagent-pay
```

## 📢 Community
*   **GitHub:** [github.com/tonatisp/iagent-pay](https://github.com/tonatisp/iagent-pay)
*   **Docs:** [tonatisp.github.io/iagent-pay](https://tonatisp.github.io/iagent-pay/)
