from iagent_pay.agent_pay import AgentPay

def main():
    print("--- 🔄 Auto-Swap Demo ---")
    
    # Initialize Solana Agent
    agent = AgentPay(chain_name="SOL_MAINNET")
    
    print("\n1️⃣  Checking Rate (SOL -> BONK)...")
    quote = agent.swap_engine.get_quote("SOL", "BONK", 1.0)
    print(f"Rate: 1 SOL = {quote['rate']} BONK")
    
    print("\n2️⃣  Executing Swap (Degen Mode)...")
    result = agent.swap("SOL", "BONK", 1.0)
    
    print(f"✅ Swap Complete! Hash: {result['tx_hash']}")
    print(f"   Now holding: {result['output_amount']} BONK")

if __name__ == "__main__":
    main()
