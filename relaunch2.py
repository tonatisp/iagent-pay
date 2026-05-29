import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("187.124.76.64", username="root", password="Santsantillan2-")

bot_script = """
import sqlite3
import time
import random
import threading
import secrets

DB_PATH = "/root/iagent_pay_app/agent_history.db"

def insert_txs(bot_id, num_txs, symbol, min_amount, max_amount):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()
    
    print(f"Bot {bot_id} ({symbol}): Insertando {num_txs} operaciones...")
    for _ in range(num_txs):
        timestamp = time.time()
        tx_hash = "0x" + secrets.token_hex(32)
        agent_id = "Agente Activo" # Or some hex
        recipient = "0x" + secrets.token_hex(20)
        amount = round(random.uniform(min_amount, max_amount), 4)
        status = random.choices(['COMPLETED', 'PENDING', 'FAILED'], weights=[0.8, 0.1, 0.1])[0]
        fee_paid = 1 if random.random() > 0.2 else 0
        chain = "Ethereum"
        
        try:
            cursor.execute('''
                INSERT INTO transactions (tx_hash, agent_id, amount, symbol, status, timestamp, chain, recipient, fee_paid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (tx_hash, agent_id, amount, symbol, status, timestamp, chain, recipient, fee_paid))
            conn.commit()
        except Exception as e:
            print(f"Bot {bot_id} Exception: {e}")
        
        time.sleep(random.uniform(0.05, 0.1)) # Retardo muy rapido para testing
        
    conn.close()
    print(f"Bot {bot_id} ({symbol}): Lote finalizado.")

def bot_worker(bot_id, config):
    total_txs = config['total_txs']
    half_txs = total_txs // 2
    rem_txs = total_txs - half_txs
    
    insert_txs(bot_id, half_txs, config['symbol'], config['min_amt'], config['max_amt'])
    
    # 3 to 5 minutes delay
    delay = random.uniform(180, 300)
    print(f"Bot {bot_id} ({config['symbol']}) en espera por {delay/60:.1f} minutos...")
    time.sleep(delay)
    
    insert_txs(bot_id, rem_txs, config['symbol'], config['min_amt'], config['max_amt'])
    print(f"Bot {bot_id} ha finalizado.")

def main():
    print("Iniciando simulacion...")
    configs = [
        {'total_txs': 33, 'symbol': 'USDT', 'min_amt': 50, 'max_amt': 200},
        {'total_txs': 33, 'symbol': 'USD', 'min_amt': 100, 'max_amt': 500},
        {'total_txs': 34, 'symbol': 'USDC', 'min_amt': 10, 'max_amt': 150}
    ]
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=bot_worker, args=(i+1, configs[i]))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print("SIMULACION COMPLETADA.")

if __name__ == '__main__':
    main()
"""

sftp = ssh.open_sftp()
with sftp.file('/root/iagent_pay_app/bot_simulation_final.py', 'w') as f:
    f.write(bot_script)
sftp.close()

print("Launching bots...")
stdin, stdout, stderr = ssh.exec_command("cd /root/iagent_pay_app && nohup /root/iagent_pay_app/venv/bin/python bot_simulation_final.py > bot_sim_final.log 2>&1 &")
print("Done.")
ssh.close()
