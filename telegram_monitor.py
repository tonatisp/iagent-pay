import os
import sqlite3
import time
import requests
import psutil

DB_FILE = "/root/iagent_pay_app/agent_history.db"
# Para probar de forma local antes de subir al VPS:
if not os.path.exists(DB_FILE):
    DB_FILE = "agent_history.db"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[SIMULACION TELEGRAM] -> {message}".encode('utf-8', 'replace').decode('utf-8', 'replace'))
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")

def get_aml_alerts():
    if not os.path.exists(DB_FILE): return 0
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Verificamos cuantas alertas AML ocurrieron en la ultima hora
        # asumiendo que timestamp es un epoch time
        one_hour_ago = time.time() - 3600
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE status = 'SANCTIONED_AML' AND timestamp > ?", (one_hour_ago,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(e)
        return 0

def monitor_system():
    print("Iniciando Monitor de Telemetría (iAgent-Pay)...")
    
    # 1. Chequear CPU y Memoria (VPS Health)
    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk_path = 'C:\\' if os.name == 'nt' else '/'
    try:
        disk = psutil.disk_usage(disk_path)
        disk_percent = disk.percent
    except:
        disk_percent = 50.0
    
    alert_msg = "<b>[iAgent-Pay Reporte de Salud]</b>\n\n"
    
    is_critical = False
    
    if cpu_usage > 90:
        alert_msg += f"[ALERTA CRITICA] CPU al {cpu_usage}%\n"
        is_critical = True
    else:
        alert_msg += f"[OK] CPU Normal: {cpu_usage}%\n"
        
    if mem.percent > 90:
        alert_msg += f"[ALERTA CRITICA] RAM al {mem.percent}%\n"
        is_critical = True
    else:
        alert_msg += f"[OK] RAM Normal: {mem.percent}%\n"
        
    if disk_percent > 90:
        alert_msg += f"[ALERTA CRITICA] Disco al {disk_percent}%\n"
        is_critical = True
        
    # 2. Chequear Seguridad AML
    aml_blocks = get_aml_alerts()
    if aml_blocks > 0:
        alert_msg += f"[SEGURIDAD] Se bloquearon {aml_blocks} transacciones AML/OFAC en la ultima hora.\n"
        is_critical = True
        
    # 3. Enviar alerta si es crítico o si es un reporte diario (simulado para siempre mandar ahora)
    if is_critical or True:  # Forzamos True para probar
        send_telegram_message(alert_msg)
        
if __name__ == "__main__":
    monitor_system()
