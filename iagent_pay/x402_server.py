"""
iAgentPay — x402 Protocol Server Middleware
Protect FastAPI or Flask endpoints with automatic USDC payment gating.

Security hardening v4.0:
  - Receipts are now persisted in SQLite (survive server restarts)
  - Duplicate receipt detection is restart-safe
  - Nonce expiry validation added (5-minute window)
"""
import json
import time
import sqlite3
import threading
import logging
from functools import wraps
from typing import Optional, Callable

logger = logging.getLogger("iagentpay.x402.server")

HEADER_PAYMENT_REQUIRED  = "X-Payment-Required"
HEADER_PAYMENT_SIGNATURE = "X-Payment-Signature"
HEADER_PAYMENT_RECEIPT   = "X-Payment-Receipt"
HEADER_PAYMENT_NONCE     = "X-Payment-Nonce"

RECEIPT_DB_PATH = "x402_receipts.db"


# ─── Persistent Receipt Store ─────────────────────────────────────────────────

class ReceiptStore:
    """
    SQLite-backed receipt store. Survives server restarts.
    Prevents double-spend attacks even after process crashes.
    """

    def __init__(self, db_path: str = RECEIPT_DB_PATH):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect_db(self):
        from .db_adapter import DBAdapter
        adapter = DBAdapter(self._db_path)
        return adapter.connect()

    def _init_db(self):
        conn = self._connect_db()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS used_receipts (
                    receipt     TEXT PRIMARY KEY,
                    path        TEXT,
                    amount_usdc REAL,
                    used_at     REAL NOT NULL,
                    expires_at  REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON used_receipts(expires_at)
            """)
            conn.commit()
        finally:
            conn.close()

    def is_used(self, receipt: str) -> bool:
        """Returns True if this receipt has already been used (duplicate spend)."""
        with self._lock:
            conn = self._connect_db()
            try:
                row = conn.execute(
                    "SELECT 1 FROM used_receipts WHERE receipt = ?", (receipt,)
                ).fetchone()
                return row is not None
            finally:
                conn.close()

    def mark_used(self, receipt: str, path: str = "", amount_usdc: float = 0.0,
                  ttl_seconds: int = 86400):
        """Mark a receipt as used. It will be retained for ttl_seconds (default 24h)."""
        now = time.time()
        with self._lock:
            conn = self._connect_db()
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO used_receipts VALUES (?, ?, ?, ?, ?)",
                    (receipt, path, amount_usdc, now, now + ttl_seconds)
                )
                conn.commit()
            finally:
                conn.close()

    def cleanup_expired(self):
        """Remove receipts older than their TTL (call periodically)."""
        with self._lock:
            conn = self._connect_db()
            try:
                deleted = conn.execute(
                    "DELETE FROM used_receipts WHERE expires_at < ?", (time.time(),)
                ).rowcount
                conn.commit()
            finally:
                conn.close()
        if deleted:
            logger.info(f"[x402] Cleaned up {deleted} expired receipts.")


def _build_payment_instructions(
    payment_address: str,
    amount_usdc: float,
    network: str = "BASE",
    description: str = "API Access",
) -> dict:
    now = int(time.time())
    return {
        "version":     "x402/1.0",
        "address":     payment_address,
        "amount":      amount_usdc,
        "currency":    "USDC",
        "network":     network,
        "description": description,
        "nonce":       str(now),
        "expires_at":  now + 300,   # 5-minute payment window
    }


def _is_nonce_expired(nonce_str: str, tolerance: int = 300) -> bool:
    """Returns True if the nonce timestamp is older than tolerance seconds."""
    try:
        nonce_ts = int(nonce_str)
        return abs(time.time() - nonce_ts) > tolerance
    except (ValueError, TypeError):
        return True  # Malformed nonce = reject


# ─── FastAPI Middleware ───────────────────────────────────────────────────────

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    class X402Middleware(BaseHTTPMiddleware):
        """
        FastAPI/Starlette middleware for x402 payment gating.
        Hardened v4.0: receipts persisted in SQLite, nonce expiry checked.

        Usage:
            app.add_middleware(
                X402Middleware,
                payment_address="0x...",
                amount_usdc=0.10,
                protected_paths=["/premium", "/api/v2"],
            )
        """
        def __init__(self, app, payment_address: str, amount_usdc: float = 0.10,
                     network: str = "BASE", protected_paths: Optional[list] = None,
                     skip_verification: bool = False,
                     receipt_db: str = RECEIPT_DB_PATH):
            super().__init__(app)
            self.payment_address   = payment_address
            self.amount_usdc       = amount_usdc
            self.network           = network
            self.protected_paths   = protected_paths or []
            self.skip_verification = skip_verification
            self._receipts         = ReceiptStore(receipt_db)

        async def dispatch(self, request, call_next):
            path = request.url.path
            needs_payment = (not self.protected_paths or
                             any(path.startswith(p) for p in self.protected_paths))

            if not needs_payment:
                return await call_next(request)

            sig     = request.headers.get(HEADER_PAYMENT_SIGNATURE)
            receipt = request.headers.get(HEADER_PAYMENT_RECEIPT)
            nonce   = request.headers.get(HEADER_PAYMENT_NONCE)

            # No payment headers → return 402 with instructions
            if not sig or not receipt:
                instructions = _build_payment_instructions(
                    self.payment_address, self.amount_usdc, self.network)
                return JSONResponse(
                    status_code=402,
                    content={"error": "Payment Required",
                             "message": f"This endpoint costs {self.amount_usdc} USDC",
                             "payment": instructions},
                    headers={HEADER_PAYMENT_REQUIRED: json.dumps(instructions)},
                )

            if not self.skip_verification:
                # 1. Check nonce freshness (prevent replay of old payments)
                if nonce and _is_nonce_expired(nonce):
                    return JSONResponse(status_code=402,
                                       content={"error": "Payment nonce expired. Please re-initiate payment."})

                # 🚨 CRITICAL VULNERABILITY MITIGATION WARNING:
                # Currently, this middleware ONLY checks for duplicate receipts to prevent replay attacks.
                # It DOES NOT connect to an RPC node to verify that the `receipt` (TxHash) actually transferred
                # the `self.amount_usdc` to `self.payment_address` on the blockchain.
                # TODO: Implement an `rpc_verify_receipt(receipt, self.payment_address, self.amount_usdc)` callback!
                
                # 2. Check duplicate receipt (persistent, survives restarts)
                if self._receipts.is_used(receipt):
                    logger.warning(f"[x402] Duplicate receipt attempt: {receipt[:16]}... on {path}")
                    return JSONResponse(status_code=402,
                                       content={"error": "Duplicate payment receipt. Each payment can only be used once."})

                # 3. Mark receipt as used in SQLite
                self._receipts.mark_used(receipt, path=path, amount_usdc=self.amount_usdc)

            logger.info(f"[x402] ✅ Payment accepted for {path} (receipt: {receipt[:16]}...)")
            return await call_next(request)

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# ─── Flask Decorator ──────────────────────────────────────────────────────────

_flask_receipt_store: Optional[ReceiptStore] = None

def _get_flask_store(db_path: str = RECEIPT_DB_PATH) -> ReceiptStore:
    global _flask_receipt_store
    if _flask_receipt_store is None:
        _flask_receipt_store = ReceiptStore(db_path)
    return _flask_receipt_store


def x402_flask(amount_usdc: float, payment_address: str,
               network: str = "BASE", description: str = "API Access",
               skip_verification: bool = False):
    """
    Flask route decorator for x402 payment gating.
    Hardened v4.0: receipts persisted in SQLite.

    @app.route("/premium")
    @x402_flask(amount_usdc=0.10, payment_address="0x...")
    def premium():
        return jsonify({"data": "premium content"})
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                from flask import request, jsonify, make_response
                sig     = request.headers.get(HEADER_PAYMENT_SIGNATURE)
                receipt = request.headers.get(HEADER_PAYMENT_RECEIPT)
                nonce   = request.headers.get(HEADER_PAYMENT_NONCE)

                if not sig or not receipt:
                    instructions = _build_payment_instructions(
                        payment_address, amount_usdc, network, description)
                    resp = make_response(
                        jsonify({"error": "Payment Required", "payment": instructions}), 402)
                    resp.headers[HEADER_PAYMENT_REQUIRED] = json.dumps(instructions)
                    return resp

                if not skip_verification:
                    store = _get_flask_store()
                    if nonce and _is_nonce_expired(nonce):
                        return make_response(
                            jsonify({"error": "Payment nonce expired."}), 402)
                    if store.is_used(receipt):
                        logger.warning(f"[x402/Flask] Duplicate receipt: {receipt[:16]}...")
                        return make_response(
                            jsonify({"error": "Duplicate payment receipt."}), 402)
                    store.mark_used(receipt, path=request.path, amount_usdc=amount_usdc)

            except ImportError:
                pass
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ─── FastAPI Route Decorator ──────────────────────────────────────────────────

def require_payment(amount_usdc: float, payment_address: str,
                    network: str = "BASE", description: str = "API Access",
                    skip_verification: bool = False):
    """
    FastAPI route decorator for per-endpoint payment gating.
    Hardened v4.0: receipts persisted in SQLite.
    """
    _store = ReceiptStore()

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if request:
                sig     = request.headers.get(HEADER_PAYMENT_SIGNATURE)
                receipt = request.headers.get(HEADER_PAYMENT_RECEIPT)
                nonce   = request.headers.get(HEADER_PAYMENT_NONCE)

                if not sig or not receipt:
                    instructions = _build_payment_instructions(
                        payment_address, amount_usdc, network, description)
                    if FASTAPI_AVAILABLE:
                        return JSONResponse(
                            status_code=402,
                            content={"error": "Payment Required", "payment": instructions},
                            headers={HEADER_PAYMENT_REQUIRED: json.dumps(instructions)},
                        )

                if not skip_verification:
                    if nonce and _is_nonce_expired(nonce):
                        return JSONResponse(status_code=402,
                                           content={"error": "Payment nonce expired."})
                    if receipt and _store.is_used(receipt):
                        return JSONResponse(status_code=402,
                                           content={"error": "Duplicate payment receipt."})
                    if receipt:
                        _store.mark_used(receipt, amount_usdc=amount_usdc)

            return await func(*args, **kwargs)
        return wrapper
    return decorator
