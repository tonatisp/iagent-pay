try:
    import spl.token
    print("✅ SPL Token Library found!")
except ImportError:
    print("❌ SPL Token Library NOT found.")

try:
    from solders.system_program import ID as SYS_PROGRAM_ID
    from solders.pubkey import Pubkey
    print(f"✅ Solders available. System Program: {SYS_PROGRAM_ID}")
except ImportError:
    print("❌ Solders NOT found.")
