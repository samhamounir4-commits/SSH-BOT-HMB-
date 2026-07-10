from telegram import Bot
from telegram.constants import ParseMode
import asyncio
from typing import List, Dict
import config

class TelegramNotifier:
    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_TOKEN)
        self.chat_id = config.TELEGRAM_CHAT_ID
    
    async def notify_new_servers(self, servers: List[Dict]):
        if not servers:
            return
        
        udp = [s for s in servers if s['type'] == 'udp']
        dnstt = [s for s in servers if s['type'] == 'dnstt']
        
        if udp:
            msg = "🟠 *SERVEURS UDP*\n\n"
            for s in udp[:5]:
                flag = {'france':'🇫🇷','germany':'🇩🇪','netherlands':'🇳🇱',
                        'poland':'🇵🇱','uk':'🇬🇧','us':'🇺🇸'}.get(s['country'], '🌍')
                msg += f"{flag} *{s['country'].upper()}*\n"
                msg += f"Host: `{s['host']}`\n"
                msg += f"Status: {s['status']} | Slots: {s['remaining']}\n\n"
            await self.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)
        
        if dnstt:
            msg = "🟢 *SERVEURS DNSTT*\n\n"
            for s in dnstt[:5]:
                flag = {'france':'🇫🇷','germany':'🇩🇪','netherlands':'🇳🇱',
                        'estonia':'🇪🇪','finland':'🇫🇮','latvia':'🇱🇻',
                        'sweden':'🇸🇪','uk':'🇬🇧','us':'🇺🇸'}.get(s['country'], '🌍')
                msg += f"{flag} *{s['country'].upper()}*\n"
                msg += f"Host: `{s['host']}`\n"
                msg += f"Status: {s['status']} | Slots: {s['remaining']}\n\n"
            await self.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)
    
    async def notify_status_change(self, server: Dict, change_type: str):
        flag = {'france':'🇫🇷','germany':'🇩🇪','netherlands':'🇳🇱',
                'poland':'🇵🇱','uk':'🇬🇧','us':'🇺🇸','estonia':'🇪🇪',
                'finland':'🇫🇮','latvia':'🇱🇻','sweden':'🇸🇪'}.get(server['country'], '🌍')
        
        if change_type == 'went_online':
            msg = f"✅ *ONLINE!* {flag} {server['country'].upper()}\n\nHost: `{server['host']}`\nSlots: {server['remaining']} dispo\nType: {server['type'].upper()}"
        else:
            msg = f"🎉 *SLOTS!* {flag} {server['country'].upper()}\n\nHost: `{server['host']}`\n{server['remaining']} comptes dispo!"
        
        await self.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)
