import os
import time
import random
import psycopg2

def run():
    print("Conectando a PostgreSQL para inyectar transacciones en vivo...")
    pg_url = "postgresql://iagent_admin:Santsantillan2-DB@localhost:5432/iagent_db"
    
    conn = psycopg2.connect(pg_url)
    conn.autocommit = True
    c = conn.cursor()
    
    q = "INSERT INTO transactions (tx_hash, agent_id, amount, symbol, status, timestamp, chain, recipient, fee_paid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    
    for i in range(25):
        tx_hash = f"0xVerifyOp_{int(time.time()*1000)}_{random.randint(1000,9999)}_{i}"
        amount = round(random.uniform(5.0, 1200.0), 2)
        symbol = random.choice(["USDC", "ETH", "MATIC", "BNB", "SOL"])
        chain = random.choice(["POLYGON", "ETHEREUM", "BINANCE", "SOLANA"])
        
        c.execute(q, (
            tx_hash,
            "Agent_Live_Demo",
            amount,
            symbol,
            "CONFIRMED",
            time.time() + i,
            chain,
            "0xAuditor_Test_Wallet",
            1.0 if random.random() < 0.2 else 0.0
        ))
        
        print(f"[{i+1}/25] Transaccion {tx_hash} por {amount} {symbol} insertada exitosamente.")
        time.sleep(0.5)
        
    conn.close()

if __name__ == "__main__":
    run()
