#!/bin/bash
# Universal VPS setup script (Ubuntu 22.04)
# Run this on a fresh VPS to deploy any bot

set -e

echo "=== Installing system dependencies ==="
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv git screen

echo "=== Creating bot user ==="
useradd -m -s /bin/bash botuser 2>/dev/null || true

echo "=== Done. Now upload your bot files and run: ==="
echo "  cd /home/botuser/<bot-folder>"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  cp .env.example .env && nano .env"
echo "  screen -S bot python bot.py"
echo ""
echo "To keep bot running after SSH disconnect: use 'screen -d' to detach"
echo "To reconnect: screen -r bot"
