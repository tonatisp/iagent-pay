import sqlite3
import time

def check_history():
    db_path = "agent_history.db"
    print(f"📂 Opening Audit Log: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Get count
        c.execute("SELECT COUNT(*) FROM transactions")
        count = c.fetchone()[0]
        print(f"📊 Total Transactions Logged: {count}")
        
        # Get last 5
        print("\n📝 Last 5 Transactions:")
        c.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 5")
        rows = c.fetchall()
        
        for row in rows:
            ts, tx_hash, recipient, amount, status = row
            # Format timestamp
            date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
            print(f"   [{date_str}] {status} | Send {amount} ETH -> {recipient[:6]}... | Hash: {tx_hash[:6]}...")
            
        conn.close()
        
        if count > 0:
            print("\n✅ AUDIT LOG VERIFIED: Database is active and recording.")
        else:
            print("\n❌ AUDIT LOG EMPTY: Something is wrong.")
            
    except Exception as e:
        print(f"❌ Error reading DB: {e}")

if __name__ == "__main__":
    check_history()
