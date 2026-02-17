import time
from iagent_pay import AgentPay, WalletManager

def simulate_high_frequency_trading():
    print("⚡ Starting High-Frequency Transaction Test (HFT)...")
    print("🎯 Goal: 20 Transactions in < 60 seconds")
    
    # 1. Setup Local High-Speed Chain (Sepolia is too slow for 20tx/min)
    provider = EthereumTesterProvider()
    w3_local = Web3(provider)
    wm = WalletManager()
    
    # 2. Setup Agents
    # Agent A (Trader)
    wallet_a = wm.create_wallet()
    agent_a = AgentPay(wallet_a)
    agent_a.w3 = w3_local
    
    # Agent B (Market Maker)
    wallet_b = wm.create_wallet()
    agent_b = AgentPay(wallet_b)
    agent_b.w3 = w3_local
    
    # 3. Fund them both
    god_account = w3_local.eth.accounts[0]
    w3_local.eth.send_transaction({'from': god_account, 'to': wallet_a.address, 'value': w3_local.to_wei(100, 'ether')})
    w3_local.eth.send_transaction({'from': god_account, 'to': wallet_b.address, 'value': w3_local.to_wei(100, 'ether')})
    
    print(f"💰 Agents funded with 100 ETH each.")
    print("🚀 STARTING ENGINE...\n")
    
    start_time = time.time()
    tx_count = 0
    target_tx = 20
    
    for i in range(target_tx // 2): # 10 rounds of Ping-Pong (2 tx per round)
        # A -> B
        tx1 = agent_a.pay_agent(wallet_b.address, 0.01, wait=False)
        print(f"[{i+1}a] A -> B (root: {tx1[:6]}...)")
        tx_count += 1
        
        # B -> A
        tx2 = agent_b.pay_agent(wallet_a.address, 0.01, wait=False)
        print(f"[{i+1}b] B <- A (root: {tx2[:6]}...)")
        tx_count += 1
        
        # Simulated network latency (minimal)
        time.sleep(0.1) 

    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n🏁 TEST COMPLETE!")
    print(f"📊 Stats:")
    print(f"   Transactions: {tx_count}")
    print(f"   Time Taken:   {duration:.2f} seconds")
    print(f"   Speed:        {tx_count / duration * 60:.2f} tx/min")
    
    if duration < 60:
        print("✅ SUCCESS: High-Frequency Goal Met!")
    else:
        print("❌ FAILED: Too Slow.")

if __name__ == "__main__":
    simulate_high_frequency_trading()
