#!/bin/bash
# Enterprise Scaling: Setup PgBouncer for iAgentPay
# Run this on the VPS with sudo

echo "🚀 Installing PgBouncer..."
apt-get update
apt-get install -y pgbouncer

echo "⚙️ Configuring PgBouncer..."

# We need to map the internal iagent_db logic to PgBouncer
cat << 'EOF' > /etc/pgbouncer/pgbouncer.ini
[databases]
iagent_db = host=127.0.0.1 port=5432 dbname=iagent_db

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = trust
logfile = /var/log/postgresql/pgbouncer.log
pidfile = /var/run/postgresql/pgbouncer.pid
admin_users = postgres
# Limit incoming connections heavily to protect PG
max_client_conn = 1000
default_pool_size = 50
reserve_pool_size = 10
EOF

echo "🔄 Restarting PgBouncer service..."
systemctl enable pgbouncer
systemctl restart pgbouncer

echo "✅ PgBouncer is running on port 6432!"
EOF
