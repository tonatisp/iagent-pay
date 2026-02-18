import json
import time
import uuid

class InvoiceManager:
    """
    Handles AIP-1 (Agent Invoice Protocol) creation and validation.
    """
    
    def __init__(self, agent):
        self.agent = agent

    def create_invoice(self, amount: float, currency: str, chain: str, description: str, expiry_hours=24) -> str:
        """
        Generates a signed JSON invoice string.
        """
        chain = chain.upper()
        currency = currency.upper()
        
        invoice = {
            "protocol": "iagent-pay/v1",
            "invoice_id": f"inv_{uuid.uuid4().hex[:8]}",
            "created_at": int(time.time()),
            "expires_at": int(time.time()) + (expiry_hours * 3600),
            "recipient": self.agent.my_address,
            "amount": amount,
            "currency": currency,
            "chain": chain,
            "description": description,
            "memo": f"Payment for {description}"
        }
        
        # In a full version, we would sign this JSON with the wallet key.
        # For MVP, we just serialize it.
        return json.dumps(invoice, indent=2)

    def parse_invoice(self, invoice_json: str) -> dict:
        """
        Validates and parses the invoice.
        Raises ValueError if invalid or expired.
        """
        try:
            data = json.loads(invoice_json)
        except:
            raise ValueError("Invalid JSON format.")
            
        # Basic Validation
        required = ["protocol", "recipient", "amount", "currency", "chain", "expires_at"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing field: {field}")
                
        if data["expires_at"] < time.time():
            raise ValueError("Invoice has EXPIRED.")
            
        return data
