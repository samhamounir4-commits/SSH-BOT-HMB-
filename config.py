import os
from datetime import datetime

# Meta
CREATOR = "🇭 🇲 🇧"
VERSION = "2.0.0"
BOT_NAME = "SSHOcean Monitor"

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# URLs
UDP_SERVERS = {
    "france": "https://sshocean.com/ssh-udp/france",
    "germany": "https://sshocean.com/ssh-udp/germany",
    "netherlands": "https://sshocean.com/ssh-udp/netherlands",
    "poland": "https://sshocean.com/ssh-udp/polan",
    "uk": "https://sshocean.com/ssh-udp/united-kingdom",
    "us": "https://sshocean.com/ssh-udp/united-states",
}

DNSTT_SERVERS = {
    "germany": "https://sshocean.com/ssh-dnstt/germany",
    "estonia": "https://sshocean.com/ssh-dnstt/estonia",
    "finland": "https://sshocean.com/ssh-dnstt/finland",
    "france": "https://sshocean.com/ssh-dnstt/france",
    "latvia": "https://sshocean.com/ssh-dnstt/latvia",
    "netherlands": "https://sshocean.com/ssh-dnstt/netherlands",
    "sweden": "https://sshocean.com/ssh-dnstt/sweden",
    "uk": "https://sshocean.com/ssh-dnstt/united-kingdom",
    "us": "https://sshocean.com/ssh-dnstt/united-states",
}

START_TIME = datetime.now()
