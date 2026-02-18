# 🧾 Agent-to-Agent Invoice Protocol (AIP-1)

## Purpose
To allow two autonomous agents to negotiate services.
**Scenario:** Agent A (Research) asks Agent B (GPU) for compute. Agent B sends an **Invoice**. Agent A pays it.

## JSON Schema
Every invoice is a JSON object signed by the issuer.

```json
{
  "protocol": "iagent-pay/v1",
  "invoice_id": "inv_890234...",
  "created_at": 1708123456,
  "expires_at": 1708127056,
  "recipient": "vitalik.eth", 
  "items": [
    {
      "description": "GPU Compute (H100) - 1 Hour",
      "quantity": 1,
      "unit_price": 2.50
    }
  ],
  "total_amount": 2.50,
  "currency": "USDC",
  "chain": "BASE",
  "memo": "Training Model v4"
}
```

## Implementation Strategy
We will add `InvoiceManager` to the SDK.

### 1. Create Invoice
```python
invoice = agent.create_invoice(
    amount=10.0,
    currency="USDC",
    chain="SOL_MAINNET",
    description="Research Report on Quantum Computing"
)
# Returns JSON string
```

### 2. Pay Invoice
```python
agent.pay_invoice(invoice_json)
# Auto-parses JSON, validates expiry, and executes payment
```
