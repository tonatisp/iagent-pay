import os
import shutil
import datetime
import gzip
import subprocess

# Paths for VPS
DB_FILE = "/root/iagent_pay_app/agent_history.db"
BACKUP_DIR = "/root/iagent_pay_app/backups"
BACKUP_DIR = "/root/iagent_pay_app/backups"

# Fallback for local testing
if not os.path.exists(DB_FILE):
    DB_FILE = "agent_history.db"
    BACKUP_DIR = "backups"

def create_backup():
    print("=== INICIANDO RESPALDO DE BASE DE DATOS ===")
    db_url = os.environ.get("DATABASE_URL")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    if db_url and ("postgres://" in db_url or "postgresql://" in db_url):
        # Enterprise PostgreSQL Backup
        backup_file = os.path.join(BACKUP_DIR, f"pg_backup_{date_str}.sql.gz.enc")
        print(f"[*] Iniciando pg_dump y cifrado AES-256 para PostgreSQL...")
        
        # We replace postgres:// with postgresql:// to avoid errors in pg_dump
        pg_dump_url = db_url.replace("postgres://", "postgresql://", 1)
        encryption_key = os.environ.get("BACKUP_ENCRYPTION_KEY", "iAgentPay-Enterprise-Secure-Key-2026")
        
        # pg_dump | gzip | openssl enc -aes-256-cbc
        cmd = f"pg_dump \"{pg_dump_url}\" | gzip | openssl enc -aes-256-cbc -salt -pass pass:{encryption_key} -out {backup_file}"
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"[*] Respaldo empresarial de PostgreSQL cifrado en: {backup_file}")
            print(f"[*] Simulación S3: Archivo subido a s3://iagentpay-backups-cold/{os.path.basename(backup_file)}")
        except subprocess.CalledProcessError as e:
            print(f"[!] Error ejecutando pg_dump: {e}")
            return
            
    else:
        # Fallback to local SQLite Backup
        if not os.path.exists(DB_FILE):
            print(f"ERROR: Archivo origen SQLite no encontrado ({DB_FILE})")
            return
            
        backup_file = os.path.join(BACKUP_DIR, f"agent_history_backup_{date_str}.db.gz")
        try:
            with open(DB_FILE, 'rb') as f_in:
                with gzip.open(backup_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print(f"[*] Respaldo SQLite comprimido guardado en: {backup_file}")
        except Exception as e:
            print(f"[!] Error respaldando SQLite: {e}")
            return

    # Cleanup old backups (keep only last 7)
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        backups = sorted([os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if '.gz' in f])
        if len(backups) > 7:
            for old_file in backups[:-7]:
                os.remove(old_file)
                print(f"[*] Limpieza: Respaldo antiguo eliminado ({old_file})")
                
        print("=== RESPALDO COMPLETADO EXITOSAMENTE ===")
    except Exception as e:
        print(f"[!] ERROR en limpieza de respaldos: {e}")

if __name__ == "__main__":
    create_backup()
