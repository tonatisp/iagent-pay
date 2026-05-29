import paramiko

VPS_IP = "187.124.76.64"
VPS_USER = "root"
VPS_PASS = "Santsantillan2-"

def kill_sim():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)
    
    print("Killing simulation...")
    _, out, _ = ssh.exec_command("pkill -f live_60min_ultimate.py")
    print(out.read().decode())
    _, out, _ = ssh.exec_command("pkill -f live_10min_simulation.py")
    
    ssh.close()

if __name__ == "__main__":
    kill_sim()
