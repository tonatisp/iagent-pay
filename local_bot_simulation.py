import os
import sys
import time
import json
import secrets
import threading
import random

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

# Setup local simulation environment to not use real money
os.environ["IAGENT_PAY_TESTING"] = "1"
os.environ["ETH_PRIVATE_KEY"] = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from iagent_pay.agent_pay import AgentPay

def bot_worker(bot_name, chain_name, symbol, recipient, amount_base):
    print(f"[{bot_name}] Initializing on {chain_name}...")
    agent = AgentPay(chain_name=chain_name, daily_limit=50000.0)
    
    total_ops = 20
    
    for i in range(1, total_ops + 1):
        # Vary the amount slightly to simulate different txs
        amount = round(amount_base + (random.random() * 0.10), 2)
        tx_hash = "0x" + secrets.token_hex(32)
            
        status = f"CONFIRMED_{symbol}" if symbol != "ETH" else "CONFIRMED"
        
        # Log to local SQLite database directly
        agent._log_transaction(tx_hash, recipient, amount, status, symbol=symbol)
        print(f"[{bot_name}] Tx {i}/{total_ops}: Sent {amount} {symbol} to {recipient[:12]}... Hash: {tx_hash[:16]}...")
        
        # Pacing logic - fast but small random delays between operations
        time.sleep(random.uniform(0.1, 0.3))

    print(f"[{bot_name}] Completed all {total_ops} operations.")

def main():
    print("==================================================")
    print(" iAgent-Pay: Local Multi-Bot Simulation")
    print("==================================================\n")
    
    # Start Bot Alpha
    t_alpha = threading.Thread(target=bot_worker, args=("Bot-Alpha", "POLYGON", "USDC", "0xAlphaTester1234567890abcdef1234567890abc", 1.0))
    # Start Bot Beta
    t_beta = threading.Thread(target=bot_worker, args=("Bot-Beta", "BASE", "USDC", "0xBetaTester1234567890abcdef1234567890abcd", 2.0))
    # Start Bot Gamma
    t_gamma = threading.Thread(target=bot_worker, args=("Bot-Gamma", "SEPOLIA", "SepoliaETH", "0xGammaTester1234567890abcdef1234567890abc", 0.05))
    
    start_time = time.time()
    t_alpha.start()
    t_beta.start()
    t_gamma.start()
    
    t_alpha.join()
    t_beta.join()
    t_gamma.join()
    
    elapsed = time.time() - start_time
    print("\n=============================================")
    print(f" Local Simulation Completed in {elapsed:.2f} seconds.")
    print("=============================================")

if __name__ == "__main__":
    main()
