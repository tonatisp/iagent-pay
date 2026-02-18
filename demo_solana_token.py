import sys
import os
sys.path.insert(0, os.path.abspath("."))

from iagent_pay.agent_pay import AgentPay
import iagent_pay
print(f"📦 iAgentPay Source: {iagent_pay.__file__}")

def main():
    print("\n--- ☀️ iAgentPay V2.0: SPL Token Demo ---\n")

    # 1. Initialize
    try:
        agent = AgentPay(chain_name="SOL_DEVNET")
    except ImportError as e:
        print(f"❌ Error: {e}")
        return

    print(f"🤖 Agent: {agent.my_address}")
    
    # 2. Check USDC Balance
    # Note: We haven't exposed 'get_token_balance' in AgentPay yet directly, 
    # but we can access it via the driver.
    try:
        usdc_bal = agent.solana.get_token_balance()
        print(f"💰 USDC Balance: {usdc_bal}")
    except Exception as e:
        print(f"⚠️ Could not fetch balance (No ATA?): {e}")

    # 3. Attempt Transfer
    # Use a real valid address (random generated) to pass Base58 check
    recipient = "GuiQKyJ9J2X8U7QkQ7QkQ7QkQ7QkQ7QkQ7QkQ7QkQ7Qk" 
    print(f"🚀 Sending 10 USDC to {recipient[:8]}...")
    
    try:
        # Expected to fail if no funds
        tx = agent.pay_token(recipient, amount=10.0, token="USDC")
        print(f"✅ Success! Tx: {tx}")
    except Exception as e:
        print(f"❌ Transfer Failed (Expected if 0 balance): {e}")

if __name__ == "__main__":
    main()
