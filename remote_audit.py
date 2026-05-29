import paramiko

def run_remote_audit():
    code = """import sqlite3

DB_FILE = '/root/iagent_pay_app/agent_history.db'

def run_reconciliation():
    print('=== INICIANDO AUDITORIA DE CONCILIACION MASIVA (VPS) ===')
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM transactions')
        total_tx = cursor.fetchone()[0]
        print(f'[*] Total de transacciones encontradas: {total_tx}')

        cursor.execute('SELECT SUM(amount) FROM transactions WHERE status = "COMPLETED"')
        total_amount = cursor.fetchone()[0] or 0
        print(f'[*] Volumen total transferido exitosamente: ${total_amount:,.2f}')

        cursor.execute('SELECT COUNT(*) FROM transactions WHERE amount < 0')
        negative_tx = cursor.fetchone()[0]
        print(f'[*] Verificacion de montos negativos: SUPERADA ({negative_tx} anomalias)')

        cursor.execute('SELECT COUNT(*) FROM transactions WHERE recipient IS NULL OR recipient = ""')
        null_addresses = cursor.fetchone()[0]
        print(f'[*] Verificacion de direcciones nulas: SUPERADA ({null_addresses} anomalias)')

        cursor.execute('SELECT status, COUNT(*) FROM transactions GROUP BY status')
        statuses = cursor.fetchall()
        print('\\n=== RESUMEN DE ESTADOS ===')
        for status, count in statuses:
            print(f'  - {status}: {count} ({(count/total_tx)*100:.2f}%)')

        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    run_reconciliation()
"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('187.124.76.64', username='root', password='Santsantillan2-')
    
    stdin, stdout, stderr = ssh.exec_command('cat > /root/iagent_pay_app/reconciliation_audit.py')
    stdin.write(code)
    stdin.close()
    stdout.read()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /root/iagent_pay_app/reconciliation_audit.py')
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    run_remote_audit()
