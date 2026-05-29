import paramiko
import os
import glob

VPS_IP = "187.124.76.64"
VPS_USER = "root"
VPS_PASS = "Santsantillan2-"
REMOTE_ROOT = "/root/iagent_pay_app"

def reset_databases():
    print("[Reset] Connecting to VPS via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)
        print("[Reset] Connection established!")

        # 1. Stop the remote service to prevent database file locks
        print("[Reset] Stopping iagent-pay service on VPS...")
        ssh.exec_command("systemctl stop iagent-pay")
        import time
        time.sleep(2)

        # 2. Delete database files on VPS
        print("[Reset] Deleting database files on VPS...")
        stdin, stdout, stderr = ssh.exec_command(f"rm -f {REMOTE_ROOT}/*.db*")
        err = stderr.read().decode().strip()
        if err:
            print(f"[Reset] Remote delete stderr: {err}")

        # 3. Start the service (it will dynamically auto-create empty, clean DB files)
        print("[Reset] Starting iagent-pay service on VPS...")
        ssh.exec_command("systemctl start iagent-pay")
        time.sleep(2)

        # Verify status
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active iagent-pay")
        status = stdout.read().decode().strip()
        print(f"[Reset] Remote Service Status: {status}")
        ssh.close()
        
    except Exception as e:
        print(f"[Reset] VPS Error: {e}")

    # 4. Local Reset in workspace
    print("[Reset] Deleting local database files in workspace...")
    local_dir = os.path.dirname(os.path.abspath(__file__))
    db_patterns = ["*.db*", "iagent_pay/*.db*"]
    for pattern in db_patterns:
        for filepath in glob.glob(os.path.join(local_dir, pattern)):
            try:
                os.remove(filepath)
                print(f"[Reset] Deleted local file: {filepath}")
            except Exception as le:
                print(f"[Reset] Failed to delete local file {filepath}: {le}")

    print("[Reset] Reset complete! Statistics and transaction history are now blank.")

if __name__ == "__main__":
    reset_databases()
