import sys
from eth_account import Account

# The key from .env
key = "f03a64330ac1cc091fe4290c7d81161cbe1ddf0e40fea7b84038775f9f2ef2d3"
account = Account.from_key(key)
addr = account.address

print(f"Address: {addr}")
print(f"Length: {len(addr)}")

if len(addr) != 42:
    print("❌ INVALID ADDRESS LENGTH!")
else:
    print("✅ VALID ADDRESS LENGTH")

# Clean output for user
print(f"\nCLEAN_ADDRESS_TO_COPY: {addr}")
