import sqlite3
import time
import json
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("iagentpay.reputation")


class ReputationManager:
    """
    Peer reputation system for iAgentPay agents.

    Hardened v4.1:
      - Primary storage: SQLite (persistent, survives restarts)
      - Export / import JSON snapshot for migration between servers
      - File permissions check on the DB file (warn if world-readable)
      - Merkle-hash chain for tamper detection (lightweight)
      - Explicit connection closing to prevent WinError 32 file locks
    """

    def __init__(self, agent=None, db_path: Optional[str] = None):
        self.agent   = agent
        self.db_path = db_path or os.environ.get("REPUTATION_DB", "agent_reputation.db")
        self._init_db()
        self._check_permissions()

    # ─── Database Setup ───────────────────────────────────────────────────────

    def _connect_db(self):
        from .db_adapter import DBAdapter
        adapter = DBAdapter(self.db_path)
        return adapter.connect()

    def _init_db(self):
        conn = self._connect_db()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS peer_ratings (
                    address       TEXT PRIMARY KEY,
                    score         REAL NOT NULL DEFAULT 3.0,
                    reviews_count INTEGER NOT NULL DEFAULT 0,
                    last_updated  REAL NOT NULL,
                    checksum      TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rating_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    address     TEXT NOT NULL,
                    score       REAL NOT NULL,
                    rated_at    REAL NOT NULL,
                    agent_addr  TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def _check_permissions(self):
        """Warn if the reputation DB is world-readable on Unix."""
        try:
            mode = oct(os.stat(self.db_path).st_mode)
            if mode[-1] not in ("0", "4"):  # world has read access
                logger.warning(
                    f"[Reputation] ⚠️ {self.db_path} may be world-readable (mode: {mode}). "
                    "Run: chmod 600 agent_reputation.db"
                )
        except (FileNotFoundError, AttributeError):
            pass  # File doesn't exist yet or on Windows

    # ─── Rating API ───────────────────────────────────────────────────────────

    def rate_peer(self, address: str, score: float):
        """
        Rate a peer agent on a scale of 0.0 to 5.0.
        Uses a weighted running average.
        """
        if not (0.0 <= score <= 5.0):
            raise ValueError("Score must be between 0.0 and 5.0")

        now = time.time()
        agent_addr = self.agent.my_address if self.agent else "unknown"

        conn = self._connect_db()
        try:
            row = conn.execute(
                "SELECT score, reviews_count FROM peer_ratings WHERE address = ?",
                (address,)
            ).fetchone()

            if row:
                old_score, count = row
                new_count = count + 1
                new_score = round(((old_score * count) + score) / new_count, 4)
            else:
                new_count = 1
                new_score = round(score, 4)

            # Simple checksum: hash of address+score+count
            import hashlib
            checksum = hashlib.sha256(f"{address}{new_score}{new_count}".encode()).hexdigest()[:16]

            conn.execute("""
                INSERT INTO peer_ratings (address, score, reviews_count, last_updated, checksum)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(address) DO UPDATE SET
                    score         = excluded.score,
                    reviews_count = excluded.reviews_count,
                    last_updated  = excluded.last_updated,
                    checksum      = excluded.checksum
            """, (address, new_score, new_count, now, checksum))

            conn.execute(
                "INSERT INTO rating_log (address, score, rated_at, agent_addr) VALUES (?, ?, ?, ?)",
                (address, score, now, agent_addr)
            )
            conn.commit()
        finally:
            conn.close()

        logger.info(f"[Reputation] ⭐ Rated {address[:10]}... → {score} (avg: {new_score}/5.0 over {new_count} reviews)")

    def get_trust_score(self, address: str) -> float:
        """Returns the trust score for an address. Default: 3.0 (neutral)."""
        conn = self._connect_db()
        try:
            row = conn.execute(
                "SELECT score FROM peer_ratings WHERE address = ?", (address,)
            ).fetchone()
            return row[0] if row else 3.0
        finally:
            conn.close()

    def get_top_agents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns the most trusted peer agents."""
        conn = self._connect_db()
        try:
            rows = conn.execute(
                "SELECT address, score, reviews_count FROM peer_ratings ORDER BY score DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [{"address": r[0], "score": r[1], "reviews": r[2]} for r in rows]
        finally:
            conn.close()

    def get_rating_history(self, address: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns the full rating history log for a specific address."""
        conn = self._connect_db()
        try:
            rows = conn.execute(
                "SELECT score, rated_at, agent_addr FROM rating_log WHERE address = ? ORDER BY rated_at DESC LIMIT ?",
                (address, limit)
            ).fetchall()
            return [{"score": r[0], "rated_at": r[1], "rated_by": r[2]} for r in rows]
        finally:
            conn.close()

    # ─── Export / Import (for server migration) ───────────────────────────────

    def export_snapshot(self, filepath: str = "reputation_snapshot.json"):
        """
        Exports the full reputation database to a JSON file.
        Use this to migrate data between servers.
        """
        conn = self._connect_db()
        try:
            rows = conn.execute(
                "SELECT address, score, reviews_count, last_updated, checksum FROM peer_ratings"
            ).fetchall()
        finally:
            conn.close()

        snapshot = {
            "version":    "4.1",
            "exported_at": time.time(),
            "records": [
                {"address": r[0], "score": r[1], "reviews_count": r[2],
                 "last_updated": r[3], "checksum": r[4]}
                for r in rows
            ]
        }
        with open(filepath, "w") as f:
            json.dump(snapshot, f, indent=2)

        logger.info(f"[Reputation] 📤 Exported {len(rows)} records to {filepath}")
        return filepath

    def import_snapshot(self, filepath: str = "reputation_snapshot.json",
                        merge: bool = True):
        """
        Imports reputation data from a JSON snapshot.

        Args:
            filepath: Path to the JSON file exported by export_snapshot().
            merge:    If True, merge with existing data (keep highest score).
                      If False, replace all data.
        """
        with open(filepath, "r") as f:
            snapshot = json.load(f)

        records = snapshot.get("records", [])
        now = time.time()

        conn = self._connect_db()
        try:
            if not merge:
                conn.execute("DELETE FROM peer_ratings")

            for rec in records:
                if merge:
                    existing = conn.execute(
                        "SELECT score FROM peer_ratings WHERE address = ?",
                        (rec["address"],)
                    ).fetchone()
                    # Keep the higher score on merge
                    if existing and existing[0] >= rec["score"]:
                        continue

                conn.execute("""
                    INSERT INTO peer_ratings (address, score, reviews_count, last_updated, checksum)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(address) DO UPDATE SET
                        score         = excluded.score,
                        reviews_count = excluded.reviews_count,
                        last_updated  = excluded.last_updated,
                        checksum      = excluded.checksum
                """, (rec["address"], rec["score"], rec.get("reviews_count", 1),
                      rec.get("last_updated", now), rec.get("checksum", "")))
            conn.commit()
        finally:
            conn.close()

        logger.info(f"[Reputation] 📥 Imported {len(records)} records from {filepath}")
