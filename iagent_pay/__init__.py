import sys

# Prevent UnicodeEncodeError on Windows terminals with non-UTF-8 codepages by replacing unencodable characters
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(errors='replace')
    except Exception:
        pass

from .agent_pay import AgentPay
from .wallet_manager import WalletManager
from .config import ChainConfig
from .pricing import PricingManager
from .yield_protocols import YieldManager
from .reputation_manager import ReputationManager
from .marketplace_bridge import MarketplaceBridge

# iAgentPay v6.0 - Full Adoption Release
# The Ultimate Banking Infrastructure for Autonomous AI Agents

__version__ = "6.0.0"
__all__ = ["AgentPay", "WalletManager", "ChainConfig", "PricingManager", "YieldManager", "ReputationManager", "MarketplaceBridge"]

import threading
import urllib.request
import json

def _check_for_updates():
    try:
        req = urllib.request.Request(
            'https://pypi.org/pypi/iagent-pay/json',
            headers={'User-Agent': f'iAgentPay/{__version__}'}
        )
        with urllib.request.urlopen(req, timeout=1.5) as response:
            data = json.loads(response.read().decode('utf-8'))
            latest_version = data['info']['version']
            
            # Basic string comparison
            if latest_version != __version__ and latest_version > __version__:
                print(f"\n\033[93m⚠️ [AVISO iAgentPay]: Estás usando la versión {__version__}. ¡La nueva versión {latest_version} ya está disponible!\n"
                      f"Ejecuta 'pip install --upgrade iagent-pay' para actualizar.\033[0m\n")
    except Exception:
        pass # Silent failure on network errors to never crash the user's code

# Run check in background thread to avoid blocking the main application
threading.Thread(target=_check_for_updates, daemon=True).start()
