import paramiko
import sys

# Forzar UTF-8 en la salida
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('187.124.76.64', username='root', password='Santsantillan2-')

def run(cmd, label):
    _, out, err = ssh.exec_command(cmd)
    print(f"\n=== {label} ===")
    o = out.read().decode('utf-8', errors='replace')
    e = err.read().decode('utf-8', errors='replace')
    if o: print(o)
    if e: print("STDERR:", e)

# 1. Postgres - contar transacciones y ver las ultimas 5
run("""cd /root/iagent_pay_app && venv/bin/python -c "
import psycopg2
c = psycopg2.connect('postgresql://iagent_admin:Santsantillan2-DB@localhost:5432/iagent_db')
cur = c.cursor()
cur.execute('SELECT COUNT(*) FROM transactions')
print('Total en postgres:', cur.fetchone()[0])
cur.execute(\"SELECT tx_hash, amount, symbol, status FROM transactions ORDER BY timestamp DESC LIMIT 5\")
for r in cur.fetchall():
    print(' ->', r)
" 2>&1""", "Conteo en Postgres")

# 2. Ver que archivo serve_dashboard.py corre el servicio (fecha de modificacion)
run("ls -la /root/iagent_pay_app/serve_dashboard.py && md5sum /root/iagent_pay_app/serve_dashboard.py", "serve_dashboard en VPS")

# 3. Ver environment del proceso de python vivo
run("cat /proc/$(ps aux | grep serve_dashboard | grep -v grep | awk '{print $2}' | head -1)/environ | tr '\\0' '\\n' | grep -E 'DATABASE|PORT'", "ENV del proceso")

# 4. Hacer GET a metrics sin token para ver la respuesta exacta
run("curl -s http://localhost:8000/api/admin/metrics", "metrics sin auth")

# 5. Hacer GET a transactions sin token
run("curl -s http://localhost:8000/api/transactions?limit=3", "transactions sin auth")

# 6. Ver ultimas lineas del log del servicio buscando traceback Python
run("journalctl -u iagent-pay -n 200 --no-pager 2>/dev/null | grep -A5 'Traceback\\|Error\\|500' | head -60", "Errores Python en log")

ssh.close()
print("\nDone.")
