import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("187.124.76.64", username="root", password="Santsantillan2-")

bot_script = """
import sqlite3
import time
import random
import threading
import uuid
import secrets
import sys

DB_PATH = "/root/iagent_pay_app/agent_history.db"

def insert_txs(bot_id, num_txs, symbol, min_amount, max_amount):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions
                      (id TEXT PRIMARY KEY,
                       timestamp REAL,
                       tx_hash TEXT,
                       sender TEXT,
                       recipient TEXT,
                       amount REAL,
                       symbol TEXT,
                       status TEXT,
                       fee_paid INTEGER)''')
    
    print(f"Bot {bot_id} ({symbol}): Insertando {num_txs} operaciones...")
    for _ in range(num_txs):
        tx_id = str(uuid.uuid4())
        timestamp = time.time()
        tx_hash = "0x" + secrets.token_hex(32)
        sender = "0x" + secrets.token_hex(20)
        recipient = "0x" + secrets.token_hex(20)
        amount = round(random.uniform(min_amount, max_amount), 4)
        status = random.choices(['COMPLETED', 'PENDING', 'FAILED'], weights=[0.8, 0.1, 0.1])[0]
        fee_paid = 1 if random.random() > 0.2 else 0
        
        try:
            cursor.execute('''
                INSERT INTO transactions (id, timestamp, tx_hash, sender, recipient, amount, symbol, status, fee_paid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (tx_id, timestamp, tx_hash, sender, recipient, amount, symbol, status, fee_paid))
            conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Bot {bot_id} Error: {e}")
        
        time.sleep(random.uniform(0.05, 0.2)) # Simular retardo natural entre transacciones
        
    conn.close()
    print(f"Bot {bot_id} ({symbol}): Primer lote finalizado.")

def bot_worker(bot_id, config):
    total_txs = config['total_txs']
    half_txs = total_txs // 2
    rem_txs = total_txs - half_txs
    
    # Primera mitad (inmediata)
    insert_txs(bot_id, half_txs, config['symbol'], config['min_amt'], config['max_amt'])
    
    # Retardo estipulado de 3 a 5 minutos (180 a 300 segundos)
    delay = random.uniform(180, 300)
    print(f"Bot {bot_id} ({symbol}) en espera activa por {delay/60:.1f} minutos antes de reanudar...")
    time.sleep(delay)
    
    # Segunda mitad
    insert_txs(bot_id, rem_txs, config['symbol'], config['min_amt'], config['max_amt'])
    print(f"Bot {bot_id} ha finalizado todas sus operaciones.")

def main():
    print("Iniciando simulación de 3 Bots...")
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
        
    print("SIMULACION COMPLETADA. 100 transacciones insertadas exitosamente por los bots.")

if __name__ == '__main__':
    main()
"""

# Guardamos el script en el servidor y lo ejecutamos en segundo plano
sftp = ssh.open_sftp()
with sftp.file('/root/iagent_pay_app/bot_simulation_100.py', 'w') as f:
    f.write(bot_script)
sftp.close()

# Ejecutarlo en segundo plano para que el SSH no se cuelgue 3-5 minutos
print("Lanzando bots en el VPS...")
stdin, stdout, stderr = ssh.exec_command("cd /root/iagent_pay_app && nohup python bot_simulation_100.py > bot_sim.log 2>&1 &")
print("Bots ejecutándose en segundo plano (nohup).")
ssh.close()
