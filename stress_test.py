import time
from web3 import Web3, EthereumTesterProvider
from iagent_pay.agent_pay import AgentPay

def simulate_high_frequency_trading():
    print("⚡ Starting High-Frequency Transaction Test (HFT)...")
    print("🎯 Goal: Benchmarking SDK Speed (Simulated Chain)")
    
    # 1. Setup Local High-Speed Chain
    provider = EthereumTesterProvider()
    w3_local = Web3(provider)
    
    # 2. Setup Agents
    # We init with "ETH" just to load defaults, then override w3
    print("🤖 Initializing Agents...")
    agent_a = AgentPay(chain_name="LOCAL")
    agent_a.w3 = w3_local
    agent_a.my_address = agent_a.account.address # Ensure address matches
    
    agent_b = AgentPay(chain_name="LOCAL")
    agent_b.w3 = w3_local
    
    # 3. Fund them both (God Mode)
    god_account = w3_local.eth.accounts[0]
    print("💰 Funding Agents...")
    w3_local.eth.send_transaction({'from': god_account, 'to': agent_a.my_address, 'value': w3_local.to_wei(100, 'ether')})
    w3_local.eth.send_transaction({'from': god_account, 'to': agent_b.my_address, 'value': w3_local.to_wei(100, 'ether')})
    
    print("🚀 STARTING ENGINE...\n")
    
    start_time = time.time()
    tx_count = 0
    target_tx = 20
    
    for i in range(target_tx // 2): 
        # A -> B
        try:
            # We mock the _check_license to avoid DB/Treasury logic slowing us down or failing locally
            # actually license check is fine if it doesn't block.
            tx1 = agent_a.pay_agent(agent_b.my_address, 0.01, wait=False)
            print(f"[{i+1}a] A -> B: {tx1}")
            tx_count += 1
            
            # B -> A
            tx2 = agent_b.pay_agent(agent_a.my_address, 0.01, wait=False)
            print(f"[{i+1}b] B <- A: {tx2}")
            tx_count += 1
        except Exception as e:
            print(f"❌ Error: {e}")
            break

    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n🏁 TEST COMPLETE!")
    print(f"📊 Stats:")
    print(f"   Transactions: {tx_count}")
    print(f"   Time Taken:   {duration:.2f} seconds")
    tps = tx_count / duration
    print(f"   TPS (SDK):    {tps:.2f} tx/sec")
    print(f"   Tx/Min:       {tps * 60:.2f} tx/min")

if __name__ == "__main__":
    simulate_high_frequency_trading()
