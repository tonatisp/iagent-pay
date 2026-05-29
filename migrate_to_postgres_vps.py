import sqlite3
import psycopg2

PG_URL = "postgresql://iagent_admin:Santsantillan2-DB@localhost:5432/iagent_db"

def migrate():
    print("Connecting to Postgres...")
    pg_conn = psycopg2.connect(PG_URL)
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()
    
    # 1. agent_history.db
    print("Migrating agent_history.db...")
    sqlite_conn = sqlite3.connect('agent_history.db')
    sqlite_cur = sqlite_conn.cursor()
    
    try:
        pg_cur.execute('DROP TABLE transactions')
    except:
        pass
        
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in sqlite_cur.fetchall()]
    
    if 'transactions' in tables:
        sqlite_cur.execute("PRAGMA table_info(transactions)")
        cols = [r[1] for r in sqlite_cur.fetchall()]
        print("transactions columns:", cols)
        
        # Dynamically create table based on sqlite columns
        pg_cur.execute('DROP TABLE IF EXISTS transactions')
        col_defs = []
        for col in cols:
            col_defs.append(f"{col} TEXT") # default to TEXT for everything to avoid type issues
        
        pg_cur.execute(f"CREATE TABLE transactions ({','.join(col_defs)})")
        
        sqlite_cur.execute(f"SELECT {','.join(cols)} FROM transactions")
        rows = sqlite_cur.fetchall()
        
        placeholders = ','.join(['%s'] * len(cols))
        q = f"INSERT INTO transactions ({','.join(cols)}) VALUES ({placeholders})"
        count = 0
        for row in rows:
            try:
                pg_cur.execute(q, row)
                count += 1
            except Exception as e:
                print("Error inserting tx:", e)
        print(f"Migrated {count} transactions.")
        
    if 'paid_invoices' in tables:
        sqlite_cur.execute("PRAGMA table_info(paid_invoices)")
        cols = [r[1] for r in sqlite_cur.fetchall()]
        sqlite_cur.execute(f"SELECT {','.join(cols)} FROM paid_invoices")
        rows = sqlite_cur.fetchall()
        
        pg_cur.execute('DROP TABLE IF EXISTS paid_invoices')
        col_defs = []
        for col in cols:
            col_defs.append(f"{col} TEXT")
        pg_cur.execute(f"CREATE TABLE paid_invoices ({','.join(col_defs)})")

        placeholders = ','.join(['%s'] * len(cols))
        q = f"INSERT INTO paid_invoices ({','.join(cols)}) VALUES ({placeholders})"
        for row in rows:
            try:
                pg_cur.execute(q, row)
            except Exception as e:
                pass
        print(f"Migrated {len(rows)} paid_invoices.")
    
    sqlite_conn.close()

    # 2. agent_reputation.db
    print("Migrating agent_reputation.db...")
    sqlite_conn = sqlite3.connect('agent_reputation.db')
    sqlite_cur = sqlite_conn.cursor()
    
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in sqlite_cur.fetchall()]
    
    for t in tables:
        if t in ['peer_ratings', 'admin_wallets', 'compliance_logs', 'custom_licenses']:
            sqlite_cur.execute(f"PRAGMA table_info({t})")
            cols = [r[1] for r in sqlite_cur.fetchall()]
            sqlite_cur.execute(f"SELECT {','.join(cols)} FROM {t}")
            rows = sqlite_cur.fetchall()
            
            pg_cur.execute(f'DROP TABLE IF EXISTS {t}')
            col_defs = [f"{col} TEXT" for col in cols]
            pg_cur.execute(f"CREATE TABLE {t} ({','.join(col_defs)})")
            
            placeholders = ','.join(['%s'] * len(cols))
            q = f"INSERT INTO {t} ({','.join(cols)}) VALUES ({placeholders})"
            
            count = 0
            for row in rows:
                try:
                    pg_cur.execute(q, row)
                    count += 1
                except Exception as e:
                    print("Error inserting rep:", e)
            print(f"Migrated {count} rows in {t}.")
            
    sqlite_conn.close()
    
    # 3. agent_marketplace.db
    print("Migrating agent_marketplace.db...")
    sqlite_conn = sqlite3.connect('agent_marketplace.db')
    sqlite_cur = sqlite_conn.cursor()
    
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in sqlite_cur.fetchall()]
    
    for t in tables:
        if t == 'escrow_contracts':
            sqlite_cur.execute(f"PRAGMA table_info({t})")
            cols = [r[1] for r in sqlite_cur.fetchall()]
            sqlite_cur.execute(f"SELECT {','.join(cols)} FROM {t}")
            rows = sqlite_cur.fetchall()
            
            pg_cur.execute(f'DROP TABLE IF EXISTS {t}')
            col_defs = [f"{col} TEXT" for col in cols]
            pg_cur.execute(f"CREATE TABLE {t} ({','.join(col_defs)})")
            
            placeholders = ','.join(['%s'] * len(cols))
            q = f"INSERT INTO {t} ({','.join(cols)}) VALUES ({placeholders})"
            
            count = 0
            for row in rows:
                try:
                    pg_cur.execute(q, row)
                    count += 1
                except Exception as e:
                    print("Error inserting escrow:", e)
            print(f"Migrated {count} rows in {t}.")
            
    sqlite_conn.close()
    
    pg_conn.commit()
    pg_conn.close()
    print("Done migrating!")

if __name__ == "__main__":
    migrate()
