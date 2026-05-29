import paramiko

VPS_IP = "187.124.76.64"
VPS_USER = "root"
VPS_PASS = "Santsantillan2-"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)

print("Checking db count...")
stdin, stdout, stderr = ssh.exec_command("python3 -c 'import sqlite3; c=sqlite3.connect(\"/root/iagent_pay_app/agent_marketplace.db\").cursor(); print(c.execute(\"SELECT count(*) FROM escrow_contracts\").fetchone()[0])'")
print(stdout.read().decode("utf-8").strip())
ssh.close()
