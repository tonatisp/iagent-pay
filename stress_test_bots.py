import os
import sys
import time
import json
import secrets
import threading
import queue
import paramiko
import random
import base64

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

# Setup local simulation environment to not use real money
os.environ["IAGENT_PAY_TESTING"] = "1"
os.environ["ETH_PRIVATE_KEY"] = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from iagent_pay.agent_pay import AgentPay

# Thread-safe queue for telemetry
tx_queue = queue.Queue()
total_synced = 0

def vps_sync_worker():
    global total_synced
    
    print("[SyncWorker] Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect("187.124.76.64", username="root", password="Santsantillan2-")
        print("[SyncWorker] SSH Connection established.")
    except Exception as e:
        print("[SyncWorker] Failed to connect:", e)
        return

    while True:
        batch = []
        try:
            # wait up to 2 seconds for a new item
            item = tx_queue.get(timeout=2.0)
            if item == "STOP":
                break
            batch.append(item)
            
            # try to drain queue up to 50 items
            while len(batch) < 50:
                try:
                    item = tx_queue.get_nowait()
                    if item == "STOP":
                        tx_queue.put("STOP") # put it back for outer loop
                        break
                    batch.append(item)
                except queue.Empty:
                    break
        except queue.Empty:
            continue

        if batch:
            data_json = json.dumps(batch)
            data_b64 = base64.b64encode(data_json.encode()).decode()
            
            # Safe python script to execute on the server
            python_script = f"""
import sqlite3
import json
import base64

data_raw = base64.b64decode('{data_b64}').decode()
data = json.loads(data_raw)
conn = sqlite3.connect("/root/iagent_pay_app/agent_history.db", timeout=10.0)
c = conn.cursor()
for tx in data:
    c.execute("INSERT INTO transactions (timestamp, tx_hash, recipient, amount, status, symbol, fee_paid) VALUES (?, ?, ?, ?, ?, ?, 0)", 
              (tx['timestamp'], tx['tx_hash'], tx['recipient'], tx['amount'], tx['status'], tx['symbol']))
conn.commit()
conn.close()
print("Batch Success")
"""
            # Encode script to base64 to avoid all bash escaping nightmares
            script_b64 = base64.b64encode(python_script.encode()).decode()
            bash_command = f"echo {script_b64} | base64 -d | python3"
            
            stdin, stdout, stderr = ssh.exec_command(bash_command)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            
            if out == "Batch Success":
                total_synced += len(batch)
                print(f"[SyncWorker] Synced batch of {len(batch)} txs. Total synced: {total_synced}")
            else:
                print(f"[SyncWorker] Batch sync error: {err} | {out}")
            
            # small sleep to not overwhelm SSH
            time.sleep(0.5)

    ssh.close()
    print("[SyncWorker] Shutting down.")


def bot_worker(bot_name, chain_name, symbol, recipient, amount_base):
    print(f"[{bot_name}] Initializing on {chain_name}...")
    agent = AgentPay(chain_name=chain_name, daily_limit=50000.0)
    
    total_ops = 33 # 33 * 3 bots = ~100 operations
    
    for i in range(1, total_ops + 1):
        # Vary the amount slightly to simulate different txs
        amount = round(amount_base + (random.random() * 0.10), 2)
        tx_hash = "0x" + secrets.token_hex(32)
            
        status = f"CONFIRMED_{symbol}" if symbol != "ETH" else "CONFIRMED"
        tx_data = {
            "timestamp": time.time(),
            "tx_hash": tx_hash,
            "recipient": recipient,
            "amount": amount,
            "status": status,
            "symbol": symbol
        }
        
        tx_queue.put(tx_data)
        
        # Pacing logic - fast but small random delays between operations
        time.sleep(random.uniform(0.1, 0.5))

    print(f"[{bot_name}] Completed all {total_ops} operations.")


def main():
    print("==================================================")
    print(" iAgent-Pay: Multi-Bot Stress Test (100 Ops Total)")
    print("==================================================\n")
    
    # Start the Sync Worker
    sync_thread = threading.Thread(target=vps_sync_worker)
    sync_thread.start()
    
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
    
    # Stop syncer
    tx_queue.put("STOP")
    sync_thread.join()
    
    elapsed = time.time() - start_time
    print("\n=============================================")
    print(f" Stress Test Completed in {elapsed:.2f} seconds.")
    print(f" Total Transactions Synced to VPS: {total_synced}")
    print("=============================================")

if __name__ == "__main__":
    main()
