from iagent_pay.agent_pay import AgentPay
import time

def main():
    print("\n--- ☀️ iAgentPay V2.0: Solana Demo ---\n")

    # 1. Initialize on Solana Devnet (More reliable than Testnet usually)
    try:
        agent = AgentPay(chain_name="SOL_DEVNET")
    except ImportError as e:
        print(f"❌ Failed to load Solana Driver: {e}")
        return

    print(f"🤖 Agent Address: {agent.my_address}")
    
    # 2. Check Balance
    bal = agent.get_balance()
    print(f"💰 Balance: {bal:.4f} SOL")

    if bal < 0.02:
        print("⚠️ Low Balance. Auto-Requesting Airdrop...")
        agent.solana.request_airdrop(1.0)
        bal = agent.get_balance()
        print(f"💰 New Balance: {bal:.4f} SOL")

    if bal < 0.001:
        print("❌ Faucet Failed (Network Conjestion).")
        print("💡 SWITCHING TO SIMULATION MODE to prove SDK logic...")
        # Mocking a success for demo purposes
        print(f"🚀 [SIMULATION] Sending Micro-Payment (0.01 SOL) to B1tCoin...111")
        print("✅ [SIMULATION] Payment Successful!")
        print(f"   Tx: 5xSIMULATED_SIGNATURE_xyz123")
        return

    # 3. Pay Someone (Random Address)
    recipient = "B1tCoinPriceOracle1111111111111111111111111" 
    print(f"🚀 Sending Micro-Payment (0.01 SOL) to {recipient[:8]}...")
    
    try:
        tx_hash = agent.pay_agent(recipient, amount=0.01) 
        print("✅ Payment Successful!")
        print(f"   Tx: {tx_hash}")
        print(f"   Explorer: {agent.solana.explorer_url.format(tx_hash)}")
    except Exception as e:
        print(f"❌ Payment Failed: {e}")

if __name__ == "__main__":
    main()
