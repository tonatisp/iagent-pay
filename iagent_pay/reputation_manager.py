import sqlite3
import time
from typing import Dict, Any, List

class ReputationManager:
    def __init__(self, agent):
        self.agent = agent
        self.db_path = "agent_reputation.db"
        self._init_db()

    def _init_db(self):
        """Initializes the reputation database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Peers table: stores scores given by this agent to others
        c.execute('''CREATE TABLE IF NOT EXISTS peer_ratings
                     (address TEXT PRIMARY KEY, score REAL, reviews_count INTEGER, last_updated REAL)''')
        # Global cache: could be synced with a decentralized registry in the future
        c.execute('''CREATE TABLE IF NOT EXISTS global_cache
                     (address TEXT PRIMARY KEY, trust_score REAL, category TEXT)''')
        conn.commit()
        conn.close()

    def rate_peer(self, address: str, score: float):
        """
        Rates a peer agent (0.0 to 5.0).
        Usually called after a successful transaction or service delivery.
        """
        if not (0 <= score <= 5):
            raise ValueError("Score must be between 0 and 5")

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Simple weighted average for local trust
        c.execute("SELECT score, reviews_count FROM peer_ratings WHERE address = ?", (address,))
        row = c.fetchone()
        
        if row:
            old_score, count = row
            new_count = count + 1
            new_score = ((old_score * count) + score) / new_count
            c.execute("UPDATE peer_ratings SET score = ?, reviews_count = ?, last_updated = ? WHERE address = ?",
                      (new_score, new_count, time.time(), address))
        else:
            c.execute("INSERT INTO peer_ratings VALUES (?, ?, ?, ?)",
                      (address, score, 1, time.time()))
        
        conn.commit()
        conn.close()
        print(f"⭐ [Reputation] Rated {address} with {score}. New internal trust: {self.get_trust_score(address):.2f}")

    def get_trust_score(self, address: str) -> float:
        """Returns the local trust score for an address. Default: 3.0 (Neutral)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT score FROM peer_ratings WHERE address = ?", (address,))
        row = c.fetchone()
        conn.close()
        
        return row[0] if row else 3.0

    def get_top_agents(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns a list of most trusted peer agents."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT address, score FROM peer_ratings ORDER BY score DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        
        return [{"address": r[0], "score": r[1]} for r in rows]
