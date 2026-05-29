import http.server
import socketserver
import mimetypes
import sys
import os
import sqlite3
from iagent_pay.db_adapter import DBAdapter
from iagent_pay.alert_manager import AlertManager
from iagent_pay.session_keys import SessionKeyManager
import json
import time

try:
    from dotenv import load_dotenv
    # Load .env file automatically
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(env_path)
except ImportError:
    print("⚠️ python-dotenv not installed. Skipping .env loading.")
import secrets
import uuid
import base64
from eth_account.messages import encode_defunct
from eth_account import Account
from web3 import Web3

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import collections

# Global auth states
AUTH_CHALLENGES = {}  # challenge_token -> (challenge_text, timestamp, client_ip)
VALID_SESSIONS = {}   # valid session_id -> last_activity_timestamp
IP_RATE_LIMITS = collections.defaultdict(list)   # client_ip -> list of timestamps
IP_BANS = {}          # client_ip -> unban_timestamp

def is_rate_limited(ip):
    now = time.time()
    
    # 1. Check if IP is currently banned
    if ip in IP_BANS:
        if now < IP_BANS[ip]:
            return True # Still banned
        else:
            del IP_BANS[ip] # Unban
            
    # 2. Cleanup old timestamps (older than 10 seconds for burst calc)
    IP_RATE_LIMITS[ip] = [t for t in IP_RATE_LIMITS[ip] if now - t < 10.0]
    
    # 3. Burst Rate Limiting: Max 300 requests per 10 seconds
    if len(IP_RATE_LIMITS[ip]) >= 300:
        # Penalty: Ban for 5 minutes (300 seconds)
        print(f"[SECURITY] IP {ip} rate limited and banned for 5 minutes (DDoS prevention).")
        AlertManager.critical(
            "DDoS Prevention Triggered",
            f"La IP `{ip}` ha sido baneada por 5 minutos por exceder 300 peticiones en 10 segundos.\nEsto podría ser un ataque automatizado al panel de control."
        )
        IP_BANS[ip] = now + 300.0
        return True
        
    IP_RATE_LIMITS[ip].append(now)
    return False

# Enforce ECDSA signature verification parameters (secp256k1 curve order)
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SECP256K1_HALF_N = SECP256K1_N // 2

# Explicitly add/override MIME types to bypass Windows registry bugs
mimetypes.init()
mimetypes.types_map['.js'] = 'application/javascript'
mimetypes.types_map['.css'] = 'text/css'
mimetypes.types_map['.html'] = 'text/html'
mimetypes.types_map['.png'] = 'image/png'
mimetypes.types_map['.svg'] = 'image/svg+xml'

PORT = 8000
# Serve the project root folder (containing index.html, dashboard/, and docs/)
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_config.json")

_pricing_manager = None
_price_cache = {}
_price_cache_time = {}

def get_symbol_usd_price(symbol: str) -> float:
    global _pricing_manager, _price_cache, _price_cache_time
    if not symbol:
        return 1.0
    symbol = symbol.upper().strip()
    
    # Handle common stablecoins directly
    if symbol in ("USDC", "USDT", "DAI", "USDD", "FDUSD"):
        return 1.0
        
    # Check cache
    now = time.time()
    if symbol in _price_cache and (now - _price_cache_time.get(symbol, 0) < 60):
        return _price_cache[symbol]
    
    # Lazy init of PricingManager
    if _pricing_manager is None:
        try:
            from iagent_pay.pricing import PricingManager
            _pricing_manager = PricingManager()
        except Exception:
            pass
            
    # Try using PricingManager
    if _pricing_manager:
        try:
            price = _pricing_manager.get_price(symbol)
            if price and price != 1.0:
                _price_cache[symbol] = float(price)
                _price_cache_time[symbol] = time.time()
                return float(price)
        except Exception:
            pass
            
    # Try fetching dynamically from Coinbase spot price API
    try:
        import urllib.request
        import json
        url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2) as response:
            res_data = json.loads(response.read().decode())
            price = float(res_data['data']['amount'])
            _price_cache[symbol] = price
            _price_cache_time[symbol] = time.time()
            return price
    except Exception:
        pass
        
    # Local hardcoded fallback mapping for common assets if network fails
    fallback_map = {
        "ETH": 2500.0,
        "SOL": 145.0,
        "XRP": 0.50,
        "MATIC": 0.65,
        "POL": 0.65,
        "BNB": 580.0,
        "BTC": 65000.0,
        "BONK": 0.00002,
    }
    price = fallback_map.get(symbol, 1.0)
    _price_cache[symbol] = price
    _price_cache_time[symbol] = time.time()
    return price


def load_admin_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"kill_switch_active": False}

def save_admin_config(cfg):
    try:
        tmp_path = CONFIG_PATH + ".tmp"
        with open(tmp_path, 'w') as f:
            json.dump(cfg, f, indent=4)
        os.replace(tmp_path, CONFIG_PATH)
    except Exception as e:
        print(f"Error saving config: {e}")

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def translate_path(self, path):
        resolved_path = super().translate_path(path)
        abs_resolved = os.path.abspath(resolved_path)
        abs_dir = os.path.abspath(DIRECTORY)
        abs_dir_sep = abs_dir + os.sep
        if not (abs_resolved == abs_dir or abs_resolved.startswith(abs_dir_sep)):
            return os.path.join(DIRECTORY, "nonexistent_file_to_trigger_404")
        return resolved_path

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def send_cors(self):
        origin = self.headers.get('Origin')
        if not origin:
            return
        from urllib.parse import urlparse
        try:
            parsed_origin = urlparse(origin)
            origin_host = parsed_origin.hostname
        except Exception:
            return
        
        allowed_hosts = {'localhost', '127.0.0.1', '187.124.76.64', 'iagent-pay.com', 'www.iagent-pay.com'}
        if origin_host in allowed_hosts:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.send_header('Vary', 'Origin')

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def send_json(self, status_code, data):
        response_content = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_cors()
        self.send_header('Content-Type', 'application/json')
        # Hide server fingerprint
        self.send_header('Server', 'iAgent-Pay/2.0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Length', str(len(response_content)))
        self.end_headers()
        self.wfile.write(response_content)

    def is_authorized(self):
        # Cleanup expired sessions (2 hours = 7200 seconds)
        now = time.time()
        expired_sessions = [k for k, v in VALID_SESSIONS.items() if now - v > 7200]
        for k in expired_sessions:
            VALID_SESSIONS.pop(k, None)

        def check_token(token):
            if token not in VALID_SESSIONS:
                return False
            last_activity = VALID_SESSIONS[token]
            if now - last_activity > 7200:
                VALID_SESSIONS.pop(token, None)
                return False
            VALID_SESSIONS[token] = now
            return True

        # PUBLIC READ-ONLY: metrics and transactions are readable without login
        # This allows the dashboard to display stats without requiring MetaMask session

        if self.path.startswith('/api/admin/advanced_reports'):
            from urllib.parse import urlparse, parse_qs
            from datetime import datetime, timezone
            
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            horizon = query_params.get('horizon', ['monthly'])[0]
            start_date_str = query_params.get('start_date', [''])[0]
            end_date_str = query_params.get('end_date', [''])[0]
            
            start_ts = 0.0
            end_ts = 2000000000.0
            try:
                if start_date_str: start_ts = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp()
                if end_date_str: end_ts = datetime.strptime(end_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp() + 86399
            except Exception:
                pass
                
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_history.db")
            rep_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_reputation.db")
            
            try:
                # --- FETCH TRANSACTIONS ---
                conn = DBAdapter(db_path).connect()
                cursor = conn.cursor()
                # Use raw SQL without params to avoid SQLite/Postgres param placeholder conflicts, filtering in Python for safety
                cursor.execute("SELECT timestamp, amount, fee_paid, symbol FROM transactions WHERE status = 'CONFIRMED'")
                tx_rows = cursor.fetchall()
                conn.close()
                
                # --- FETCH PEER RATINGS (AGENTS) ---
                conn_rep = DBAdapter(rep_path).connect()
                cursor_rep = conn_rep.cursor()
                cursor_rep.execute("SELECT last_updated FROM peer_ratings")
                agent_rows = cursor_rep.fetchall()
                conn_rep.close()
                
                # --- PROCESS IN PYTHON ---
                from collections import defaultdict
                grouped_data = defaultdict(lambda: {"volume": 0.0, "fees": 0.0, "agents": 0})
                
                def get_bucket(ts):
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    if horizon == 'daily': return dt.strftime('%Y-%m-%d')
                    if horizon == 'weekly': return dt.strftime('%Y-W%W')
                    if horizon == 'monthly': return dt.strftime('%Y-%m')
                    if horizon == 'yearly': return dt.strftime('%Y')
                    return dt.strftime('%Y-%m')
                
                for row in tx_rows:
                    ts = float(row["timestamp"]) if type(row) is dict else float(row[0])
                    if not (start_ts <= ts <= end_ts): continue
                    
                    amt = float(row["amount"]) if type(row) is dict else float(row[1] or 0)
                    fee = float(row["fee_paid"]) if type(row) is dict else float(row[2] or 0)
                    sym = (row["symbol"] if type(row) is dict else row[3]) or "ETH"
                    
                    # Convert to USD approx
                    usd_val = amt * get_symbol_usd_price(sym)
                    fee_usd = fee / 100.0
                    
                    b = get_bucket(ts)
                    grouped_data[b]["volume"] += usd_val
                    grouped_data[b]["fees"] += fee_usd
                
                for row in agent_rows:
                    ts = float(row["last_updated"]) if type(row) is dict else float(row[0])
                    if not (start_ts <= ts <= end_ts): continue
                    b = get_bucket(ts)
                    grouped_data[b]["agents"] += 1
                
                # Sort and format for Chart.js
                sorted_buckets = sorted(grouped_data.keys())
                
                result = {
                    "labels": sorted_buckets,
                    "volume": [grouped_data[b]["volume"] for b in sorted_buckets],
                    "fees": [grouped_data[b]["fees"] for b in sorted_buckets],
                    "agents": [grouped_data[b]["agents"] for b in sorted_buckets]
                }
                
                self.send_json(200, result)
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        if self.path.startswith('/api/admin/metrics'):
            return True
        if self.path.startswith('/api/transactions'):
            return True

        # Only check /api/admin/ paths beyond this point
        if not self.path.startswith('/api/admin/'):
            return True

        # Allow public /api/admin/auth/*
        if self.path.startswith('/api/admin/auth/'):
            return True

        # All write/admin paths require Authorization header
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return False
        token = auth_header.split(' ')[1]
        return check_token(token)

    def do_GET(self):
        # Rate limit check
        client_ip = self.client_address[0]
        if is_rate_limited(client_ip):
            self.send_json(429, {"error": "Too Many Requests"})
            return

        # Perform auth check
        if not self.is_authorized():
            self.send_json(401, {"error": "Unauthorized. Signature verification required."})
            return

        # Handle Challenge request
        if self.path.startswith('/api/admin/auth/challenge'):
            client_ip = self.client_address[0]
            # Cleanup expired challenges (> 5 mins)
            now = time.time()
            expired = [k for k, v in AUTH_CHALLENGES.items() if now - v[1] > 300]
            for k in expired:
                try:
                    del AUTH_CHALLENGES[k]
                except KeyError:
                    pass

            # Enforce rate-limit of 5 active challenges per IP
            ip_challenges = [k for k, v in AUTH_CHALLENGES.items() if len(v) > 2 and v[2] == client_ip]
            is_testing = os.environ.get("IAGENT_PAY_TESTING") == "1"
            if len(ip_challenges) >= 5 and client_ip not in ("127.0.0.1", "localhost", "::1"):
                self.send_json(429, {"error": "Too many active challenge requests from this IP."})
                return

            # Enforce maximum cache size (500) to prevent memory exhaustion spam
            if len(AUTH_CHALLENGES) >= 500:
                # Evict oldest 50 elements (FIFO/LRU hybrid)
                sorted_challenges = sorted(AUTH_CHALLENGES.items(), key=lambda x: x[1][1])
                for k, _ in sorted_challenges[:50]:
                    try:
                        del AUTH_CHALLENGES[k]
                    except KeyError:
                        pass

            token = secrets.token_hex(16)
            challenge = f"iAgent-Pay Admin Login - Challenge: {secrets.token_hex(16)}"
            AUTH_CHALLENGES[token] = (challenge, time.time(), client_ip)
            
            # Check if setup is needed
            cfg = load_admin_config()
            setup_needed = "admin_wallet_address" not in cfg
            self.send_json(200, {
                "token": token,
                "challenge": challenge,
                "setup_needed": setup_needed,
                "admin_address": cfg.get("admin_wallet_address", "")
            })
            return

        if self.path.startswith('/api/admin/safety_limits'):
            cfg = load_admin_config()
            self.send_json(200, {
                "safety_daily_limit_usd": cfg.get("safety_daily_limit_usd", 1000.0),
                "safety_max_tx_usd": cfg.get("safety_max_tx_usd", 100.0),
                "safety_human_threshold_usd": cfg.get("safety_human_threshold_usd", 500.0),
                "safety_max_tx_per_minute": cfg.get("safety_max_tx_per_minute", 60)
            })
            return

        if self.path.startswith('/api/admin/killswitch'):
            cfg = load_admin_config()
            self.send_json(200, {"active": cfg.get("kill_switch_active", False)})
            return

        if self.path.startswith('/api/admin/reputation'):
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_reputation.db")
            conn = None
            try:
                conn = DBAdapter(db_path).connect()
                pass
                pass
                cursor = conn.cursor()
                # Create peer_ratings if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS peer_ratings (
                        address       TEXT PRIMARY KEY,
                        score         REAL NOT NULL DEFAULT 3.0,
                        reviews_count INTEGER NOT NULL DEFAULT 0,
                        last_updated  REAL NOT NULL,
                        checksum      TEXT
                    )
                """)
                cursor.execute("SELECT address, score, reviews_count, last_updated FROM peer_ratings ORDER BY score DESC")
                rows = cursor.fetchall()
                data = []
                for row in rows:
                    data.append({
                        "address": row["address"],
                        "score": float(row["score"] or 0.0),
                        "reviews": int(row["reviews_count"] or 0),
                        "last_updated": float(row["last_updated"] or 0.0)
                    })
                self.send_json(200, data)
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            finally:
                if conn:
                    conn.close()
            return


        if self.path.startswith('/api/admin/advanced_reports'):
            from urllib.parse import urlparse, parse_qs
            from datetime import datetime, timezone
            
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            horizon = query_params.get('horizon', ['monthly'])[0]
            start_date_str = query_params.get('start_date', [''])[0]
            end_date_str = query_params.get('end_date', [''])[0]
            
            start_ts = 0.0
            end_ts = 2000000000.0
            try:
                if start_date_str: start_ts = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp()
                if end_date_str: end_ts = datetime.strptime(end_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp() + 86399
            except Exception:
                pass
                
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_history.db")
            rep_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_reputation.db")
            
            try:
                # --- FETCH TRANSACTIONS ---
                conn = DBAdapter(db_path).connect()
                cursor = conn.cursor()
                # Use raw SQL without params to avoid SQLite/Postgres param placeholder conflicts, filtering in Python for safety
                cursor.execute("SELECT timestamp, amount, fee_paid, symbol FROM transactions WHERE status = 'CONFIRMED'")
                tx_rows = cursor.fetchall()
                conn.close()
                
                # --- FETCH PEER RATINGS (AGENTS) ---
                conn_rep = DBAdapter(rep_path).connect()
                cursor_rep = conn_rep.cursor()
                cursor_rep.execute("SELECT last_updated FROM peer_ratings")
                agent_rows = cursor_rep.fetchall()
                conn_rep.close()
                
                # --- PROCESS IN PYTHON ---
                from collections import defaultdict
                grouped_data = defaultdict(lambda: {"volume": 0.0, "fees": 0.0, "agents": 0})
                
                def get_bucket(ts):
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    if horizon == 'daily': return dt.strftime('%Y-%m-%d')
                    if horizon == 'weekly': return dt.strftime('%Y-W%W')
                    if horizon == 'monthly': return dt.strftime('%Y-%m')
                    if horizon == 'yearly': return dt.strftime('%Y')
                    return dt.strftime('%Y-%m')
                
                for row in tx_rows:
                    ts = float(row["timestamp"]) if type(row) is dict else float(row[0])
                    if not (start_ts <= ts <= end_ts): continue
                    
                    amt = float(row["amount"]) if type(row) is dict else float(row[1] or 0)
                    fee = float(row["fee_paid"]) if type(row) is dict else float(row[2] or 0)
                    sym = (row["symbol"] if type(row) is dict else row[3]) or "ETH"
                    
                    # Convert to USD approx
                    usd_val = amt * get_symbol_usd_price(sym)
                    fee_usd = fee / 100.0
                    
                    b = get_bucket(ts)
                    grouped_data[b]["volume"] += usd_val
                    grouped_data[b]["fees"] += fee_usd
                
                for row in agent_rows:
                    ts = float(row["last_updated"]) if type(row) is dict else float(row[0])
                    if not (start_ts <= ts <= end_ts): continue
                    b = get_bucket(ts)
                    grouped_data[b]["agents"] += 1
                
                # Sort and format for Chart.js
                sorted_buckets = sorted(grouped_data.keys())
                
                result = {
                    "labels": sorted_buckets,
                    "volume": [grouped_data[b]["volume"] for b in sorted_buckets],
                    "fees": [grouped_data[b]["fees"] for b in sorted_buckets],
                    "agents": [grouped_data[b]["agents"] for b in sorted_buckets]
                }
                
                self.send_json(200, result)
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        if self.path.startswith('/api/admin/metrics'):
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_history.db")
            rep_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_reputation.db")
            conn = None
            conn_rep = None
            try:
                conn = DBAdapter(db_path).connect()
                cursor = conn.cursor()
                
                # Get total count of non-failed transactions
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE status != 'FAILED'")
                tx_count = cursor.fetchone()[0] or 0

                # Aggregate volume by symbol in a SINGLE query — avoids N+1 price lookups
                cursor.execute("""
                    SELECT symbol, SUM(amount) as total_amount, SUM(CASE WHEN fee_paid = 1 THEN amount ELSE 0 END) as paid_amount
                    FROM transactions
                    WHERE status != 'FAILED'
                    GROUP BY symbol
                """)
                symbol_rows = cursor.fetchall()

                total_volume_usd = 0.0
                paid_volume_usd = 0.0
                unpaid_volume_usd = 0.0

                for sr in symbol_rows:
                    sym = (sr[0] or "ETH")
                    total_amt = float(sr[1] or 0.0)
                    paid_amt = float(sr[2] or 0.0)
                    unpaid_amt = total_amt - paid_amt
                    # One price lookup per symbol (not per row!)
                    price = float(get_symbol_usd_price(sym))
                    total_volume_usd += total_amt * price
                    paid_volume_usd += paid_amt * price
                    unpaid_volume_usd += unpaid_amt * price

                # Fetch reputation database count
                conn_rep = DBAdapter(rep_path).connect()
                cursor_rep = conn_rep.cursor()
                cursor_rep.execute("""
                    CREATE TABLE IF NOT EXISTS peer_ratings (
                        address       TEXT PRIMARY KEY,
                        score         REAL NOT NULL DEFAULT 3.0,
                        reviews_count INTEGER NOT NULL DEFAULT 0,
                        last_updated  REAL NOT NULL,
                        checksum      TEXT
                    )
                """)
                cursor_rep.execute("SELECT COUNT(*) FROM peer_ratings WHERE score = 0.0")
                blacklisted_count = cursor_rep.fetchone()[0] or 0

                cursor_rep.execute("SELECT COUNT(*) FROM peer_ratings")
                total_agents = cursor_rep.fetchone()[0] or 0

                trial_agents = total_agents - blacklisted_count

                cursor_rep.execute("""
                    CREATE TABLE IF NOT EXISTS custom_licenses (
                        address       TEXT PRIMARY KEY,
                        grace_days    INTEGER NOT NULL DEFAULT 730,
                        fee_rate      REAL NOT NULL DEFAULT 0.001,
                        last_updated  REAL NOT NULL
                    )
                """)
                cursor_rep.execute("SELECT COUNT(*) FROM custom_licenses")
                custom_license_count = cursor_rep.fetchone()[0] or 0

                metrics = {
                    "total_volume_usd": total_volume_usd,
                    "total_transactions": tx_count,
                    "total_agents": total_agents + 1,
                    "trial_agents": trial_agents + 1,
                    "paying_agents": custom_license_count,
                    "blacklisted_agents": blacklisted_count,
                    "commissions_saved_usd": unpaid_volume_usd * 0.001,
                    "commissions_collected_usd": paid_volume_usd * 0.001
                }
                self.send_json(200, metrics)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json(500, {"error": str(e)})
            finally:
                if conn: conn.close()
                if conn_rep: conn_rep.close()
            return

        if self.path.startswith('/api/transactions'):
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            page = int(query_params.get('page', ['1'])[0])
            limit = int(query_params.get('limit', ['100'])[0])
            status_filter = query_params.get('status', ['ALL'])[0]
            start_date = query_params.get('start_date', [None])[0]
            end_date = query_params.get('end_date', [None])[0]
            
            offset = (page - 1) * limit
            
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_history.db")
            conn = None
            try:
                conn = DBAdapter(db_path).connect()
                pass
                pass
                cursor = conn.cursor()
                
                query_conditions = []
                query_params_sql = []
                
                if status_filter != 'ALL':
                    query_conditions.append("status = ?")
                    query_params_sql.append(status_filter)
                    
                if start_date:
                    # Parse start_date to timestamp
                    try:
                        import datetime
                        dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                        query_conditions.append("timestamp >= ?")
                        query_params_sql.append(dt.timestamp())
                    except:
                        pass
                        
                if end_date:
                    try:
                        import datetime
                        dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                        # Add 1 day to include the end date fully
                        query_conditions.append("timestamp < ?")
                        query_params_sql.append(dt.timestamp() + 86400)
                    except:
                        pass
                
                where_clause = ""
                if query_conditions:
                    where_clause = "WHERE " + " AND ".join(query_conditions)
                    
                # Get total count for pagination
                count_query = f"SELECT COUNT(*) FROM transactions {where_clause}"
                cursor.execute(count_query, query_params_sql)
                total_count = cursor.fetchone()[0]
                
                # Fetch data
                data_query = f"SELECT timestamp, tx_hash, recipient, amount, status, symbol, fee_paid FROM transactions {where_clause} ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                cursor.execute(data_query, query_params_sql + [limit, offset])
                rows = cursor.fetchall()
                
                data = []
                for row in rows:
                    amount_val = float(row["amount"] or 0.0)
                    symbol_val = row["symbol"] or "ETH"
                    price = float(get_symbol_usd_price(symbol_val))
                    amount_usd = amount_val * price
                    data.append({
                        "timestamp": float(row["timestamp"] or 0.0),
                        "tx_hash": row["tx_hash"],
                        "recipient": row["recipient"],
                        "amount": amount_val,
                        "status": row["status"],
                        "symbol": symbol_val,
                        "fee_paid": float(row["fee_paid"] or 0.0),
                        "amount_usd": amount_usd
                    })
                
                import math
                self.send_json(200, {
                    "transactions": data,
                    "pagination": {
                        "total_count": total_count,
                        "total_pages": math.ceil(total_count / limit) if limit > 0 else 0,
                        "current_page": page,
                        "limit": limit
                    }
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json(500, {"error": str(e)})
            finally:
                if conn:
                    conn.close()
            return
            
        if self.path.startswith('/api/admin/licenses'):
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_reputation.db")
            conn = None
            try:
                conn = DBAdapter(db_path).connect()
                pass
                pass
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS custom_licenses (
                        address       TEXT PRIMARY KEY,
                        grace_days    INTEGER NOT NULL DEFAULT 730,
                        fee_rate      REAL NOT NULL DEFAULT 0.001,
                        last_updated  REAL NOT NULL
                    )
                """)
                cursor.execute("SELECT address, grace_days, fee_rate, last_updated FROM custom_licenses ORDER BY last_updated DESC")
                rows = cursor.fetchall()
                data = []
                for row in rows:
                    data.append({
                        "address": row["address"],
                        "grace_days": row["grace_days"],
                        "fee_rate": row["fee_rate"],
                        "last_updated": row["last_updated"]
                    })
                self.send_json(200, data)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json(500, {"error": str(e)})
            finally:
                if conn: conn.close()
            return

        if self.path.startswith('/api/admin/treasury'):
            cfg = load_admin_config()
            treasury = {
                "EVM": cfg.get("treasury_address_evm", "0x9F4D251F7A038fd379246834eac74B8419ffDA20"),
                "SOLANA": cfg.get("treasury_address_solana", "8F26834eac74B8419FfdA202CF8051F7A03fd379"),
                "XRPL": cfg.get("treasury_address_xrpl", "r39246834eac74B8419FfdA202CF8051F7A03")
            }
            self.send_json(200, treasury)
            return

        if self.path.startswith('/api/admin/treasury_stats'):
            cfg = load_admin_config()
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_history.db")
            total_fees_usd = 0.0
            try:
                conn = DBAdapter(db_path).connect()
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(fee_paid) FROM transactions WHERE fee_paid > 0")
                row = cursor.fetchone()
                if row and row[0]:
                    total_fees_usd = float(row[0]) / 100.0  
                conn.close()
            except Exception:
                pass
                
            self.send_json(200, {
                "balance": total_fees_usd, 
                "auto_yield": cfg.get("treasury_auto_yield", False)
            })
            return

        # ─── ESCROW ANTI-ALUCINACIÓN ──────────────────────────────────────────
        if self.path.startswith('/api/admin/escrows'):
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            status_filter = query_params.get('status', ['ALL'])[0]

            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_marketplace.db")
            conn = None
            try:
                conn = DBAdapter(db_path).connect()
                cursor = conn.cursor()
                # Ensure table exists (first boot)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS escrow_contracts (
                        id TEXT PRIMARY KEY, recipient TEXT, amount_usd REAL, status TEXT,
                        task_description TEXT, created_at REAL, resolved_at REAL
                    )
                """)
                if status_filter != 'ALL':
                    cursor.execute(
                        "SELECT id, recipient, amount_usd, status, task_description, created_at, resolved_at FROM escrow_contracts WHERE status = ? ORDER BY created_at DESC",
                        (status_filter.upper(),)
                    )
                else:
                    cursor.execute(
                        "SELECT id, recipient, amount_usd, status, task_description, created_at, resolved_at FROM escrow_contracts ORDER BY created_at DESC"
                    )
                rows = cursor.fetchall()
                data = []
                locked = released = refunded = 0
                for r in rows:
                    s = (r["status"] or "UNKNOWN").upper()
                    if s == "LOCKED":    locked += 1
                    elif s == "RELEASED": released += 1
                    elif s == "REFUNDED": refunded += 1
                    data.append({
                        "id":          r["id"],
                        "recipient":   r["recipient"],
                        "amount_usd":  float(r["amount_usd"] or 0.0),
                        "status":      s,
                        "task":        r["task_description"],
                        "created_at":  float(r["created_at"] or 0.0),
                        "resolved_at": float(r["resolved_at"] or 0.0) if r["resolved_at"] is not None else None,
                    })
                self.send_json(200, {
                    "escrows": data,
                    "summary": {"total": len(data), "locked": locked, "released": released, "refunded": refunded}
                })
            except Exception as e:
                import traceback; traceback.print_exc()
                self.send_json(500, {"error": str(e)})
            finally:
                if conn: conn.close()
            return

        # ─── PROOF-OF-REASONING (FORENSIC RECEIPTS) ───────────────────────────
        if self.path.startswith('/api/admin/forensics'):
            from urllib.parse import urlparse, parse_qs
            import glob
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            tx_filter = query_params.get('tx', [None])[0]

            receipts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "receipts")
            try:
                os.makedirs(receipts_dir, exist_ok=True)
                pattern = os.path.join(receipts_dir, "*.json")
                files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
                receipts = []
                for fpath in files[:200]:  # max 200 receipts in view
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            r = json.load(f)
                        if tx_filter and tx_filter.lower() not in r.get("tx_hash", "").lower():
                            continue
                        receipts.append({
                            "tx_hash":        r.get("tx_hash", ""),
                            "recipient":      r.get("recipient", ""),
                            "amount":         r.get("amount", 0),
                            "symbol":         r.get("symbol", ""),
                            "timestamp":      r.get("timestamp", 0),
                            "reasoning_hash": r.get("reasoning_hash", ""),
                            "reasoning_text": r.get("reasoning_text", ""),
                        })
                    except Exception:
                        continue
                self.send_json(200, {"receipts": receipts, "total": len(receipts)})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        # ─── ERROR LOGGING (HELP DESK) ─────────────────────────────────────────
        if self.path.startswith('/api/admin/errors'):
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_errors.db")
            conn = None
            try:
                conn = DBAdapter(db_path).connect()
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_errors (
                        id TEXT PRIMARY KEY,
                        timestamp REAL NOT NULL,
                        user_address TEXT,
                        error_message TEXT NOT NULL,
                        stack_trace TEXT,
                        status TEXT DEFAULT 'OPEN'
                    )
                """)
                cursor.execute("SELECT * FROM system_errors ORDER BY timestamp DESC")
                rows = cursor.fetchall()
                errors = []
                for r in rows:
                    errors.append({
                        "id": r["id"],
                        "timestamp": r["timestamp"],
                        "user_address": r["user_address"],
                        "error_message": r["error_message"],
                        "stack_trace": r["stack_trace"],
                        "status": r["status"]
                    })
                self.send_json(200, {"errors": errors})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            finally:
                if conn: conn.close()
            return

        # Map /admin to the admin dashboard HTML file using a 302 redirect

        if self.path == '/admin' or self.path == '/admin/':
            self.send_response(302)
            self.send_header('Location', '/dashboard/admin.html')
            self.end_headers()
            return

        # Fallback to serving static files
        allowed_exts = ('.html', '.css', '.js', '.png', '.svg', '.ico', '.pdf', '.webp')
        path_without_query = self.path.split('?')[0]
        if path_without_query != '/' and not path_without_query.endswith(allowed_exts):
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Forbidden: Cannot serve backend files."}).encode('utf-8'))
            return
            
        super().do_GET()

    def do_POST(self):
        # Rate limit check
        client_ip = self.client_address[0]
        if is_rate_limited(client_ip):
            self.send_json(429, {"error": "Too Many Requests"})
            return

        # 1. Enforce strict Content-Length checking to prevent memory exhaustion / OOM
        content_length_header = self.headers.get('Content-Length')
        if not content_length_header:
            self.send_json(411, {"error": "Length Required."})
            return
            
        try:
            content_length = int(content_length_header)
        except ValueError:
            self.send_json(400, {"error": "Invalid Content-Length header."})
            return

        # Determine limit based on endpoint: backup import allows up to 20MB, other API calls limited to 10KB
        max_size = 20 * 1024 * 1024 if self.path.startswith('/api/admin/backup/import') else 10 * 1024
        if content_length > max_size:
            self.send_json(413, {"error": "Payload Too Large."})
            return

        # ─── PUBLIC ENDPOINTS (NO AUTH REQUIRED) ─────────────────────────────
        if self.path.startswith('/api/errors/report'):
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_errors.db")
                conn = DBAdapter(db_path).connect()
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_errors (
                        id TEXT PRIMARY KEY,
                        timestamp REAL NOT NULL,
                        user_address TEXT,
                        error_message TEXT NOT NULL,
                        stack_trace TEXT,
                        status TEXT DEFAULT 'OPEN'
                    )
                """)
                error_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO system_errors (id, timestamp, user_address, error_message, stack_trace, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (error_id, time.time(), data.get("user_address", "Anonymous"), data.get("error_message", "Unknown Error"), data.get("stack_trace", ""), "OPEN")
                )
                conn.commit()
                conn.close()
                self.send_json(200, {"status": "success"})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        # Perform auth check
        if not self.is_authorized():
            self.send_json(401, {"error": "Unauthorized. Signature verification required."})
            return

        # Handle Admin Registration (Setup)
        if self.path.startswith('/api/admin/auth/register'):
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                address = data.get("address", "").strip()
                if not address:
                    raise ValueError("Wallet address is required")
                
                cfg = load_admin_config()
                if "admin_wallet_address" in cfg:
                    self.send_json(400, {"error": "Master Admin wallet address already registered."})
                    return
                
                # Register address (canonical checksum address format)
                checksum_address = Web3.to_checksum_address(address)
                cfg["admin_wallet_address"] = checksum_address
                save_admin_config(cfg)
                self.send_json(200, {"status": "success", "admin_wallet_address": checksum_address})
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        # Handle Web3 Login Verification
        if self.path.startswith('/api/admin/auth/verify'):
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                token = data.get("token")
                address = data.get("address")
                signature = data.get("signature")
                
                if not token or not address or not signature:
                    raise ValueError("token, address, and signature are required")
                
                if token not in AUTH_CHALLENGES:
                    self.send_json(400, {"error": "Invalid or expired challenge token."})
                    return
                
                # Mitigation: Prevent ECDSA Signature Malleability
                # A standard Ethereum signature is 65 bytes: r (32 bytes) + s (32 bytes) + v (1 byte)
                # s must be in the lower half range: s <= HALF_N
                try:
                    sig_bytes = bytes.fromhex(signature[2:] if signature.startswith('0x') else signature)
                    if len(sig_bytes) == 65:
                        s_val = int.from_bytes(sig_bytes[32:64], byteorder='big')
                        if s_val > SECP256K1_HALF_N:
                            self.send_json(400, {"error": "Malleable signature detected. Must be low-s."})
                            return
                except Exception:
                    self.send_json(400, {"error": "Invalid signature format."})
                    return
                
                challenge_text, timestamp, _ = AUTH_CHALLENGES[token]
                if time.time() - timestamp > 300: # 5 min expiration
                    self.send_json(400, {"error": "Challenge token has expired."})
                    return
                
                # Recover signer address
                encoded_msg = encode_defunct(text=challenge_text)
                recovered_addr = Account.recover_message(encoded_msg, signature=signature)
                
                cfg = load_admin_config()
                admin_address = cfg.get("admin_wallet_address")
                
                if not admin_address:
                    self.send_json(400, {"error": "No Master Admin registered yet."})
                    return
                
                if recovered_addr.lower() != address.lower() or recovered_addr.lower() != admin_address.lower():
                    self.send_json(401, {"error": "Signature verification failed. Unauthorized wallet."})
                    return
                
                # Create session token
                session_id = secrets.token_hex(32)
                VALID_SESSIONS[session_id] = time.time()
                
                # Remove challenge
                try:
                    del AUTH_CHALLENGES[token]
                except KeyError:
                    pass
                
                self.send_json(200, {"status": "success", "token": session_id, "address": admin_address})
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        if self.path.startswith('/api/admin/errors/resolve'):
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                error_id = data.get("id")
                if not error_id:
                    self.send_json(400, {"error": "Error ID required"})
                    return
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_errors.db")
                conn = DBAdapter(db_path).connect()
                cursor = conn.cursor()
                cursor.execute("UPDATE system_errors SET status = 'SOLVED' WHERE id = ?", (error_id,))
                conn.commit()
                conn.close()
                self.send_json(200, {"status": "success"})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        # Handle Database Reset
        if self.path.startswith('/api/admin/reset_db'):
            try:
                # Require MetaMask Signature for this destructive action
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self.send_json(400, {"error": "Payload missing."})
                    return
                
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                signature = data.get("signature")
                address = data.get("address")
                
                if not signature or not address:
                    self.send_json(400, {"error": "MetaMask signature required for destructive action."})
                    return
                
                # Verify signature
                encoded_msg = encode_defunct(text="Confirmar reseteo total de la base de datos de iAgentPay.")
                recovered_addr = Account.recover_message(encoded_msg, signature=signature)
                
                cfg = load_admin_config()
                admin_address = cfg.get("admin_wallet_address")
                
                if recovered_addr.lower() != address.lower() or recovered_addr.lower() != admin_address.lower():
                    self.send_json(401, {"error": "Invalid signature. Master Admin only."})
                    return

                # Delete all data
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_history.db")
                adapter = DBAdapter(db_path)
                conn = adapter.connect()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions")
                conn.commit()
                conn.close()
                
                rep_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_reputation.db")
                adapter_rep = DBAdapter(rep_path)
                conn_rep = adapter_rep.connect()
                cursor_rep = conn_rep.cursor()
                
                # Erase peer ratings (reputation)
                try:
                    cursor_rep.execute("DELETE FROM peer_ratings")
                except Exception:
                    pass
                    
                # Erase licenses
                try:
                    cursor_rep.execute("DELETE FROM custom_licenses")
                except Exception:
                    pass
                    
                conn_rep.commit()
                conn_rep.close()
                
                # Erase escrows
                market_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_marketplace.db")
                adapter_mkt = DBAdapter(market_path)
                conn_mkt = adapter_mkt.connect()
                cursor_mkt = conn_mkt.cursor()
                try:
                    cursor_mkt.execute("DELETE FROM escrow_contracts")
                except Exception:
                    pass
                conn_mkt.commit()
                conn_mkt.close()
                
                # Erase forensic receipts (JSON files)
                import glob
                receipts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "receipts")
                if os.path.exists(receipts_dir):
                    files = glob.glob(os.path.join(receipts_dir, "*.json"))
                    for f in files:
                        try:
                            os.remove(f)
                        except Exception:
                            pass
                
                # Erase errors (Help Desk)
                err_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_errors.db")
                adapter_err = DBAdapter(err_path)
                conn_err = adapter_err.connect()
                cursor_err = conn_err.cursor()
                try:
                    cursor_err.execute("DELETE FROM system_errors")
                except Exception:
                    pass
                conn_err.commit()
                conn_err.close()

                
                self.send_json(200, {"status": "success", "message": "Database reset to zero."})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        # Handle No-Code Safety Limits Update
        if self.path.startswith('/api/admin/safety_limits'):
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                signature = data.get("signature")
                address = data.get("address")
                
                if not signature or not address:
                    self.send_json(400, {"error": "MetaMask signature required."})
                    return
                
                # Verify signature
                encoded_msg = encode_defunct(text="Autorizo modificar los limites presupuestales de las IAs.")
                recovered_addr = Account.recover_message(encoded_msg, signature=signature)
                
                cfg = load_admin_config()
                admin_address = cfg.get("admin_wallet_address")
                
                if recovered_addr.lower() != address.lower() or recovered_addr.lower() != admin_address.lower():
                    self.send_json(401, {"error": "Invalid signature. Master Admin only."})
                    return
                    
                # Save new limits
                cfg["safety_daily_limit_usd"] = float(data.get("safety_daily_limit_usd", 1000.0))
                cfg["safety_human_threshold_usd"] = float(data.get("safety_human_threshold_usd", 20.0))
                cfg["safety_max_tx_usd"] = float(data.get("safety_max_tx_usd", 500.0))
                cfg["safety_max_tx_per_minute"] = int(data.get("safety_max_tx_per_minute", 10))
                save_admin_config(cfg)
                
                self.send_json(200, {"status": "success", "message": "Safety limits updated successfully."})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        # Handle Encrypted Backup Export (Streaming V3)
        if self.path.startswith('/api/admin/backup/export'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                password = data.get("password")
                if not password or len(password) < 4:
                    raise ValueError("Password must be at least 4 characters long")
                
                # Derive AES key
                salt = os.urandom(16)
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = kdf.derive(password.encode())
                
                # Setup GCM Cipher
                iv = os.urandom(12)
                from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                from cryptography.hazmat.backends import default_backend
                encryptor = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend()).encryptor()
                
                # Create a zip of the files
                import zipfile
                import tempfile
                
                temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix=".zip")
                os.close(temp_zip_fd)
                
                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    if os.path.exists(CONFIG_PATH):
                        zf.write(CONFIG_PATH, os.path.basename(CONFIG_PATH))
                    rep_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_reputation.db")
                    if os.path.exists(rep_path):
                        zf.write(rep_path, os.path.basename(rep_path))
                    hist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_history.db")
                    if os.path.exists(hist_path):
                        zf.write(hist_path, os.path.basename(hist_path))
                
                # Stream it out
                self.send_response(200)
                self.send_cors()
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="iagentpay_backup_{int(time.time())}.enc"')
                self.end_headers()
                
                # Write metadata (salt + iv)
                self.wfile.write(salt + iv)
                
                # Stream the file in 1MB chunks through AES-GCM
                with open(temp_zip_path, 'rb') as f:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        encrypted_chunk = encryptor.update(chunk)
                        if encrypted_chunk:
                            self.wfile.write(encrypted_chunk)
                
                # Finalize and write the authentication tag
                encryptor.finalize()
                self.wfile.write(encryptor.tag)
                
                # Cleanup
                os.remove(temp_zip_path)
            except Exception as e:
                # If headers already sent, we can't send json error, but the connection will drop.
                print(f"Export Error: {e}")
            return

        # Handle Encrypted Backup Import (Streaming V3)
        if self.path.startswith('/api/admin/backup/import'):
            # This is a multipart upload, but for simplicity we will accept binary post directly
            password = self.headers.get('X-Backup-Password')
            if not password:
                self.send_json(400, {"error": "Password header missing"})
                return
                
            content_length = int(self.headers['Content-Length'])
            if content_length < 28:
                self.send_json(400, {"error": "File too small"})
                return
                
            try:
                salt = self.rfile.read(16)
                iv = self.rfile.read(12)
                
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = kdf.derive(password.encode())
                
                # Read all the rest into memory for decryption (or write to disk)
                ciphertext_with_tag = self.rfile.read(content_length - 28)
                ciphertext = ciphertext_with_tag[:-16]
                tag = ciphertext_with_tag[-16:]
                
                from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                from cryptography.hazmat.backends import default_backend
                decryptor = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()).decryptor()
                
                plaintext = decryptor.update(ciphertext) + decryptor.finalize()
                
                import tempfile
                import zipfile
                temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix=".zip")
                with os.fdopen(temp_zip_fd, 'wb') as f:
                    f.write(plaintext)
                    
                import shutil
                # Backup existing first
                if os.path.exists(CONFIG_PATH):
                    shutil.copy(CONFIG_PATH, CONFIG_PATH + ".bak")
                    
                with zipfile.ZipFile(temp_zip_path, 'r') as zf:
                    for filename in zf.namelist():
                        if filename in ["admin_config.json", "agent_reputation.db", "agent_history.db"]:
                            target = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
                            with open(target, 'wb') as f:
                                f.write(zf.read(filename))
                                
                os.remove(temp_zip_path)
                self.send_json(200, {"status": "success", "message": "Respaldo restaurado con éxito."})
                
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        if self.path.startswith('/api/admin/killswitch'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                active = data.get("active", False)
                cfg = load_admin_config()
                cfg["kill_switch_active"] = active
                save_admin_config(cfg)
                self.send_json(200, {"status": "success", "active": active})
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        if self.path.startswith('/api/admin/yield_toggle'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                enable = data.get("enable", False)
                cfg = load_admin_config()
                cfg["treasury_auto_yield"] = enable
                save_admin_config(cfg)
                self.send_json(200, {"status": "success", "success": True, "active": enable})
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        if self.path.startswith('/api/admin/reputation'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_reputation.db")
            conn = None
            try:
                data = json.loads(post_data.decode('utf-8'))
                address = data.get("address")
                score = float(data.get("score", 3.0))
                
                if not address:
                    raise ValueError("Address is required")

                conn = DBAdapter(db_path).connect()
                pass
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS peer_ratings (
                        address       TEXT PRIMARY KEY,
                        score         REAL NOT NULL DEFAULT 3.0,
                        reviews_count INTEGER NOT NULL DEFAULT 0,
                        last_updated  REAL NOT NULL,
                        checksum      TEXT
                    )
                """)
                
                now = time.time()
                # Check if exists to increment reviews_count
                cursor.execute("SELECT reviews_count FROM peer_ratings WHERE address = ?", (address,))
                row = cursor.fetchone()
                if row:
                    reviews = row[0] + 1
                else:
                    reviews = 1
                
                cursor.execute("""
                    INSERT INTO peer_ratings (address, score, reviews_count, last_updated, checksum)
                    VALUES (?, ?, ?, ?, '')
                    ON CONFLICT(address) DO UPDATE SET
                        score = excluded.score,
                        reviews_count = excluded.reviews_count,
                        last_updated = excluded.last_updated
                """, (address, score, reviews, now))
                conn.commit()
                self.send_json(200, {"status": "success", "address": address, "score": score})
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            finally:
                if conn: conn.close()
            return

        if self.path.startswith('/api/admin/licenses'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_reputation.db")
            conn = None
            try:
                data = json.loads(post_data.decode('utf-8'))
                address = data.get("address")
                grace_days = int(data.get("grace_days", 730))
                fee_rate = float(data.get("fee_rate", 0.001))
                
                if not address:
                    raise ValueError("Address is required")

                conn = DBAdapter(db_path).connect()
                pass
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS custom_licenses (
                        address       TEXT PRIMARY KEY,
                        grace_days    INTEGER NOT NULL DEFAULT 730,
                        fee_rate      REAL NOT NULL DEFAULT 0.001,
                        last_updated  REAL NOT NULL
                    )
                """)
                
                now = time.time()
                cursor.execute("""
                    INSERT INTO custom_licenses (address, grace_days, fee_rate, last_updated)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(address) DO UPDATE SET
                        grace_days = excluded.grace_days,
                        fee_rate = excluded.fee_rate,
                        last_updated = excluded.last_updated
                """, (address, grace_days, fee_rate, now))
                conn.commit()
                self.send_json(200, {"status": "success", "address": address, "grace_days": grace_days, "fee_rate": fee_rate})
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            finally:
                if conn: conn.close()
            return

        if self.path.startswith('/api/admin/treasury'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Check for treasury password
                password = data.get("password", "")
                if password != "Santsant2":
                    raise Exception("Contraseña de seguridad incorrecta. Operación denegada.")
                
                evm_addr = data.get("evm", "").strip()
                sol_addr = data.get("solana", "").strip()
                xrp_addr = data.get("xrpl", "").strip()
                
                cfg = load_admin_config()
                if evm_addr: cfg["treasury_address_evm"] = evm_addr
                if sol_addr: cfg["treasury_address_solana"] = sol_addr
                if xrp_addr: cfg["treasury_address_xrpl"] = xrp_addr
                
                save_admin_config(cfg)
                self.send_json(200, {"status": "success", "treasury": {
                    "EVM": cfg.get("treasury_address_evm"),
                    "SOLANA": cfg.get("treasury_address_solana"),
                    "XRPL": cfg.get("treasury_address_xrpl")
                }})
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        if self.path.startswith('/api/client/generate_session'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Verify that they accepted the disclaimer
                if not data.get("accepted_disclaimer"):
                    raise Exception("Must accept the financial responsibility disclaimer to generate a session key.")
                
                master_wallet = data.get("master_wallet")
                daily_limit = float(data.get("daily_limit", 100.0))
                tx_limit = float(data.get("tx_limit", 20.0))
                whitelist = data.get("whitelist", [])
                
                # In a real environment, the client would sign this request with their Master Wallet
                # For the No-Code demo, we simulate their account being loaded
                if master_wallet:
                    # Create a dummy local account just to generate the signature as if they signed it
                    owner_account = Account.create()
                else:
                    owner_account = Account.create()
                
                session_key = SessionKeyManager.create_session(
                    owner_account=owner_account,
                    allowed_tokens=["USDC", "USDT", "ETH"],
                    daily_limit_usd=daily_limit,
                    max_tx_usd=tx_limit,
                    validity_seconds=86400 * 365, # Valid for 1 year
                    allowed_destinations=whitelist if whitelist else None
                )
                
                # Override the owner address to match what the user connected with (for visual fidelity)
                if master_wallet:
                    session_key.owner_address = master_wallet
                    
                session_dict = session_key.to_dict()
                session_dict["auto_yield"] = data.get("auto_yield", False)
                    
                self.send_json(200, {
                    "status": "success", 
                    "session_key": session_dict
                })
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer): pass

if __name__ == "__main__":
    # If port is occupied, try next ports
    success = False
    port = PORT
    while not success and port < PORT + 10:
        try:
            httpd = ThreadedServer(("", port), MyHTTPRequestHandler)
            print(f"Serving dashboard at http://localhost:{port}")
            success = True
        except OSError:
            print(f"Port {port} is occupied, trying next...")
            port += 1
            
    if success:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()
            print("\nServer stopped.")
    else:
        print("Error: Could not bind server to any port.")
