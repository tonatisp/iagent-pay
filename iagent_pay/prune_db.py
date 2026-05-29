import sqlite3
import time
import os

def prune_database(db_path: str, retain_days: int = 30):
    """
    Elimina registros antiguos de la base de datos para ahorrar espacio (Pruning).
    Ejecuta un comando VACUUM para recuperar el espacio en el disco duro.
    """
    if not os.path.exists(db_path):
        print(f"Base de datos no encontrada: {db_path}")
        return

    print(f"🚀 Iniciando Pruning en {db_path} (Reteniendo {retain_days} días)...")
    try:
        from .db_adapter import DBAdapter
        adapter = DBAdapter(db_path)
        conn = adapter.connect()
        c = conn.cursor()
        
        # Calcular el timestamp de corte
        cutoff_timestamp = time.time() - (retain_days * 86400)
        
        # Eliminar transacciones antiguas
        c.execute("DELETE FROM transactions WHERE timestamp < ?", (cutoff_timestamp,))
        deleted_txs = c.rowcount
        
        # Eliminar facturas antiguas
        try:
            c.execute("DELETE FROM paid_invoices WHERE timestamp < ?", (cutoff_timestamp,))
            deleted_invs = c.rowcount
        except Exception:
            deleted_invs = 0

        conn.commit()
        
        print(f"✅ Eliminadas {deleted_txs} transacciones y {deleted_invs} facturas antiguas.")
        print("⏳ Ejecutando VACUUM para desfragmentar el disco (puede demorar)...")
        
        # VACUUM reconstruye el archivo de la BD eliminando el espacio libre.
        # En Postgres no se puede correr dentro de un bloque de transaccion.
        if hasattr(adapter, 'is_postgres') and adapter.is_postgres:
            # Set autocommit to True for VACUUM in Postgres
            conn.conn.autocommit = True
            try:
                conn.execute("VACUUM;")
            finally:
                conn.conn.autocommit = False
        else:
            conn.execute("VACUUM;")
        
        print(f"🎉 Pruning completado con éxito en {db_path}.")
        conn.close()
    except Exception as e:
        print(f"❌ Error durante el pruning de {db_path}: {e}")

if __name__ == "__main__":
    # Si se ejecuta directamente, poda la base local
    target_dbs = ["agent_history.db", "transactions.db"]
    for db in target_dbs:
        db_full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db)
        if os.path.exists(db_full_path):
            prune_database(db_full_path, retain_days=30)
        else:
            # Intentar en el directorio actual
            if os.path.exists(db):
                prune_database(db, retain_days=30)
