from iagent_pay.agent_pay import AgentPay
from iagent_pay.wallet_manager import WalletManager
import time

def main():
    print("--- 🧾 Invoice Protocol Demo ---")
    
    # Setup Agents
    # Note: AgentPay manages wallet internally via WalletManager
    
    seller = AgentPay(chain_name="SOL_MAINNET")
    buyer = AgentPay(chain_name="SOL_MAINNET") # Self-pay for demo
    
    # 1. User Creates Invoice
    print("\n1️⃣  Seller Creating Invoice...")
    inv_json = seller.create_invoice(
        amount=50.0,
        currency="USDC",
        chain="SOL_MAINNET",
        description="AI Model Fine-Tuning Service (v2)"
    )
    print(f"📄 Invoice Generated:\n{inv_json}")
    
    # 2. Buyer Pays Invoice
    print("\n2️⃣  Buyer Paying Invoice...")
    try:
        tx = buyer.pay_invoice(inv_json)
        print(f"✅ Invoice Paid! Tx: {tx}")
    except Exception as e:
        print(f"❌ Payment Failed: {e}")

if __name__ == "__main__":
    main()
