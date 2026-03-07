import sqlite3
import time
import uuid
from typing import Dict, Any, List

class MarketplaceBridge:
    def __init__(self, agent):
        self.agent = agent
        self.db_path = "agent_marketplace.db"
        self._init_db()

    def _init_db(self):
        """Initializes the marketplace/bounty database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Bounties table: stores tasks posted by this agent for humans
        c.execute('''CREATE TABLE IF NOT EXISTS bounties
                     (id TEXT PRIMARY KEY, title TEXT, reward_usd REAL, status TEXT, created_at REAL)''')
        conn.commit()
        conn.close()

    def post_bounty(self, title: str, reward_usd: float) -> str:
        """
        Posts a bounty for a human to complete.
        In a real scenario, this would sync with an external API (e.g., Mechanical Turk or a Web3 Bounty Board).
        """
        bounty_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO bounties VALUES (?, ?, ?, ?, ?)",
                  (bounty_id, title, reward_usd, "OPEN", time.time()))
        conn.commit()
        conn.close()
        
        print(f"🤝 [Marketplace] Bounty Posted: '{title}' for ${reward_usd:.2f}. ID: {bounty_id}")
        return bounty_id

    def list_my_bounties(self) -> List[Dict[str, Any]]:
        """Returns all bounties posted by this agent."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, title, reward_usd, status FROM bounties")
        rows = c.fetchall()
        conn.close()
        
        return [{"id": r[0], "title": r[1], "reward": r[2], "status": r[3]} for r in rows]

    def release_payment(self, bounty_id: str, human_address: str):
        """
        Releases the payment to the human once the task is verified.
        Uses the agent's payment logic.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT title, reward_usd, status FROM bounties WHERE id = ?", (bounty_id,))
        row = c.fetchone()
        
        if not row:
            raise ValueError("Bounty not found")
        if row[2] != "OPEN":
            raise ValueError("Bounty is not open for payment")

        title, reward_usd, status = row
        
        print(f"🤝 [Marketplace] Releasing ${reward_usd:.2f} to {human_address} for task: {title}")
        
        # Calculate amount in native token (simplified: use $2500 per ETH as mock price if price oracle fails)
        try:
            native_price = self.agent.pricing.get_native_price()
        except:
            native_price = 2500.0
            
        amount_native = reward_usd / native_price
        
        # Execute Payment through Agent
        self.agent.pay_agent(human_address, amount_native)
        
        # Update Status
        c.execute("UPDATE bounties SET status = 'PAID' WHERE id = ?", (bounty_id,))
        conn.commit()
        conn.close()
        
        print(f"✅ [Marketplace] Payment Released for Bounty {bounty_id}")
