from web3 import Web3
import requests

class SocialResolver:
    """
    Resolves human-readable names to blockchain addresses.
    Supports:
    - ENS (.eth) -> Ethereum Address (0x...)
    - SNS (.sol) -> Solana Address (Base58)
    """
    
    def __init__(self):
        # We need a Mainnet connection for ENS, even if the agent is on Base/Polygon
        # Using a public reliable RPC
        try:
            self.ens_w3 = Web3(Web3.HTTPProvider("https://eth.llamarpc.com"))
        except:
            self.ens_w3 = None

    def resolve(self, identifier: str) -> str:
        """
        Auto-detects .eth or .sol and resolves it.
        Returns None if resolution fails.
        """
        original_id = identifier.strip()
        lower_id = original_id.lower()
        
        if lower_id.endswith(".eth"):
            return self._resolve_ens(lower_id)
        
        if lower_id.endswith(".sol"):
            return self._resolve_sns(lower_id)
            
        return original_id # Return RAW (Case Sensitive) if not a handle

    def _resolve_ens(self, name: str) -> str:
        if not self.ens_w3 or not self.ens_w3.is_connected():
            print("⚠️ ENS Resolution unavailable (No Mainnet Connection).")
            return None
        
        try:
            address = self.ens_w3.ens.address(name)
            if address:
                print(f"🔍 Resolved ENS: {name} -> {address}")
                return address
        except Exception as e:
            print(f"❌ ENS Lookup Error: {e}")
        return None

    def _resolve_sns(self, name: str) -> str:
        """
        Resolves Solana Name Service (Bonfida).
        Uses public API to avoid heavy dependency for now.
        """
        try:
            # Bonfida Public API
            url = f"https://sns-sdk-proxy.bonfida.workers.dev/resolve/{name}"
            response = requests.get(url, timeout=3)
            data = response.json()
            
            if data.get("result"):
                address = data["result"]
                print(f"🔍 Resolved SNS: {name} -> {address}")
                return address
        except Exception as e:
            print(f"❌ SNS Lookup Error: {e}")
            
        return None
