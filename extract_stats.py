import psycopg2

def extract_stats():
    conn = psycopg2.connect("dbname='iagent_db' user='iagent_admin' password='Santsantillan2-DB' host='187.124.76.64'")
    cur = conn.cursor()
    
    # Capital Total Procesado
    cur.execute("SELECT SUM(amount) FROM transactions WHERE status = 'CONFIRMED'")
    total_usd = cur.fetchone()[0] or 0.0
    
    # Comisiones (Fee Paid) - Supongamos que guardamos fees en centavos
    cur.execute("SELECT SUM(fee_paid) FROM transactions WHERE status = 'CONFIRMED'")
    total_fees_cents = cur.fetchone()[0] or 0.0
    total_fees_usd = total_fees_cents / 100.0
    
    # Transacciones
    cur.execute("SELECT COUNT(*) FROM transactions")
    tx_count = cur.fetchone()[0]
    
    # Escrows
    cur.execute("SELECT SUM(amount_usd) FROM escrow_contracts WHERE status = 'LOCKED'")
    locked_escrow = cur.fetchone()[0] or 0.0
    
    print(f"Total USD: {total_usd}")
    print(f"Total Fees USD: {total_fees_usd}")
    print(f"Total TX: {tx_count}")
    print(f"Locked Escrow USD: {locked_escrow}")

if __name__ == "__main__":
    extract_stats()
