import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('187.124.76.64', username='root', password='Santsantillan2-')

_, out, _ = ssh.exec_command('curl -s http://localhost:8000/api/admin/metrics')
print('METRICS:', out.read().decode('utf-8', errors='replace')[:600])

_, out, _ = ssh.exec_command('curl -s "http://localhost:8000/api/transactions?limit=2"')
print('TRANSACTIONS:', out.read().decode('utf-8', errors='replace')[:600])

ssh.close()
