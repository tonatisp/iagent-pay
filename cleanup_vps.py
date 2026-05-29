import paramiko

VPS_IP = "187.124.76.64"
VPS_USER = "root"
VPS_PASS = "Santsantillan2-"

def cleanup_vps():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)
    
    print("Cleaning up VPS test scripts...")
    cmds = [
        "rm -f /root/iagent_pay_app/live_*.py",
        "rm -f /root/inject_500.py",
        "rm -f /root/iagent_pay_app/agent_errors.db",
        "rm -f /root/iagent_pay_app/agent_history.db",
        "rm -f /root/iagent_pay_app/agent_marketplace.db",
        "rm -f /root/iagent_pay_app/agent_reputation.db"
    ]
    # Note: deleting the .db files is safe because PostgreSQL is being used! 
    # Any residual SQLite files are garbage.
    
    for cmd in cmds:
        _, out, err = ssh.exec_command(cmd)
        print(f"Executed: {cmd}")
        
    ssh.close()

if __name__ == "__main__":
    cleanup_vps()
