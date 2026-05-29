import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("187.124.76.64", username="root", password="Santsantillan2-")

print("Relaunching bots using the correct python path in the VPS...")
stdin, stdout, stderr = ssh.exec_command("cd /root/iagent_pay_app && nohup /root/iagent_pay_app/venv/bin/python bot_simulation_100.py > bot_sim.log 2>&1 &")
print("Done.")
ssh.close()
