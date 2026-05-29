import paramiko
import os
import sys

def run_remote_test():
    host = os.environ.get("VPS_HOST", "187.124.76.64")
    port = int(os.environ.get("VPS_PORT", 22))
    username = os.environ.get("VPS_USER", "root")
    password = os.environ.get("VPS_PASS", "Santsantillan2-")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"[*] Connecting to {host}...")
    try:
        ssh.connect(host, port, username, password)
        print("[+] Connected successfully! Launching test_corporate_20M.py...")
        
        # We run it using python3 inside the app directory
        cmd = "cd /root/iagent_pay_app && python3 test_corporate_20M.py"
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        
        for line in iter(stdout.readline, ""):
            try:
                print(line.strip())
            except UnicodeEncodeError:
                print(line.encode('ascii', 'replace').decode('ascii').strip())
        
        exit_status = stdout.channel.recv_exit_status()
        print(f"\n[*] Remote test finished with status: {exit_status}")
        
    except Exception as e:
        print(f"[-] Error: {str(e)}")
    finally:
        ssh.close()

if __name__ == "__main__":
    run_remote_test()
