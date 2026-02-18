import inspect
try:
    import spl.token.client
    print("✅ spl.token.client FOUND")
    print(dir(spl.token.client))
except ImportError:
    print("❌ spl.token.client NOT found")

from spl.token.instructions import transfer, create_associated_token_account
print(f"Transfer Sig: {inspect.signature(transfer)}")
print(f"CreateATA Sig: {inspect.signature(create_associated_token_account)}")
