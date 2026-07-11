from flask import Flask
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.parser import SSHOceanScraper
from database import Database
from notifier import TelegramNotifier
import bot_commands as cmd
import config
import asyncio
import os
import threading
from datetime import datetime

app = Flask(__name__)
db = Database()
scraper = SSHOceanScraper()

def check_servers():
    """Monitoring automatique"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Vérification...")

    try:
        servers = scraper.check_all_servers()

        for server in servers:
            changes = db.update_server(server)

            if changes['is_new'] or changes['went_online'] or changes['has_slots']:
                notifier = TelegramNotifier()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                data = {
                    'host': server.host,
                    'country': server.country,
                    'type': server.server_type,
                    'status': server.status,
                    'remaining': server.accounts_remaining,
                    'url': server.url
                }

                if changes['is_new']:
                    loop.run_until_complete(notifier.notify_new_servers([data]))
                    db.mark_notified(server.host, 'online')
                elif changes['went_online']:
                    loop.run_until_complete(notifier.notify_status_change(data, 'went_online'))
                    db.mark_notified(server.host, 'online')
                elif changes['has_slots']:
                    loop.run_until_complete(notifier.notify_status_change(data, 'has_slots'))
                    db.mark_notified(server.host, 'available')

                loop.close()
    except Exception as e:
        print(f"Erreur monitoring: {e}")

@app.route('/')
def health():
    stats = db.get_stats()
    return {
        "status": "alive",
        "bot": config.BOT_NAME,
        "version": config.VERSION,
        "creator": config.CREATOR,
        "online": stats['online'],
        "offline": stats['offline']
    }

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

def run_telegram():
    """Lance le bot Telegram"""
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # 👑 Essentielles
    application.add_handler(CommandHandler("start", cmd.start))
    application.add_handler(CommandHandler("help", cmd.help_command))
    application.add_handler(CommandHandler("commands", cmd.commands))
    application.add_handler(CommandHandler("status", cmd.status))
    application.add_handler(CommandHandler("summary", cmd.summary))
    application.add_handler(CommandHandler("stats", cmd.stats))
    application.add_handler(CommandHandler("check", cmd.check))
    application.add_handler(CommandHandler("refresh", cmd.refresh))

    # 💎 Serveurs
    application.add_handler(CommandHandler("servers", cmd.servers))
    application.add_handler(CommandHandler("online", cmd.online))
    application.add_handler(CommandHandler("offline", cmd.offline))
    application.add_handler(CommandHandler("udp", cmd.udp))
    application.add_handler(CommandHandler("dnstt", cmd.dnstt))
    application.add_handler(CommandHandler("country", cmd.country))
    application.add_handler(CommandHandler("search", cmd.search))
    application.add_handler(CommandHandler("host", cmd.host))
    application.add_handler(CommandHandler("info", cmd.info))

    # 🌟 Système
    application.add_handler(CommandHandler("alerts", cmd.alerts))
    application.add_handler(CommandHandler("ping", cmd.ping))
    application.add_handler(CommandHandler("uptime", cmd.uptime))
    application.add_handler(CommandHandler("version", cmd.version))
    application.add_handler(CommandHandler("about", cmd.about))

    # Callbacks boutons
    application.add_handler(CallbackQueryHandler(cmd.button_callback))

    # Webhook pour Render
    webhook_url = os.environ.get('WEBHOOK_URL')
    if webhook_url:
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get('PORT', 10000)),
            webhook_url=webhook_url
        )
    else:
        application.run_polling()

def main():
    # Premier check
    check_servers()

    # Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_servers, 'interval', minutes=3, id='monitor')
    scheduler.start()

    # Lancer Flask dans un thread séparé
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Lancer Telegram (bloquant)
    run_telegram()

if __name__ == '__main__':
    main()
