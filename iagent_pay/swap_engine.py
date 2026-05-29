import time

# ─────────────────────────────────────────────────────────────────────────────
# iAgentPay — Swap Engine v4.0
#
# PRODUCTION STATUS:
#   ✅ Solana: Routes to Jupiter Aggregator API (real quotes, real swaps)
#   ✅ EVM:    Routes to 0x Protocol / Uniswap API (real quotes)
#   ⚠️  Execution on EVM requires a signed transaction (not yet wired for MVP)
#
# For MVP/testnet purposes, execution is simulated but quotes ARE real.
# Set SWAP_LIVE_MODE=1 environment variable to enable live EVM execution.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("iagentpay.swap")

LIVE_MODE = os.environ.get("SWAP_LIVE_MODE", "0") == "1"


class SwapEngine:
    """
    Token swap engine for iAgentPay agents.

    - Solana: Uses Jupiter Aggregator API for real price quotes.
    - EVM: Uses 0x Protocol API for real price quotes.
    - Execution: Live on Solana (Jupiter) and EVM (0x Router) when SWAP_LIVE_MODE=1.
    """

    def __init__(self, agent):
        self.agent = agent

    def _get_token_decimals(self, symbol: str) -> int:
        symbol = symbol.upper()
        if symbol in ["ETH", "MATIC", "BNB", "DAI"]:
            return 18
        if symbol in ["USDC", "USDT", "EURC"]:
            return 6
        if self.agent.is_solana:
            if symbol == "SOL":
                return 9
            if symbol == "BONK":
                return 5
            if symbol == "WIF":
                return 6
            if symbol == "POPCAT":
                return 9
            if symbol == "PEPE":
                return 6
        # On EVM, try to fetch on-chain
        if not self.agent.is_solana and not self.agent.is_xrp:
            try:
                addr = self.agent._resolve_token_address(symbol)
                if addr:
                    from iagent_pay.tokens import ERC20_ABI
                    contract = self.agent.w3.eth.contract(address=addr, abi=ERC20_ABI)
                    return int(self.agent._execute_rpc_with_backoff(contract.functions.decimals().call))
            except Exception:
                pass
        return 18  # default fallback

    def get_quote(self, input_token: str, output_token: str, amount: float, slippage_bps: int = 50) -> dict:
        """
        Fetches a real swap quote from Jupiter (Solana) or 0x Protocol (EVM).
        Falls back to mock data if APIs are unreachable.
        """
        if self.agent.is_solana:
            return self._quote_jupiter(input_token, output_token, amount, slippage_bps)
        else:
            return self._quote_0x(input_token, output_token, amount, slippage_bps)

    def _quote_jupiter(self, input_token: str, output_token: str, amount: float, slippage_bps: int = 50) -> dict:
        """Fetch quote from Jupiter Aggregator (Solana)."""
        # Jupiter uses Solana mint addresses; use known mints for common tokens
        mints = {
            "SOL":  "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "WIF":  "EKpQGSJtjMFqKZ9KQGWjhDk9scGEC1tx4SHZa9sZwtqa",
            "POPCAT": "7GCih6xsf14w6jeRaoHTMRSTb9QXTYBiMetXFJuqdcuA",
            "PEPE": "25nKQr8s65jW6P9G9C23CqGfNScwS1D2Y9854D2wWp3w"
        }
        dec_map = {
            "SOL": 9, "USDC": 6, "BONK": 5, "WIF": 6, "POPCAT": 9, "PEPE": 6
        }
        
        input_token_upper = input_token.upper()
        output_token_upper = output_token.upper()
        
        input_mint  = mints.get(input_token_upper, input_token)
        output_mint = mints.get(output_token_upper, output_token)

        # Scale amount by token decimals
        in_dec = dec_map.get(input_token_upper, 6)
        out_dec = dec_map.get(output_token_upper, 6)
        amount_raw = int(amount * (10 ** in_dec))

        url = (
            f"https://quote-api.jup.ag/v6/quote"
            f"?inputMint={input_mint}&outputMint={output_mint}"
            f"&amount={amount_raw}&slippageBps={slippage_bps}"
        )
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            out_amount = int(data.get("outAmount", 0))
            out_ui     = out_amount / (10 ** out_dec)
            rate       = out_ui / amount if amount else 0
            logger.info(f"[SwapEngine] Jupiter quote: {amount} {input_token} → {out_ui} {output_token}")
            return {
                "input": amount, "output": out_ui, "rate": rate,
                "slippage": slippage_bps / 100.0, "provider": "Jupiter Aggregator (Live)",
                "source": "live", "raw_quote_response": data
            }
        except Exception as e:
            logger.warning(f"[SwapEngine] Jupiter API unavailable ({e}), using mock.")
            return self._mock_quote(input_token, output_token, amount, "Jupiter (Fallback)", slippage_bps)

    def _quote_0x(self, input_token: str, output_token: str, amount: float, slippage_bps: int = 50) -> dict:
        """Fetch quote from 0x Protocol (EVM chains)."""
        # 0x API requires an API key for production; use mock for MVP
        # To enable: set ZEROX_API_KEY environment variable
        api_key = os.environ.get("ZEROX_API_KEY", "")
        if not api_key:
            logger.info("[SwapEngine] ZEROX_API_KEY not set — using mock quote for EVM swap.")
            return self._mock_quote(input_token, output_token, amount, "Uniswap (Mock — set ZEROX_API_KEY for live)", slippage_bps)

        input_decimals = self._get_token_decimals(input_token)
        output_decimals = self._get_token_decimals(output_token)
        
        sell_amount = int(amount * (10 ** input_decimals))
        slippage_pct = slippage_bps / 10000.0
        url = (
            f"https://api.0x.org/swap/v1/quote"
            f"?sellToken={input_token}&buyToken={output_token}&sellAmount={sell_amount}"
            f"&slippagePercentage={slippage_pct}"
        )
        headers = {"0x-api-key": api_key}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            buy_amount = int(data.get("buyAmount", 0)) / (10 ** output_decimals)
            rate = buy_amount / amount if amount else 0
            logger.info(f"[SwapEngine] 0x quote: {amount} {input_token} → {buy_amount} {output_token}")
            return {
                "input": amount, "output": buy_amount, "rate": rate,
                "slippage": slippage_bps / 100.0, "provider": "0x Protocol (Live)",
                "source": "live",
                "tx_data": {
                    "to": data.get("to"),
                    "data": data.get("data"),
                    "value": data.get("value"),
                    "allowanceTarget": data.get("allowanceTarget"),
                    "gas": data.get("gas"),
                    "gasPrice": data.get("gasPrice")
                }
            }
        except Exception as e:
            logger.warning(f"[SwapEngine] 0x API error ({e}), using mock.")
            return self._mock_quote(input_token, output_token, amount, "Uniswap (Fallback)", slippage_bps)

    def _mock_quote(self, input_token: str, output_token: str,
                    amount: float, provider: str, slippage_bps: int = 50) -> dict:
        """Approximate mock rates when live APIs are unavailable."""
        rates = {
            "SOL_USDC": 145.0, "USDC_SOL": 0.0069,
            "ETH_USDC": 3200.0, "USDC_ETH": 0.0003125,
            "SOL_BONK": 20000.0, "ETH_PEPE": 1_000_000.0,
            "SOL_WIF": 50.0, "SOL_POPCAT": 70.0, "SOL_PEPE": 500000.0
        }
        pair = f"{input_token.upper()}_{output_token.upper()}"
        rate = rates.get(pair, 1.0)
        return {
            "input": amount, "output": round(amount * rate, 6),
            "rate": rate, "slippage": slippage_bps / 100.0,
            "provider": provider, "source": "mock"
        }

    def execute_swap(self, input_token: str, output_token: str,
                     amount: float, min_output_amount: float = 0.0, slippage_bps: int = 50) -> dict:
        """
        Executes a token swap.

        On Solana with SWAP_LIVE_MODE=1: routes to Jupiter for real execution.
        On EVM with SWAP_LIVE_MODE=1: routes to 0x Protocol for real execution.
        Without live mode: simulates the swap.

        Args:
            min_output_amount: Slippage protection — reject if output < this value.
            slippage_bps: slippage tolerance in basis points.
        """
        quote = self.get_quote(input_token, output_token, amount, slippage_bps)

        if quote["output"] < min_output_amount:
            raise ValueError(
                f"Slippage protection triggered: expected ≥ {min_output_amount} "
                f"{output_token}, got {quote['output']}. Swap aborted."
            )

        if LIVE_MODE and quote.get("source") == "live":
            if self.agent.is_solana:
                # Live Solana swap via Jupiter
                raw_quote = quote.get("raw_quote_response")
                if not raw_quote:
                    raise ValueError("Jupiter quote did not return raw_quote_response payload for execution.")
                
                print(f"💸 Executing live Solana swap via Jupiter API...")
                try:
                    mock_sig = self._execute_jupiter_swap(raw_quote)
                except Exception as e:
                    logger.error(f"[SwapEngine] Jupiter swap execution failed: {e}")
                    raise
            else:
                # Live EVM swap via 0x Protocol
                tx_data = quote.get("tx_data")
                if not tx_data or not tx_data.get("to") or not tx_data.get("data"):
                    raise ValueError("0x quote did not return transaction payload for execution.")
                
                # Check and approve allowance if input_token is an ERC-20
                input_token_upper = input_token.upper()
                if input_token_upper not in ["ETH", "MATIC", "BNB"]:
                    token_address = self.agent._resolve_token_address(input_token_upper)
                    if not token_address:
                        raise ValueError(f"Could not resolve token address for {input_token}")
                    
                    allowance_target = tx_data.get("allowanceTarget")
                    if not allowance_target:
                        raise ValueError("0x quote did not return allowanceTarget address.")
                    
                    from iagent_pay.tokens import ERC20_ABI
                    contract = self.agent.w3.eth.contract(address=token_address, abi=ERC20_ABI)
                    
                    # Fetch current allowance
                    current_allowance = self.agent._execute_rpc_with_backoff(
                        contract.functions.allowance(self.agent.my_address, allowance_target).call
                    )
                    
                    input_decimals = self._get_token_decimals(input_token)
                    sell_amount = int(amount * (10 ** input_decimals))
                    
                    if current_allowance < sell_amount:
                        print(f"🔄 Insufficient allowance for 0x Router (Have: {current_allowance}, Needed: {sell_amount}).")
                        print(f"🔄 Sending ERC20 approval transaction to {allowance_target}...")
                        
                        # Approve max value
                        approve_tx = contract.functions.approve(allowance_target, 2**256 - 1).build_transaction({
                            'chainId': self.agent.w3.eth.chain_id,
                            'gas': 60000,
                            'gasPrice': self.agent._get_smart_gas_price(),
                            'nonce': self.agent._get_nonce()
                        })
                        
                        approve_hash = self.agent._send_evm_transaction(approve_tx, wait=True)
                        print(f"✅ Approval Transaction Confirmed. Tx: {approve_hash}")
                
                # Execute Swap Transaction
                print(f"💸 Executing live EVM swap via 0x Router ({quote['provider']})...")
                
                gas_limit = int(tx_data.get("gas", 250000))
                gas_limit = int(gas_limit * 1.2) # +20% safety margin
                value = int(tx_data.get("value", 0))
                
                swap_tx = {
                    'to': tx_data["to"],
                    'data': tx_data["data"],
                    'value': value,
                    'gas': gas_limit,
                    'gasPrice': self.agent._get_smart_gas_price(),
                    'nonce': self.agent._get_nonce(),
                    'chainId': self.agent.w3.eth.chain_id
                }
                
                real_hash = self.agent._send_evm_transaction(swap_tx, wait=True)
                mock_sig = real_hash
        else:
            if LIVE_MODE:
                logger.warning(
                    "[SwapEngine] ⚠️ LIVE MODE requested but execution is simulated for this chain or API is mocked."
                )
            else:
                logger.info(
                    "[SwapEngine] 🔶 SIMULATION MODE — no real funds moved. "
                    "Set SWAP_LIVE_MODE=1 to enable live swaps."
                )
            mock_sig = f"SIM_SWAP_{int(time.time())}"

        logger.info(
            f"[SwapEngine] {amount} {input_token} → {quote['output']} {output_token} "
            f"via {quote['provider']}"
        )

        return {
            "tx_hash":       mock_sig,
            "input_token":   input_token,
            "output_token":  output_token,
            "input_amount":  amount,
            "output_amount": quote["output"],
            "rate":          quote["rate"],
            "provider":      quote["provider"],
            "simulated":     not (LIVE_MODE and quote.get("source") == "live"),
            "timestamp":     time.time(),
        }

    def _execute_jupiter_swap(self, raw_quote: dict) -> str:
        import urllib.request
        import json
        
        url = "https://quote-api.jup.ag/v6/swap"
        req_body = {
            "quoteResponse": raw_quote,
            "userPublicKey": self.agent.solana.get_address(),
            "wrapAndUnwrapSol": True
        }
        
        req = urllib.request.Request(url, data=json.dumps(req_body).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            
        swap_tx_b64 = data.get("swapTransaction")
        if not swap_tx_b64:
            raise ValueError(f"Jupiter /v6/swap did not return swapTransaction: {data}")
            
        return self.agent.solana.execute_versioned_transaction(swap_tx_b64)
