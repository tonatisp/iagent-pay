import paramiko
import sys
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
    if e and e.strip(): print("STDERR:", e)

# Confirmar que ahora las endpoints son accesibles sin token
run("curl -s http://localhost:8000/api/admin/metrics", "metrics SIN auth (debe mostrar datos)")
run("curl -s 'http://localhost:8000/api/transactions?limit=3'", "transactions SIN auth (debe mostrar datos)")

ssh.close()
print("\nVerificacion completada.")
