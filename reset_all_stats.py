#!/usr/bin/env python3
"""
reset_all_stats.py — Limpia TODAS las estadísticas y datos de prueba
tanto en el VPS como localmente.

Bases de datos afectadas:
  - agent_history.db   (tabla: transactions)
  - agent_reputation.db (tablas: peer_ratings, custom_licenses)
  - x402_receipts.db   (tabla: receipts)
"""

import os
import sqlite3
import sys
import time

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

VPS_IP   = "187.124.76.64"
VPS_USER = "root"
VPS_PASS = "Santsantillan2-"
REMOTE_ROOT = "/root/iagent_pay_app"

# All known locations of DB files on VPS (found via: find /root -name "*.db")
VPS_DB_PATHS = [
    "/root/agent_history.db",
    "/root/agent_reputation.db",
    "/root/iagent_pay_app/iagent_pay/agent_history.db",
    "/root/iagent_pay_app/x402_receipts.db",
    "/root/iagent_pay_app/agent_history.db",
    "/root/iagent_pay_app/agent_reputation.db",
]

DBS = [
    "agent_history.db",
    "agent_reputation.db",
    "x402_receipts.db",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reset_local_sqlite(db_path: str):
    """Borra el contenido de todas las tablas en un archivo SQLite local."""
    if not os.path.exists(db_path):
        print(f"  [local] No existe: {db_path}  (saltando)")
        return
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Obtener todas las tablas (excepto las del sistema SQLite)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            print(f"  [local] Tabla '{table}' vaciada en {os.path.basename(db_path)}")
        conn.commit()
        # VACUUM para compactar el archivo y que el tamaño refleje el estado limpio
        conn.execute("VACUUM")
        conn.close()
        print(f"  [local] ✓ {os.path.basename(db_path)} completamente limpia")
    except Exception as e:
        print(f"  [local] ERROR en {db_path}: {e}")


# ---------------------------------------------------------------------------
# VPS Reset via SSH
# ---------------------------------------------------------------------------

def reset_vps():
    print("\n========================================")
    print("  RESET REMOTO (VPS)")
    print("========================================")
    try:
        import paramiko
    except ImportError:
        print("  [VPS] paramiko no instalado — saltando reset remoto.")
        print("  Instala con:  pip install paramiko")
        return

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"  [VPS] Conectando a {VPS_IP}...")
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=15)
        print("  [VPS] Conexión establecida ✓")

        # 1. Detener el servicio
        print("  [VPS] Deteniendo servicio iagent-pay...")
        ssh.exec_command("systemctl stop iagent-pay 2>/dev/null; sleep 2")
        time.sleep(3)

        # 2. Limpiar PostgreSQL (fuente principal de datos del dashboard)
        print("  [VPS] Limpiando PostgreSQL (iagent_db)...")
        PG_URL = "postgresql://iagent_admin:Santsantillan2-DB@localhost:5432/iagent_db"
        pg_cmd = (
            f'psql "{PG_URL}" -c '
            '"TRUNCATE TABLE transactions, paid_invoices, compliance_logs RESTART IDENTITY CASCADE;" 2>&1'
        )
        stdin_pg, stdout_pg, stderr_pg = ssh.exec_command(pg_cmd)
        time.sleep(3)
        pg_out = stdout_pg.read().decode().strip()
        print(f"  [VPS] PostgreSQL: {pg_out}")

        # Verify PostgreSQL
        stdin_v, stdout_v, _ = ssh.exec_command(
            f'psql "{PG_URL}" -c "SELECT COUNT(*) FROM transactions;" 2>&1'
        )
        time.sleep(2)
        print(f"  [VPS] PostgreSQL transactions after reset: {stdout_v.read().decode().strip()}")

        for remote_path in VPS_DB_PATHS:
            db_name = remote_path.split("/")[-1]
            script = (
                f"python3 -c \""
                f"import sqlite3,os; p='{remote_path}'; "
                f"conn=sqlite3.connect(p) if os.path.exists(p) else None; "
                f"[setattr(conn,'_skip',True) if not os.path.exists(p) else None]; "
                f"exec(open('/dev/stdin').read()) if False else None"
                f"\""
            )
            # Use heredoc approach via exec_command
            heredoc = f"""python3 - << 'PYEOF'
import sqlite3, os
p = "{remote_path}"
if not os.path.exists(p):
    print("  [VPS] No existe: {remote_path}  (saltando)")
else:
    conn = sqlite3.connect(p)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [r[0] for r in cur.fetchall()]
    for t in tables:
        cur.execute("DELETE FROM " + t)
        print("  [VPS] Tabla " + t + " vaciada en {db_name}")
    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    print("  [VPS] OK {db_name} completamente limpia")
PYEOF"""
            stdin, stdout, stderr = ssh.exec_command(heredoc)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if out:
                print(out)
            if err and "Warning" not in err:
                print(f"  [VPS] stderr: {err}")


        # 3. Reiniciar el servicio
        print("  [VPS] Reiniciando servicio iagent-pay...")
        ssh.exec_command("systemctl start iagent-pay")
        time.sleep(3)

        # 4. Verificar estado
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active iagent-pay")
        status = stdout.read().decode().strip()
        icon = "✓" if status == "active" else "⚠"
        print(f"  [VPS] {icon} Estado del servicio: {status}")

        ssh.close()
        print("  [VPS] Reset remoto completado ✓")

    except Exception as e:
        print(f"  [VPS] ERROR de conexión: {e}")


# ---------------------------------------------------------------------------
# Local Reset
# ---------------------------------------------------------------------------

def reset_local():
    print("\n========================================")
    print("  RESET LOCAL")
    print("========================================")
    project_root = os.path.dirname(os.path.abspath(__file__))

    for db_name in DBS:
        db_path = os.path.join(project_root, db_name)
        reset_local_sqlite(db_path)

    print("  [local] Reset local completado ✓")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("============================================")
    print("   iAgentPay -- Reset Completo de Datos    ")
    print("============================================")
    print()

    # Confirmar antes de ejecutar
    confirm = input("⚠  Esto borrará TODAS las estadísticas y transacciones.\n   Escribe 'SI' para confirmar: ").strip().upper()
    if confirm != "SI":
        print("Operación cancelada.")
        sys.exit(0)

    reset_vps()
    reset_local()

    print()
    print("============================================")
    print("   OK Reset completo! Datos en blanco.     ")
    print("============================================")
