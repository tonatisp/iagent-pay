from web3 import Web3
import time

# Aave v3 Pool ABI (Supply/Withdraw)
AAVE_V3_POOL_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "asset", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "address", "name": "onBehalfOf", "type": "address"},
            {"internalType": "uint16", "name": "referralCode", "type": "uint16"}
        ],
        "name": "supply",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "asset", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "address", "name": "to", "type": "address"}
        ],
        "name": "withdraw",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Aave v3 Pool Address on BASE
BASE_AAVE_V3_POOL = Web3.to_checksum_address("0xA238Dd80C259a72e81d7e4674A963c9b9018d872")

class YieldManager:
    def __init__(self, agent):
        self.agent = agent
        self.protocol = None
        self.active = False
        # Mapping to aTokens for balance checking
        self.atoken_map = {
            "BASE": {
                "USDC": Web3.to_checksum_address("0x4e65fE4DbA5950d2428e01216bcA7ba28da6A4ad")
            }
        }

    def _check_protocol_health(self) -> bool:
        """
        Verifies if the DeFi protocol is responding and safe.
        In production, this would check Aave's 'Emergency Admin' status.
        """
        if self.agent.is_solana: return True
        
        try:
            # Check if pool contract exists and responds (Base/Aave)
            w3 = self.agent.w3
            if not w3 or not w3.is_connected():
                 return False
            code = w3.eth.get_code(BASE_AAVE_V3_POOL)
            if len(code) < 100:
                print("🚨 [DeFi Safety] Aave Pool contract seems empty or destroyed!")
                return False
            return True
        except Exception as e:
            print(f"🚨 [DeFi Safety] Protocol health check failed: {e}")
            return False

    def enable(self, protocol="aave"):
        self.protocol = protocol.lower()
        self.active = True
        print(f"🏦 [YieldManager] Enabled auto-yield via {self.protocol.upper()}")

    def deposit(self, token_symbol: str, amount: float):
        """Deposits tokens into the yield protocol."""
        if not self.active:
            return
            
        if not self._check_protocol_health():
             print("🚫 [YieldManager] Deposit aborted due to protocol safety concerns.")
             return

        if self.agent.is_solana:
            print(f"🏦 [YieldManager] Solana yield (Jito/Marinade) coming in v3.1.")
            return

        if self.protocol == "aave" and self.agent.chain_name == "BASE":
            return self._deposit_aave_base(token_symbol, amount)

    def _deposit_aave_base(self, token_symbol, amount):
        token_address = self.agent._resolve_token_address(token_symbol)
        if not token_address:
            print(f"⚠️ [YieldManager] Unknown token {token_symbol}")
            return

        w3 = self.agent.w3
        from .tokens import ERC20_ABI
        
        try:
            # 1. Resolve Decimals
            token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
            decimals = token_contract.functions.decimals().call()
            amount_units = int(amount * (10 ** decimals))

            # 2. Check Allowance & Approve
            allowance = token_contract.functions.allowance(self.agent.my_address, BASE_AAVE_V3_POOL).call()
            if allowance < amount_units:
                print(f"🏦 [YieldManager] Approving Aave Pool for {amount} {token_symbol}...")
                approve_tx = token_contract.functions.approve(BASE_AAVE_V3_POOL, amount_units).build_transaction({
                    'from': self.agent.my_address,
                    'nonce': self.agent._get_nonce(),
                })
                self.agent._send_evm_transaction(approve_tx, wait=True, log_recipient=BASE_AAVE_V3_POOL, log_amount=0, log_symbol=f"Approve-{token_symbol}")
        except Exception as e:
            print(f"⚠️ [YieldManager] Deposit checks failed (Contract unreachable): {e}")
            return None

        # 3. Supply to Aave
        print(f"🏦 [YieldManager] Supplying {amount} {token_symbol} to Aave v3...")
        pool = w3.eth.contract(address=BASE_AAVE_V3_POOL, abi=AAVE_V3_POOL_ABI)
        supply_tx = pool.functions.supply(
            token_address, 
            amount_units, 
            self.agent.my_address, 
            0 # Referral code
        ).build_transaction({
            'from': self.agent.my_address,
            'nonce': self.agent._get_nonce(),
        })
        
        return self.agent._send_evm_transaction(supply_tx, wait=True, log_recipient=BASE_AAVE_V3_POOL, log_amount=amount, log_symbol=f"DEPOSIT-{token_symbol}")

    def get_yield_balance(self, token_symbol: str) -> float:
        """Checks how much has been deposited + interest."""
        atoken_address = self.atoken_map.get(self.agent.chain_name, {}).get(token_symbol)
        if not atoken_address:
            return 0.0
            
        try:
            from .tokens import ERC20_ABI
            atoken_contract = self.agent.w3.eth.contract(address=atoken_address, abi=ERC20_ABI)
            balance_units = atoken_contract.functions.balanceOf(self.agent.my_address).call()
            decimals = atoken_contract.functions.decimals().call()
            return float(balance_units) / (10 ** decimals)
        except Exception as e:
            print(f"⚠️ [YieldManager] Could not fetch balance from {self.protocol.upper()} (Network/Contract error)")
            return 0.0

    def harvest(self):
        """Reports current performance."""
        if not self.active:
            return
        
        try:
            # For now, just report USDC if on Base
            if self.agent.chain_name == "BASE":
                balance = self.get_yield_balance("USDC")
                print(f"🏦 [YieldManager] Current Aave Treasury: {balance:.6f} USDC")
        except Exception as e:
            print(f"⚠️ [YieldManager] Harvest failed: {e}")
