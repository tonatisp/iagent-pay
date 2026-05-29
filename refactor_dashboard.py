import os
import re

dashboard_path = r"C:\Users\E-100\Desktop\iagentpay-al-100\respaldo iagent-pay 23.05.26\serve_dashboard.py"

with open(dashboard_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add import
import_db = "from iagent_pay.db_adapter import DBAdapter\n"
if "DBAdapter" not in content:
    content = content.replace("import sqlite3\n", "import sqlite3\n" + import_db)

# Replace conn = sqlite3.connect(...) with DBAdapter(...).connect()
content = re.sub(
    r"sqlite3\.connect\(\s*db_path[^)]*\)",
    r"DBAdapter(db_path).connect()",
    content
)

content = re.sub(
    r"sqlite3\.connect\(\s*rep_path[^)]*\)",
    r"DBAdapter(rep_path).connect()",
    content
)

# Remove conn.execute('PRAGMA journal_mode=WAL;') as DBAdapter handles it
content = re.sub(
    r"conn\.execute\('PRAGMA journal_mode=WAL;'\)",
    r"pass",
    content
)

# Remove conn.row_factory = sqlite3.Row as we'll handle it in DBAdapter if needed
content = re.sub(
    r"conn\.row_factory = sqlite3\.Row",
    r"pass",
    content
)

with open(dashboard_path, "w", encoding="utf-8") as f:
    f.write(content)

print("serve_dashboard.py refactored successfully.")
