# 🚀 iAgentPay Production Deployment Guide

This guide explains how to deploy your AI Agent swarm to a Linux VPS (Ubuntu 22.04).

## Prerequisites
*   A Linux VPS (DigitalOcean Droplet, AWS EC2, or Hetzner).
*   SSH Access.
*   Your `wallet_key.json` or private keys.

---

## 1. Server Setup (Ubuntu)

Connect to your server:
```bash
ssh root@your-server-ip
```

Update and install Docker:
```bash
sudo apt update && sudo apt upgrade -y
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

## 2. Deploy iAgentPay Stack

Clone your repository (or copy files):
```bash
mkdir iagent-pay && cd iagent-pay
# COPY your Dockerfile, docker-compose.yml, and src here
```

Create a `.env` file for secrets:
```bash
nano .env
```
_Paste:_
```
AGENT_PRIVATE_KEY=0xYourPrivateKeyHere...
SOLANA_PRIVATE_KEY=[123, 45, ...]
```

## 3. Launch Swarm

Start the containers in detached mode:
```bash
docker compose up -d --build
```

Check status:
```bash
docker compose ps
```

View logs:
```bash
docker compose logs -f agent-alpha
```

---

## 4. Updates & Maintenance

To update your agents with new code:
```bash
git pull origin main
docker compose up -d --build
```
This performs a zero-downtime rolling update (if configured) or a quick restart.
