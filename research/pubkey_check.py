from solders.pubkey import Pubkey

s = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
try:
    p = Pubkey.from_string(s)
    print(f"✅ Success: {p}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Check with repr
print(f"String: {repr(s)}")
