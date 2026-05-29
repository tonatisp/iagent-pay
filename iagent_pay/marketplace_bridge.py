import time
import uuid
import hashlib
import json
import os
from typing import Dict, Any, List

class MarketplaceBridge:
    def __init__(self, agent):
        self.agent = agent
        self.db_path = "agent_marketplace.db"
        self._init_db()

    def _connect_db(self):
        from .db_adapter import DBAdapter
        adapter = DBAdapter(self.db_path)
        return adapter.connect()

    def _init_db(self):
        """Initializes the marketplace/bounty database."""
        conn = self._connect_db()
        c = conn.cursor()
        # Bounties table: stores tasks posted by this agent for humans
        c.execute('''CREATE TABLE IF NOT EXISTS bounties
                     (id TEXT PRIMARY KEY, title TEXT, reward_usd REAL, status TEXT, created_at REAL)''')
        # Escrow contracts: Anti-Hallucination Pay-on-Success
        c.execute('''CREATE TABLE IF NOT EXISTS escrow_contracts
                     (id TEXT PRIMARY KEY, recipient TEXT, amount_usd REAL, status TEXT,
                      task_description TEXT, created_at REAL, resolved_at REAL)''')
        conn.commit()
        conn.close()

    def post_bounty(self, title: str, reward_usd: float) -> str:
        """
        Posts a bounty for a human to complete.
        In a real scenario, this would sync with an external API (e.g., Mechanical Turk or a Web3 Bounty Board).
        """
        bounty_id = str(uuid.uuid4())[:8]
        
        conn = self._connect_db()
        c = conn.cursor()
        c.execute("INSERT INTO bounties VALUES (?, ?, ?, ?, ?)",
                  (bounty_id, title, reward_usd, "OPEN", time.time()))
        conn.commit()
        conn.close()
        
        print(f"🤝 [Marketplace] Bounty Posted: '{title}' for ${reward_usd:.2f}. ID: {bounty_id}")
        return bounty_id

    def list_my_bounties(self) -> List[Dict[str, Any]]:
        """Returns all bounties posted by this agent."""
        conn = self._connect_db()
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
        conn = self._connect_db()
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

    # ─── SMART ESCROW (Anti-Hallucination Pay-on-Success) ─────────────────────

    def create_smart_escrow(
        self, amount_usd: float, recipient: str, task_description: str
    ) -> str:
        """
        Locks funds for a task until success/failure is confirmed.
        No money leaves the system until `resolve_smart_escrow` is called.

        Returns:
            escrow_id: The ID to use when resolving the escrow.
        """
        import math
        try:
            amount_usd = float(amount_usd)
            if math.isnan(amount_usd) or math.isinf(amount_usd) or amount_usd < 0:
                raise ValueError("Monto inválido para Escrow")
        except (ValueError, TypeError):
            raise ValueError("Monto inválido para Escrow")

        escrow_id = "escrow_" + str(uuid.uuid4())[:12]
        conn = self._connect_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO escrow_contracts VALUES (?, ?, ?, ?, ?, ?, ?)",
            (escrow_id, recipient, amount_usd, "LOCKED", task_description, time.time(), None)
        )
        conn.commit()
        conn.close()
        print(f"🔐 [SmartEscrow] Funds LOCKED: ${amount_usd:.2f} for task → '{task_description}' (ID: {escrow_id})")
        return escrow_id

    def resolve_smart_escrow(self, escrow_id: str, success: bool) -> Dict[str, Any]:
        """
        Resolves an open escrow contract.
          - success=True  → Releases payment to recipient (agent did a great job).
          - success=False → Refunds the full amount back to the owner (agent hallucinated).
        """
        now = time.time()
        conn = self._connect_db()
        c = conn.cursor()
        
        # Atomic Lock to prevent Race Conditions (Double-Spend)
        c.execute("UPDATE escrow_contracts SET status = 'PROCESSING', resolved_at = ? WHERE id = ? AND status = 'LOCKED'", (now, escrow_id))
        if c.rowcount == 0:
            conn.close()
            raise ValueError(f"[SmartEscrow] Escrow '{escrow_id}' is already resolved, processing, or not found.")
            
        c.execute("SELECT recipient, amount_usd, task_description FROM escrow_contracts WHERE id = ?", (escrow_id,))
        row = c.fetchone()
        
        recipient, amount_usd, task = row

        if success:
            # ✅ Task completed correctly — pay the recipient
            try:
                native_price = self.agent.pricing.get_native_price()
            except Exception:
                native_price = 2500.0
            amount_native = amount_usd / native_price
            self.agent.pay_agent(recipient, amount_native)
            new_status = "RELEASED"
            print(f"✅ [SmartEscrow] RELEASED: ${amount_usd:.2f} → {recipient} | Task: '{task}'")
        else:
            # ❌ Agent hallucinated or failed — 100% refund to owner
            new_status = "REFUNDED"
            print(f"🔴 [SmartEscrow] REFUNDED: ${amount_usd:.2f} returned to owner. Agent failed task: '{task}'")

        c.execute("UPDATE escrow_contracts SET status = ? WHERE id = ?", (new_status, escrow_id))
        conn.commit()
        conn.close()

        return {
            "escrow_id": escrow_id,
            "status": new_status,
            "amount_usd": amount_usd,
            "recipient": recipient,
            "task": task,
            "resolved_at": now,
        }

    def list_escrows(self, status_filter: str = None) -> List[Dict[str, Any]]:
        """Lists all escrow contracts, optionally filtered by status (LOCKED/RELEASED/REFUNDED)."""
        conn = self._connect_db()
        c = conn.cursor()
        if status_filter:
            c.execute("SELECT id, recipient, amount_usd, status, task_description, created_at FROM escrow_contracts WHERE status = ?",
                      (status_filter.upper(),))
        else:
            c.execute("SELECT id, recipient, amount_usd, status, task_description, created_at FROM escrow_contracts")
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "recipient": r[1], "amount_usd": r[2], "status": r[3],
                 "task": r[4], "created_at": r[5]} for r in rows]


