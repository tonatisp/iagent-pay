import time
from iagent_pay import AgentPay, WalletManager
from web3 import Web3

def simulate_economy():
    print("🤖 Initializing AgentPay Economy Simulation...\n")
    wm = WalletManager()

    # 1. Create Agents
    # In a real local simulation, we need funds. 
    # The EthereumTesterProvider usually pre-funds the first 10 accounts.
    # We will simulate that "Agent A" is one of those funded accounts.
    
    # We cheat slightly for the simulation to get a funded account from the provider
    # In production, you would fund the agent's wallet manually.
    temp_w3 = Web3(Web3.EthereumTesterProvider())
    funded_account_address = temp_w3.eth.accounts[0] # Get a funded address
    # We can't easily get the private key of the tester accounts in this specific setup 
    # without deeper hooks, so for this DEMO script simplicity, we will:
    # Use a custom provider that funds our new agents for the sake of the demo.
    
    # Actually, simpler: Use simulated provider in AgentPay and let's just 'pretend' funding for the MVP demo output
    # or use the simulation capabilities to send test ETH.
    
    print("Creating Agent A (The Client)...")
    wallet_a = wm.create_wallet()
    agent_a = AgentPay(wallet_a) 
    # Fund Agent A (Simulation Hack)
    # sending from the 'god' account of the test provider to Agent A
    god_address = agent_a.w3.eth.accounts[0] 
    agent_a.w3.eth.send_transaction({'to': wallet_a.address, 'from': god_address, 'value': agent_a.w3.to_wei(10, 'ether')})
    
    print(f"Agent A Address: {wallet_a.address}")
    print(f"Agent A Balance: {agent_a.get_balance()} ETH\n")

    print("Creating Agent B (The Service Provider)...")
    wallet_b = wm.create_wallet()
    agent_b = AgentPay(wallet_b)
    print(f"Agent B Address: {wallet_b.address}")
    print(f"Agent B Balance: {agent_b.get_balance()} ETH\n")

    # 2. Simulate Interaction
    service_price = 0.005
    print(f"🚀 Agent A wants to buy a 'Weather Forecast' dataset from Agent B.")
    print(f"💳 Price: {service_price} ETH")
    print("Processing payment...")

    start_time = time.time()
    tx_hash = agent_a.pay_agent(wallet_b.address, service_price)
    end_time = time.time()

    print(f"✅ Payment Complete!")
    print(f"🔗 Transaction Hash: {tx_hash}")
    print(f"⏱️ Time taken: {end_time - start_time:.4f} seconds\n")

    # 3. Verify Balances
    print("--- Final State ---")
    print(f"Agent A Balance: {agent_a.get_balance()} ETH (Decreased)")
    print(f"Agent B Balance: {agent_b.get_balance()} ETH (Increased)")
    print("\n🎉 Simulation Success: Agents traded value autonomously!")

if __name__ == "__main__":
    simulate_economy()
