import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("187.124.76.64", username="root", password="Santsantillan2-")

stdin, stdout, stderr = ssh.exec_command("ls -l /proc/164092/cwd; cat /proc/164092/cmdline; echo ''; ls -la /root/iagent_pay_app")
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())

ssh.close()
