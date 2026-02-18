from iagent_pay.agent_pay import AgentPay
from web3 import Web3, EthereumTesterProvider

def main():
    print("--- ⛽ Gas Guardrail Demo ---")
    
    # 1. Setup Local Chain (Gas is usually 1 Gwei here)
    provider = EthereumTesterProvider()
    w3 = Web3(provider)
    
    agent = AgentPay(chain_name="LOCAL")
    agent.w3 = w3 
    agent.my_address = agent.account.address
    
    # Fund Agent
    w3.eth.send_transaction({'from': w3.eth.accounts[0], 'to': agent.my_address, 'value': w3.to_wei(1, 'ether')})

    recipient = w3.eth.accounts[1]

    # Test 1: Conservative Limit (Should FAIL because Base Fee is ~1 Gwei)
    print("\n1️⃣  Attempting Payment with limit=0.0001 Gwei (Impossible Limit)...")
    try:
        agent.pay_agent(recipient, 0.01, wait=False, max_gas_gwei=0.0001)
        print("❌ Failed: Transaction went through but should have aborted.")
    except ValueError as e:
        print(f"✅ Success! Guardrail Active: {e}")

    # Test 2: Generous Limit
    print("\n2️⃣  Attempting Payment with limit=100 Gwei (Safe Limit)...")
    try:
        tx = agent.pay_agent(recipient, 0.01, wait=False, max_gas_gwei=100)
        print(f"✅ Transaction Sent! {tx.hex()}")
    except ValueError as e:
        print(f"❌ Failed unexpectedly: {e}")

if __name__ == "__main__":
    main()
