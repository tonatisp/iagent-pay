"""
iAgentPay — x402 Protocol Server Middleware
Protect FastAPI or Flask endpoints with automatic USDC payment gating.
"""
import json
import time
import logging
from functools import wraps
from typing import Optional, Callable

logger = logging.getLogger("iagentpay.x402.server")

HEADER_PAYMENT_REQUIRED  = "X-Payment-Required"
HEADER_PAYMENT_SIGNATURE = "X-Payment-Signature"
HEADER_PAYMENT_RECEIPT   = "X-Payment-Receipt"


def _build_payment_instructions(
    payment_address: str,
    amount_usdc: float,
    network: str = "BASE_SEPOLIA",
    description: str = "API Access",
) -> dict:
    return {
        "version":     "x402/1.0",
        "address":     payment_address,
        "amount":      amount_usdc,
        "currency":    "USDC",
        "network":     network,
        "description": description,
        "nonce":       str(int(time.time())),
        "expires_at":  int(time.time()) + 300,
    }


# ─── FastAPI Middleware ───────────────────────────────────────────────────────

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    class X402Middleware(BaseHTTPMiddleware):
        """
        FastAPI/Starlette middleware for x402 payment gating.

        Usage:
            app.add_middleware(
                X402Middleware,
                payment_address="0x...",
                amount_usdc=0.10,
                protected_paths=["/premium", "/api/v2"],
            )
        """
        def __init__(self, app, payment_address: str, amount_usdc: float = 0.10,
                     network: str = "BASE_SEPOLIA", protected_paths: Optional[list] = None,
                     skip_verification: bool = False):
            super().__init__(app)
            self.payment_address   = payment_address
            self.amount_usdc       = amount_usdc
            self.network           = network
            self.protected_paths   = protected_paths or []
            self.skip_verification = skip_verification
            self._paid_receipts: set = set()

        async def dispatch(self, request, call_next):
            path = request.url.path
            needs_payment = (not self.protected_paths or
                             any(path.startswith(p) for p in self.protected_paths))

            if not needs_payment:
                return await call_next(request)

            sig     = request.headers.get(HEADER_PAYMENT_SIGNATURE)
            receipt = request.headers.get(HEADER_PAYMENT_RECEIPT)

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
                if receipt in self._paid_receipts:
                    return JSONResponse(status_code=402,
                                       content={"error": "Duplicate payment receipt"})
                self._paid_receipts.add(receipt)

            logger.info(f"[x402] Payment verified for {path} (tx: {receipt})")
            return await call_next(request)

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# ─── Flask Decorator ──────────────────────────────────────────────────────────

def x402_flask(amount_usdc: float, payment_address: str,
               network: str = "BASE_SEPOLIA", description: str = "API Access"):
    """
    Flask route decorator for x402 payment gating.

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
                sig = request.headers.get(HEADER_PAYMENT_SIGNATURE)
                if not sig:
                    instructions = _build_payment_instructions(
                        payment_address, amount_usdc, network, description)
                    resp = make_response(
                        jsonify({"error": "Payment Required", "payment": instructions}), 402)
                    resp.headers[HEADER_PAYMENT_REQUIRED] = json.dumps(instructions)
                    return resp
            except ImportError:
                pass
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ─── FastAPI Route Decorator ──────────────────────────────────────────────────

def require_payment(amount_usdc: float, payment_address: str,
                    network: str = "BASE_SEPOLIA", description: str = "API Access"):
    """
    FastAPI route decorator for per-endpoint payment gating.

    @app.get("/premium")
    @require_payment(amount_usdc=0.05, payment_address="0x...")
    async def premium_endpoint(request: Request):
        return {"data": "premium content"}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if request and not request.headers.get(HEADER_PAYMENT_SIGNATURE):
                instructions = _build_payment_instructions(
                    payment_address, amount_usdc, network, description)
                if FASTAPI_AVAILABLE:
                    return JSONResponse(
                        status_code=402,
                        content={"error": "Payment Required", "payment": instructions},
                        headers={HEADER_PAYMENT_REQUIRED: json.dumps(instructions)},
                    )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
