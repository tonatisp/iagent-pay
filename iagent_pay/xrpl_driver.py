import time
from typing import Optional

class XRPLDriver:
    """
    Driver for XRP Ledger (XRPL) integration.
    Supports balance checks and native XRP transfers.
    """
    def __init__(self, endpoint: str = "https://s.altnet.rippletest.net:51234"):
        self.endpoint = endpoint
        self._client = None
        self.wallet = None

    @property
    def client(self):
        if self._client is None:
            from xrpl.clients import JsonRpcClient
            self._client = JsonRpcClient(self.endpoint)
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    def load_wallet(self, seed: str):
        """Loads an XRPL wallet from a secret seed."""
        from xrpl.wallet import Wallet
        self.wallet = Wallet.from_seed(seed)
        return self.wallet.address

    def get_address(self) -> str:
        if self.wallet:
            return self.wallet.address
        return "Not Loaded"

    def get_balance(self) -> float:
        """Fetches the account balance in XRP."""
        if not self.wallet:
            raise ValueError("XRPL Wallet not loaded.")
        
        from xrpl.models.requests import AccountInfo
        from xrpl.utils import drops_to_xrp
        try:
            acct_info = AccountInfo(account=self.wallet.address, ledger_index="validated")
            response = self.client.request(acct_info)
            if response.is_successful():
                drops = response.result["account_data"]["Balance"]
                return float(drops_to_xrp(drops))
            else:
                print(f"⚠️ XRPL Account not found or not initialized yet: {response.result.get('error_message', 'Unknown Error')}")
                return 0.0
        except Exception as e:
            print(f"⚠️ XRPL Balance Check Failed: {e}")
            return 0.0

    def transfer(self, recipient: str, amount_xrp: float, destination_tag: Optional[int] = None) -> str:
        """
        Sends native XRP to a recipient.
        :param destination_tag: Optional tag for exchanges/institutional wallets.
        """
        if not self.wallet:
            raise ValueError("XRPL Wallet not loaded.")

        from decimal import Decimal
        from xrpl.models.transactions import Payment
        from xrpl.transaction import submit_and_wait
        from xrpl.utils import xrp_to_drops

        # Prepare Payment Transaction
        payment = Payment(
            account=self.wallet.address,
            amount=str(xrp_to_drops(Decimal(str(amount_xrp)))),
            destination=recipient,
            destination_tag=destination_tag
        )

        # Submit and wait for validation
        try:
            response = submit_and_wait(payment, self.client, self.wallet)
            if response.is_successful():
                tx_hash = response.result["hash"]
                return tx_hash
            raise Exception(f"XRPL Transaction failed: {response.result.get('meta', {}).get('TransactionResult')}")
        except Exception as e:
            print(f"❌ XRPL Transfer Failed: {e}")
            raise e

