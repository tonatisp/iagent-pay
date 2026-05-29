import paramiko
import json

def verify_vps():
    print("Verificando endpoints en el VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect('187.124.76.64', username='root', password='Santsantillan2-')
        
        checks = {
            'Servicio activo': 'systemctl is-active iagent-pay',
            'HTTP /api/admin/escrows': 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/admin/escrows',
            'HTTP /api/admin/forensics': 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/admin/forensics',
            'JSON escrows': 'curl -s http://localhost:8000/api/admin/escrows',
            'JSON forensics': 'curl -s http://localhost:8000/api/admin/forensics',
        }
        
        for label, cmd in checks.items():
            _, stdout, _ = ssh.exec_command(cmd)
            out = stdout.read().decode().strip()
            # Truncate output for JSON responses to keep it readable
            if out.startswith('{'):
                print(f"{label}: {out[:150]}...")
            else:
                print(f"{label}: {out}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    verify_vps()
