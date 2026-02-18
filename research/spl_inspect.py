from spl.token.instructions import transfer_checked, transfer, create_associated_token_account
import inspect

print("--- Transfer Checked ---")
try:
    print(inspect.signature(transfer_checked))
except:
    print("Could not get signature")

print("\n--- Transfer ---")
try:
    print(inspect.signature(transfer))
except:
    print("Could not get signature")

print("\n--- Create ATA ---")
try:
    print(inspect.signature(create_associated_token_account))
except:
    print("Could not get signature")
