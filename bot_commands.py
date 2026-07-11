from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database import Database
from scraper.parser import SSHOceanScraper
import config
import time
from datetime import datetime

db = Database()
scraper = SSHOceanScraper()

# ============ 👑 ESSENTIELLES ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Accueil luxueux"""
    welcome = f"""
✨ {config.BOT_NAME} ✨
👑 Créé par {config.CREATOR}

🤖 Je surveille {len(config.UDP_SERVERS) + len(config.DNSTT_SERVERS)} serveurs SSHOcean 24/7

💎 Commandes rapides:
/status — Voir l'état actuel
/check — Scanner immédiatement
/servers — Liste des serveurs
/help — Toute l'aide

🔔 Je t'alerte dès qu'un serveur est disponible!
"""

    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data='status'),
            InlineKeyboardButton("🔍 Check", callback_data='check')
        ],
        [
            InlineKeyboardButton("📋 Serveurs", callback_data='servers'),
            InlineKeyboardButton("❓ Aide", callback_data='help')
        ]
    ]

    await update.message.reply_text(
        welcome,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aide rapide"""
    help_text = """
🆘 Aide rapide

👑 Essentielles
/start — Accueil
/status — État global
/check — Scan immédiat
/servers — Liste complète

💎 Filtres
/online — En ligne uniquement
/offline — Hors ligne
/udp — Serveurs UDP
/dnstt — Serveurs DNSTT

🌟 Infos
/stats — Statistiques
/alerts — Dernières alertes
/ping — Latence du bot
/about — Informations

Tape /commands pour voir toutes les commandes!
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toutes les commandes"""
    commands_text = """
📚 Toutes les commandes disponibles

👑 Essentielles
/start — Accueil luxueux
/help — Aide rapide
/commands — Cette liste
/status — État global
/summary — Résumé élégant
/stats — Statistiques détaillées
/check — Scan immédiat
/refresh — Actualiser le cache

💎 Serveurs
/servers — Liste complète
/online — Serveurs en ligne
/offline — Serveurs hors ligne
/udp — Serveurs UDP
/dnstt — Serveurs DNSTT
/country — Groupé par pays
/search mot — Recherche rapide
/host nom — Recherche hostname
/info pays — Détails d'un pays

🌟 Système
/alerts — Dernières alertes
/ping — Latence du bot
/uptime — Temps de fonctionnement
/version — Version du bot
/about — Informations

💡 Exemples:
/search germany — Cherche l'Allemagne
/info france — Détails de la France
"""
    await update.message.reply_text(commands_text, parse_mode=ParseMode.MARKDOWN)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """État global"""
    stats = db.get_stats()

    status_text = f"""
📊 ÉTAT GLOBAL

🟢 En ligne: {stats['online']} serveurs
🔴 Hors ligne: {stats['offline']} serveurs
🎫 Slots disponibles: {stats['total_slots']}

🟠 UDP: {stats['udp']} serveurs
🟢 DNSTT: {stats['dnstt']} serveurs

📅 Dernière vérification: {datetime.now().strftime('%H:%M:%S')}
"""
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Résumé élégant"""
    stats = db.get_stats()
    online_servers = db.get_servers_by_status('Online')

    text = f"""
💎 RÉSUMÉ ÉLÉGANT

✨ {stats['online']} serveurs actifs sur {stats['total']}
🎫 {stats['total_slots']} comptes disponibles

🌟 Top pays en ligne:
"""
    countries = {}
    for s in online_servers:
        countries[s['country']] = countries.get(s['country'], 0) + 1

    for country, count in sorted(countries.items(), key=lambda x: -x[1])[:5]:
        flag = {
            'france': '🇫🇷', 'germany': '🇩🇪', 'netherlands': '🇳🇱',
            'poland': '🇵🇱', 'uk': '🇬🇧', 'us': '🇺🇸', 'estonia': '🇪🇪',
            'finland': '🇫🇮', 'latvia': '🇱🇻', 'sweden': '🇸🇪'
        }.get(country, '🌍')
        text += f"  {flag} {country.title()}: {count}\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Statistiques détaillées"""
    stats = db.get_stats()

    text = f"""
📈 STATISTIQUES DÉTAILLÉES

📊 Général
• Total serveurs: {stats['total']}
• En ligne: {stats['online']} ({stats['online']*100//max(stats['total'],1)}%)
• Hors ligne: {stats['offline']}
• Total alertes: {stats['total_alerts']}

🔌 Par type
• UDP Custom: {stats['udp']}
• DNSTT (SlowDNS): {stats['dnstt']}

🎫 Disponibilité
• Slots totaux: {stats['total_slots']}
• Moyenne par serveur: {stats['total_slots']//max(stats['total'],1)}
"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scan immédiat"""
    message = await update.message.reply_text("🔍 Scan en cours...", parse_mode=ParseMode.MARKDOWN)

    servers = scraper.check_all_servers()
    changes = []

    for server in servers:
        change = db.update_server(server)
        if any([change['is_new'], change['went_online'], change['has_slots']]):
            changes.append(f"{server.country}: {server.status} ({server.accounts_remaining} slots)")

    result = f"""
✅ Scan terminé!

📊 {len(servers)} serveurs vérifiés
🔄 {len(changes)} changements détectés

{'📝 Changements:' if changes else '📭 Aucun changement'}
"""
    if changes:
        for c in changes[:10]:
            result += f"  • {c}\n"
        if len(changes) > 10:
            result += f"  ...et {len(changes)-10} autres"

    await message.edit_text(result, parse_mode=ParseMode.MARKDOWN)

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Actualiser le cache"""
    await update.message.reply_text("🔄 Cache actualisé!", parse_mode=ParseMode.MARKDOWN)

# ============ 💎 SERVEURS ============

async def servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Liste complète"""
    all_servers = db.get_all_servers()

    if not all_servers:
        await update.message.reply_text("❌ Aucun serveur en base. Faites /check d'abord!")
        return

    udp = [s for s in all_servers if s['type'] == 'udp']
    dnstt = [s for s in all_servers if s['type'] == 'dnstt']

    text = "🖥️ *TOUS LES SERVEURS*\n\n"

    if udp:
        text += "🟠 *UDP Custom:*\n"
        for s in udp:
            emoji = "🟢" if s['status'] == 'Online' else "🔴"
            text += f"  {emoji} {s['country'].title()}: {s['remaining']} slots\n"
        text += "\n"

    if dnstt:
        text += "🟢 *DNSTT (SlowDNS):*\n"
        for s in dnstt:
            emoji = "🟢" if s['status'] == 'Online' else "🔴"
            text += f"  {emoji} {s['country'].title()}: {s['remaining']} slots\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Serveurs en ligne"""
    servers = db.get_servers_by_status('Online')

    if not servers:
        await update.message.reply_text("🔴 Aucun serveur en ligne actuellement")
        return

    text = f"🟢 *SERVEURS EN LIGNE* ({len(servers)})\n\n"

    for s in servers:
        flag = {
            'france': '🇫🇷', 'germany': '🇩🇪', 'netherlands': '🇳🇱',
            'poland': '🇵🇱', 'uk': '🇬🇧', 'us': '🇺🇸', 'estonia': '🇪🇪',
            'finland': '🇫🇮', 'latvia': '🇱🇻', 'sweden': '🇸🇪'
        }.get(s['country'], '🌍')
        text += f"{flag} *{s['country'].title()}* ({s['type'].upper()})\n"
        text += f"   Host: `{s['host']}`\n"
        text += f"   🎫 {s['remaining']} slots disponibles\n\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def offline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Serveurs hors ligne"""
    servers = db.get_servers_by_status('Offline')

    if not servers:
        await update.message.reply_text("🟢 Tous les serveurs sont en ligne!")
        return

    text = f"🔴 *SERVEURS HORS LIGNE* ({len(servers)})\n\n"

    for s in servers:
        flag = {
            'france': '🇫🇷', 'germany': '🇩🇪', 'netherlands': '🇳🇱',
            'poland': '🇵🇱', 'uk': '🇬🇧', 'us': '🇺🇸', 'estonia': '🇪🇪',
            'finland': '🇫🇮', 'latvia': '🇱🇻', 'sweden': '🇸🇪'
        }.get(s['country'], '🌍')
        text += f"{flag} {s['country'].title()} ({s['type'].upper()})\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def udp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Serveurs UDP"""
    servers = db.get_servers_by_type('udp')

    text = "🟠 *SERVEURS UDP CUSTOM*\n\n"

    for s in servers:
        emoji = "🟢" if s['status'] == 'Online' else "🔴"
        flag = {
            'france': '🇫🇷', 'germany': '🇩🇪', 'netherlands': '🇳🇱',
            'poland': '🇵🇱', 'uk': '🇬🇧', 'us': '🇺🇸'
        }.get(s['country'], '🌍')
        text += f"{emoji} {flag} {s['country'].title()}\n"
        text += f"   `{s['host']}`\n"
        text += f"   🎫 {s['remaining']} slots\n\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def dnstt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Serveurs DNSTT"""
    servers = db.get_servers_by_type('dnstt')

    text = "🟢 *SERVEURS DNSTT (SlowDNS)*\n\n"

    for s in servers:
        emoji = "🟢" if s['status'] == 'Online' else "🔴"
        flag = {
            'france': '🇫🇷', 'germany': '🇩🇪', 'netherlands': '🇳🇱',
            'estonia': '🇪🇪', 'finland': '🇫🇮', 'latvia': '🇱🇻',
            'sweden': '🇸🇪', 'uk': '🇬🇧', 'us': '🇺🇸'
        }.get(s['country'], '🌍')
        text += f"{emoji} {flag} {s['country'].title()}\n"
        text += f"   `{s['host']}`\n"
        text += f"   🎫 {s['remaining']} slots\n\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Groupé par pays"""
    all_servers = db.get_all_servers()

    countries = {}
    for s in all_servers:
        if s['country'] not in countries:
            countries[s['country']] = []
        countries[s['country']].append(s)

    text = "🌍 *SERVEURS PAR PAYS*\n\n"

    for country, servers in sorted(countries.items()):
        flag = {
            'france': '🇫🇷', 'germany': '🇩🇪', 'netherlands': '🇳🇱',
            'poland': '🇵🇱', 'uk': '🇬🇧', 'us': '🇺🇸', 'estonia': '🇪🇪',
            'finland': '🇫🇮', 'latvia': '🇱🇻', 'sweden': '🇸🇪'
        }.get(country, '🌍')
        online = len([s for s in servers if s['status'] == 'Online'])
        text += f"{flag} {country.title()}: {online}/{len(servers)} en ligne\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recherche rapide"""
    if not context.args:
        await update.message.reply_text("❌ Usage: /search germany")
        return

    term = ' '.join(context.args).lower()
    results = db.search_servers(term)

    if not results:
        await update.message.reply_text(f"🔍 Aucun résultat pour '{term}'")
        return

    text = f"🔍 *Résultats pour '{term}'*\n\n"

    for r in results:
        emoji = "🟢" if r['status'] == 'Online' else "🔴"
        text += f"{emoji} {r['country'].title()} ({r['type'].upper()})\n"
        text += f"   `{r['host']}`\n\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recherche hostname"""
    if not context.args:
        await update.message.reply_text("❌ Usage: /host de1.ssht.site")
        return

    hostname = ' '.join(context.args).lower()
    results = db.search_servers(hostname)

    if not results:
        await update.message.reply_text(f"🔍 Host '{hostname}' non trouvé")
        return

    r = results[0]
    text = f"""
🖥️ INFORMATIONS HOST

Host: {r['host']}
Pays: {r['country'].title()}
Type: {r['type'].upper()}
Status: {'🟢 Online' if r['status'] == 'Online' else '🔴 Offline'}
"""

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Détails d'un pays"""
    if not context.args:
        await update.message.reply_text("❌ Usage: /info france")
        return

    country_name = ' '.join(context.args).lower()
    server = db.get_server_by_country(country_name)

    if not server:
        # Try live check
        live_server = scraper.check_single_country(country_name)
        if live_server:
            text = f"""
🇫🇷 {live_server.country.upper()} (LIVE)

🖥️ Host: {live_server.host}
🔌 Protocol: {live_server.protocol}
🔢 Port: {live_server.ssh_port}
⏱️ Validité: {live_server.validity}

📊 Status: {'🟢 Online' if live_server.status == 'Online' else '🔴 Offline'}
🎫 Slots: {live_server.accounts_remaining} disponibles
"""
        else:
            await update.message.reply_text(f"❌ Pays '{country_name}' non trouvé")
            return
    else:
        text = f"""
🇫🇷 {server['country'].upper()}

🖥️ Host: {server['host']}
🔌 Protocol: {server['protocol']}
📊 Status: {'🟢 Online' if server['status'] == 'Online' else '🔴 Offline'}
🎫 Slots: {server['remaining']} disponibles

📅 Premier scan: {server['first_seen'][:10]}
🔄 Dernier check: {server['last_check'][:10]}
"""

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ============ 🌟 SYSTÈME ============

async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dernières alertes"""
    alerts_list = db.get_recent_alerts(10)

    if not alerts_list:
        await update.message.reply_text("📭 Aucune alerte récente")
        return

    text = "🔔 *DERNIÈRES ALERTES*\n\n"

    for a in alerts_list:
        emoji = {'new': '✨', 'online': '🟢', 'slots': '🎫'}.get(a['type'], '📌')
        text += f"{emoji} *{a['type'].upper()}*\n"
        text += f"   {a['country'].title()} — {a['time'][11:16]}\n"
        text += f"   _{a['message'][:50]}..._\n\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Latence du bot"""
    start = time.time()
    message = await update.message.reply_text("🏓 Ping...", parse_mode=ParseMode.MARKDOWN)
    end = time.time()

    latency = round((end - start) * 1000)

    await message.edit_text(f"🏓 *Pong!*\n\nLatence: `{latency}ms`", parse_mode=ParseMode.MARKDOWN)

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Temps de fonctionnement"""
    now = datetime.now()
    delta = now - config.START_TIME

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    text = f"""
⏱️ UPTIME

🤖 En ligne depuis:
{days} jours, {hours}h {minutes}m {seconds}s

🚀 Démarré: {config.START_TIME.strftime('%d/%m/%Y %H:%M:%S')}
"""

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Version du bot"""
    text = f"""
📦 VERSION

🤖 {config.BOT_NAME}
🔢 Version: {config.VERSION}
👑 Créateur: {config.CREATOR}

🐍 Python 3.11
📚 python-telegram-bot 20.7
🔍 CloudScraper 1.2.71
"""

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Informations"""
    text = f"""
💎 À PROPOS

🤖 {config.BOT_NAME}
Surveillance automatique des serveurs SSHOcean

👑 Créé avec passion par {config.CREATOR}

🎯 Fonctionnalités:
• Scan automatique toutes les 3 minutes
• Détection nouveaux serveurs
• Alertes instantanées Telegram
• Support UDP & DNSTT
• 15 pays surveillés

📡 Technologies:
Python • Telegram Bot • Render • SQLite
"""

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# Callback handler pour les boutons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'status':
        await status(update, context)
    elif query.data == 'check':
        await check(update, context)
    elif query.data == 'servers':
        await servers(update, context)
    elif query.data == 'help':
        await help_command(update, context)
