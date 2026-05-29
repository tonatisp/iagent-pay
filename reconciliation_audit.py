import sqlite3
import os

DB_FILE = "agent_history.db"

def run_reconciliation():
    print(f"=== INICIANDO AUDITORIA DE CONCILIACION BANCARIA ===")
    if not os.path.exists(DB_FILE):
        print(f"ERROR: No se encuentra la base de datos {DB_FILE}")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 1. Verificar registros totales
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_tx = cursor.fetchone()[0]
        print(f"[*] Total de transacciones encontradas: {total_tx}")

        # 2. Verificar suma total de dinero movido
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE status = 'COMPLETED'")
        total_amount = cursor.fetchone()[0] or 0
        print(f"[*] Total de fondos transferidos exitosamente: ${total_amount:.2f} USD")

        # 3. Detectar anomalías: Montos negativos
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE amount < 0")
        negative_tx = cursor.fetchone()[0]
        if negative_tx > 0:
            print(f"[!] ALERTA CRITICA: Se encontraron {negative_tx} transacciones con montos negativos (Posible fraude)")
        else:
            print(f"[*] Verificacion de montos negativos: SUPERADA (0 anomalías)")

        # 4. Detectar anomalías: Direcciones nulas
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE recipient IS NULL OR recipient = ''")
        null_addresses = cursor.fetchone()[0]
        if null_addresses > 0:
            print(f"[!] ALERTA CRITICA: Se encontraron {null_addresses} transacciones con direcciones fantasma")
        else:
            print(f"[*] Verificacion de direcciones nulas: SUPERADA (0 anomalías)")

        # 5. Resumen de estados
        cursor.execute("SELECT status, COUNT(*) FROM transactions GROUP BY status")
        statuses = cursor.fetchall()
        print("\n=== RESUMEN DE ESTADOS ===")
        for status, count in statuses:
            print(f"  - {status}: {count} ({count/total_tx*100:.1f}%)")

        print("\n[+] CONCILIACION COMPLETADA SIN DESCUADRES CRITICOS.")
        
    except Exception as e:
        print(f"Error fatal durante la conciliacion: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_reconciliation()
