import os
import time
import uuid
import multiprocessing
import psycopg2

PG_URL = os.environ.get("DATABASE_URL", "postgresql://iagent_admin:Santsantillan2-DB@localhost:5432/iagent_db")

def worker(duration, q):
    conn = psycopg2.connect(PG_URL)
    conn.autocommit = True
    c = conn.cursor()
    
    start_time = time.time()
    count = 0
    
    while time.time() - start_time < duration:
        tx_hash = "0xTPS" + uuid.uuid4().hex[:30]
        try:
            c.execute("""
                INSERT INTO transactions (tx_hash, agent_id, amount, symbol, status, timestamp, chain, recipient, fee_paid) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (tx_hash, "TPS_BOT", 10.0, "USDC", "CONFIRMED", time.time(), "POLYGON", "TEST_REC", 1.0))
            count += 1
        except Exception:
            pass
            
    conn.close()
    q.put(count)

def run_benchmark(duration=10, workers=4):
    print(f"INICIANDO BENCHMARK DE TPS EN VPS (POSTGRESQL)")
    print(f"Duracion: {duration} segundos")
    print(f"Procesos concurrentes: {workers}")
    
    q = multiprocessing.Queue()
    processes = []
    
    start_time = time.time()
    
    for _ in range(workers):
        p = multiprocessing.Process(target=worker, args=(duration, q))
        processes.append(p)
        p.start()
        
    for p in processes:
        p.join()
        
    total_time = time.time() - start_time
    total_tx = 0
    
    while not q.empty():
        total_tx += q.get()
        
    tps = total_tx / total_time
    
    print("\n" + "="*30)
    print("RESULTADOS DEL BENCHMARK")
    print("="*30)
    print(f"Transacciones exitosas: {total_tx}")
    print(f"Tiempo total real:      {total_time:.2f} s")
    print(f"Velocidad (TPS):        {tps:.2f} tx/sec")
    print("="*30)

if __name__ == "__main__":
    run_benchmark(duration=10, workers=4)
