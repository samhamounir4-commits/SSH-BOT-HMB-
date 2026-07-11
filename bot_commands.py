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

FLAG_MAP = {
    "france": "🇫🇷",
    "germany": "🇩🇪",
    "netherlands": "🇳🇱",
    "poland": "🇵🇱",
    "uk": "🇬🇧",
    "us": "🇺🇸",
    "estonia": "🇪🇪",
    "finland": "🇫🇮",
    "latvia": "🇱🇻",
    "sweden": "🇸🇪",
}


def flag(country: str) -> str:
    return FLAG_MAP.get(country.lower(), "🌍")


async def send(update: Update, text: str, **kwargs):
    if update.message:
        return await update.message.reply_text(text, **kwargs)
    if update.callback_query and update.callback_query.message:
        return await update.callback_query.message.reply_text(text, **kwargs)
    return None


# ============ 👑 ESSENTIELLES ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = f"""
✨ *{config.BOT_NAME}* ✨
👑 Créé par {config.CREATOR}

🤖 Je surveille {len(config.UDP_SERVERS) + len(config.DNSTT_SERVERS)} serveurs SSHOcean 24/7

💎 *Commandes rapides:*
/status — Voir l'état actuel
/check — Scanner immédiatement
/servers — Liste des serveurs
/help — Toute l'aide

🔔 Je t'alerte dès qu'un serveur est disponible!
"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("🔍 Check", callback_data="check"),
        ],
        [
            InlineKeyboardButton("📋 Serveurs", callback_data="servers"),
            InlineKeyboardButton("❓ Aide", callback_data="help"),
        ],
    ]

    await send(
        update,
        welcome,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🆘 *Aide rapide*

👑 *Essentielles*
/start — Accueil
/status — État global
/check — Scan immédiat
/servers — Liste complète

💎 *Filtres*
/online — En ligne uniquement
/offline — Hors ligne
/udp — Serveurs UDP
/dnstt — Serveurs DNSTT

🌟 *Infos*
/stats — Statistiques
/alerts — Dernières alertes
/ping — Latence du bot
/about — Informations

Tape /commands pour voir toutes les commandes!
"""
    await send(update, help_text, parse_mode=ParseMode.MARKDOWN)


async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands_text = """
📚 *Toutes les commandes disponibles*

👑 *Essentielles*
/start — Accueil luxueux
/help — Aide rapide
/commands — Cette liste
/status — État global
/summary — Résumé élégant
/stats — Statistiques détaillées
/check — Scan immédiat
/refresh — Actualiser le cache

💎 *Serveurs*
/servers — Liste complète
/online — Serveurs en ligne
/offline — Serveurs hors ligne
/udp — Serveurs UDP
/dnstt — Serveurs DNSTT
/country — Groupé par pays
/search *mot* — Recherche rapide
/host *nom* — Recherche hostname
/info *pays* — Détails d'un pays

🌟 *Système*
/alerts — Dernières alertes
/ping — Latence du bot
/uptime — Temps de fonctionnement
/version — Version du bot
/about — Informations

💡 *Exemples:*
`/search germany` — Cherche l'Allemagne
`/info france` — Détails de la France
"""
    await send(update, commands_text, parse_mode=ParseMode.MARKDOWN)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = db.get_stats()

    status_text = f"""
📊 *ÉTAT GLOBAL*

🟢 En ligne: {stats['online']} serveurs
🔴 Hors ligne: {stats['offline']} serveurs
🎫 Slots disponibles: {stats['total_slots']}

🟠 UDP: {stats['udp']} serveurs
🟢 DNSTT: {stats['dnstt']} serveurs

📅 Dernière vérification: {datetime.now().strftime('%H:%M:%S')}
"""
    await send(update, status_text, parse_mode=ParseMode.MARKDOWN)


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = db.get_stats()
    online_servers = db.get_servers_by_status("Online")

    text = f"""
💎 *RÉSUMÉ ÉLÉGANT*

✨ {stats['online']} serveurs actifs sur {stats['total']}
🎫 {stats['total_slots']} comptes disponibles

🌟 *Top pays en ligne:*
"""
    countries = {}
    for s in online_servers:
        countries[s["country"]] = countries.get(s["country"], 0) + 1

    for country_name, count in sorted(countries.items(), key=lambda x: -x[1])[:5]:
        text += f"  {flag(country_name)} {country_name.title()}: {count}\n"

    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = db.get_stats()

    text = f"""
📈 *STATISTIQUES DÉTAILLÉES*

📊 *Général*
• Total serveurs: {stats['total']}
• En ligne: {stats['online']} ({stats['online'] * 100 // max(stats['total'], 1)}%)
• Hors ligne: {stats['offline']}
• Total alertes: {stats['total_alerts']}

🔌 *Par type*
• UDP Custom: {stats['udp']}
• DNSTT (SlowDNS): {stats['dnstt']}

🎫 *Disponibilité*
• Slots totaux: {stats['total_slots']}
• Moyenne par serveur: {stats['total_slots'] // max(stats['total'], 1)}
"""
    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await send(update, "🔍 *Scan en cours...*", parse_mode=ParseMode.MARKDOWN)

    servers = scraper.check_all_servers()
    changes = []

    for server in servers:
        change = db.update_server(server)
        if change["is_new"] or change["went_online"] or change["has_slots"]:
            changes.append(f"{server.country}: {server.status} ({server.accounts_remaining} slots)")

    result = f"""
✅ *Scan terminé!*

📊 {len(servers)} serveurs vérifiés
🔄 {len(changes)} changements détectés

{'📝 Changements:' if changes else '📭 Aucun changement'}
"""
    if changes:
        for c in changes[:10]:
            result += f"  • {c}\n"
        if len(changes) > 10:
            result += f"  ...et {len(changes) - 10} autres"

    if message:
        await message.edit_text(result, parse_mode=ParseMode.MARKDOWN)
    else:
        await send(update, result, parse_mode=ParseMode.MARKDOWN)


async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send(update, "🔄 *Cache actualisé!*", parse_mode=ParseMode.MARKDOWN)


# ============ 💎 SERVEURS ============

async def servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_servers = db.get_all_servers()

    if not all_servers:
        await send(update, "❌ Aucun serveur en base. Faites /check d'abord!")
        return

    udp = [s for s in all_servers if s["type"] == "udp"]
    dnstt = [s for s in all_servers if s["type"] == "dnstt"]

    text = "🖥️ *TOUS LES SERVEURS*\n\n"

    if udp:
        text += "🟠 *UDP Custom:*\n"
        for s in udp:
            emoji = "🟢" if s["status"] == "Online" else "🔴"
            text += f"  {emoji} {s['country'].title()}: {s['remaining']} slots\n"
        text += "\n"

    if dnstt:
        text += "🟢 *DNSTT (SlowDNS):*\n"
        for s in dnstt:
            emoji = "🟢" if s["status"] == "Online" else "🔴"
            text += f"  {emoji} {s['country'].title()}: {s['remaining']} slots\n"

    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    servers = db.get_servers_by_status("Online")

    if not servers:
        await send(update, "🔴 Aucun serveur en ligne actuellement")
        return

    text = f"🟢 *SERVEURS EN LIGNE* ({len(servers)})\n\n"

    for s in servers:
        text += f"{flag(s['country'])} *{s['country'].title()}* ({s['type'].upper()})\n"
        text += f"   Host: `{s['host']}`\n"
        text += f"   🎫 {s['remaining']} slots disponibles\n\n"

    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def offline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    servers = db.get_servers_by_status("Offline")

    if not servers:
        await send(update, "🟢 Tous les serveurs sont en ligne!")
        return

    text = f"🔴 *SERVEURS HORS LIGNE* ({len(servers)})\n\n"

    for s in servers:
        text += f"{flag(s['country'])} {s['country'].title()} ({s['type'].upper()})\n"

    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def udp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    servers = db.get_servers_by_type("udp")
    text = "🟠 *SERVEURS UDP CUSTOM*\n\n"

    if not servers:
        text += "Aucun serveur trouvé."
        await send(update, text, parse_mode=ParseMode.MARKDOWN)
        return

    for s in servers:
        emoji = "🟢" if s["status"] == "Online" else "🔴"
        text += f"{emoji} {flag(s['country'])} {s['country'].title()}\n"
        text += f"   `{s['host']}`\n"
        text += f"   🎫 {s['remaining']} slots\n\n"

    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def dnstt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    servers = db.get_servers_by_type("dnstt")
    text = "🟢 *SERVEURS DNSTT (SlowDNS)*\n\n"

    if not servers:
        text += "Aucun serveur trouvé."
        await send(update, text, parse_mode=ParseMode.MARKDOWN)
        return

    for s in servers:
        emoji = "🟢" if s["status"] == "Online" else "🔴"
        text += f"{emoji} {flag(s['country'])} {s['country'].title()}\n"
        text += f"   `{s['host']}`\n"
        text += f"   🎫 {s['remaining']} slots\n\n"

    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_servers = db.get_all_servers()

    countries = {}
    for s in all_servers:
        countries.setdefault(s["country"], []).append(s)

    text = "🌍 *SERVEURS PAR PAYS*\n\n"

    for country_name, servers_list in sorted(countries.items()):
        online_count = len([s for s in servers_list if s["status"] == "Online"])
        text += f"{flag(country_name)} {country_name.title()}: {online_count}/{len(servers_list)} en ligne\n"

    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await send(update, "❌ Usage: `/search germany`", parse_mode=ParseMode.MARKDOWN)
        return

    term = " ".join(context.args).lower()
    results = db.search_servers(term)

    if not results:
        await send(update, f"🔍 Aucun résultat pour '{term}'")
        return

    text = f"🔍 *Résultats pour '{term}'*\n\n"

    for r in results:
        emoji = "🟢" if r["status"] == "Online" else "🔴"
        text += f"{emoji} {r['country'].title()} ({r['type'].upper()})\n"
        text += f"   `{r['host']}`\n\n"

    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await send(update, "❌ Usage: `/host de1.ssht.site`", parse_mode=ParseMode.MARKDOWN)
        return

    hostname = " ".join(context.args).lower()
    results = db.search_servers(hostname)

    if not results:
        await send(update, f"🔍 Host '{hostname}' non trouvé")
        return

    r = results[0]
    text = f"""
🖥️ *INFORMATIONS HOST*

Host: `{r['host']}`
Pays: {r['country'].title()}
Type: {r['type'].upper()}
Status: {'🟢 Online' if r['status'] == 'Online' else '🔴 Offline'}
"""
    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await send(update, "❌ Usage: `/info france`", parse_mode=ParseMode.MARKDOWN)
        return

    country_name = " ".join(context.args).lower()
    server = db.get_server_by_country(country_name)

    if not server:
        live_server = scraper.check_single_country(country_name)
        if live_server:
            text = f"""
{flag(live_server.country)} *{live_server.country.upper()}* (LIVE)

🖥️ Host: `{live_server.host}`
🔌 Protocol: {live_server.protocol}
🔢 Port: {live_server.ssh_port}
⏱️ Validité: {live_server.validity}

📊 Status: {'🟢 Online' if live_server.status == 'Online' else '🔴 Offline'}
🎫 Slots: {live_server.accounts_remaining} disponibles
"""
        else:
            await send(update, f"❌ Pays '{country_name}' non trouvé")
            return
    else:
        text = f"""
{flag(server['country'])} *{server['country'].upper()}*

🖥️ Host: `{server['host']}`
🔌 Protocol: {server['protocol']}
📊 Status: {'🟢 Online' if server['status'] == 'Online' else '🔴 Offline'}
🎫 Slots: {server['remaining']} disponibles

📅 Premier scan: {server['first_seen'][:10]}
🔄 Dernier check: {server['last_check'][:10]}
"""
    await send(update, text, parse_mode=ParseMode.MARKDOWN)


# ============ 🌟 SYSTÈME ============

async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alerts_list = db.get_recent_alerts(10)

    if not alerts_list:
        await send(update, "📭 Aucune alerte récente")
        return

    text = "🔔 *DERNIÈRES ALERTES*\n\n"

    for a in alerts_list:
        emoji = {"new": "✨", "online": "🟢", "slots": "🎫"}.get(a["type"], "📌")
        text += f"{emoji} *{a['type'].upper()}*\n"
        text += f"   {a['country'].title()} — {a['time'][11:16]}\n"
        text += f"   _{a['message'][:50]}..._\n\n"

    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    message = await send(update, "🏓 *Ping...*", parse_mode=ParseMode.MARKDOWN)
    end = time.time()
    latency = round((end - start) * 1000)

    if message:
        await message.edit_text(f"🏓 *Pong!*\n\nLatence: `{latency}ms`", parse_mode=ParseMode.MARKDOWN)
    else:
        await send(update, f"🏓 *Pong!*\n\nLatence: `{latency}ms`", parse_mode=ParseMode.MARKDOWN)


async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    delta = now - config.START_TIME

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    text = f"""
⏱️ *UPTIME*

🤖 En ligne depuis:
{days} jours, {hours}h {minutes}m {seconds}s

🚀 Démarré: {config.START_TIME.strftime('%d/%m/%Y %H:%M:%S')}
"""
    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
📦 *VERSION*

🤖 {config.BOT_NAME}
🔢 Version: {config.VERSION}
👑 Créateur: {config.CREATOR}

🐍 Python 3.11
📚 python-telegram-bot 20.7
🔍 CloudScraper 1.2.71
"""
    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
💎 *À PROPOS*

🤖 *{config.BOT_NAME}*
Surveillance automatique des serveurs SSHOcean

👑 Créé avec passion par {config.CREATOR}

🎯 Fonctionnalités:
• Scan automatique toutes les 5 minutes
• Détection nouveaux serveurs
• Alertes instantanées Telegram
• Support UDP & DNSTT
• Serveurs suivis par pays

📡 Technologies:
Python • Telegram Bot • Render • SQLite
"""
    await send(update, text, parse_mode=ParseMode.MARKDOWN)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "status":
        await status(update, context)
    elif query.data == "check":
        await check(update, context)
    elif query.data == "servers":
        await servers(update, context)
    elif query.data == "help":
        await help_command(update, context)
