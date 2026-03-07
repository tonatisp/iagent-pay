# 🤖 Reddit Post: r/Python & r/LocalLLaMA

**Title:** I built a "Circuit Breaker" for AI Agents so they don't drain your wallet. (Open Source)

**Body:**
Hey guys,
I've been building autonomous agents recently, and one fear always stopped me from giving them a crypto wallet: **Prompt Injection.**

If an agent gets tricked (or hallucinates), it could empty the entire wallet in one transaction.

So I built **iAgentPay v2.1** - A Python SDK that acts as a financial banking layer for AI.

### 🛡️ The "Capital Guard" Feature
Unlike a standard Web3 wrapper, this SDK enforces a **Daily Spending Limit** locally.
```python
# Even if the LLM decides to send 100 ETH...
agent = AgentPay(wallet, daily_limit=10.0)

# ...the SDK blocks it automatically.
# Raises: 🚨 Security Alert: Daily Limit Exceeded!
```

### ⚡ Other Features
*   **Dual-Chain:** Operates on Ethereum (EVM) and Solana (SVM) with one class.
*   **B2B Invoicing:** Implements **AIP-1** (Agent Invoice Protocol) so agents can bill each other via JSON.
*   **Auto-Swap:** Integrated with Jupiter/Uniswap logic to swap tokens programmatically.

It's fully open source and available on PyPI.
`pip install iagent-pay`

I'd love to hear what you think about the security architecture!

**Repo:** [Link]
**Docs:** [Link]
