import sqlite3
from datetime import datetime
from typing import List, Dict, Optional


class Database:
    def __init__(self, db_path: str = "servers.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._connect()
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS servers (
                host TEXT PRIMARY KEY,
                country TEXT,
                server_type TEXT,
                protocol TEXT,
                status TEXT,
                accounts_remaining INTEGER,
                first_seen TEXT,
                last_check TEXT,
                last_status_change TEXT,
                notified_online INTEGER DEFAULT 0,
                notified_available INTEGER DEFAULT 0,
                url TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT,
                country TEXT,
                alert_type TEXT,
                timestamp TEXT,
                message TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    @staticmethod
    def _row_to_server_dict(row) -> Dict:
        return {
            "host": row[0],
            "country": row[1],
            "type": row[2],
            "protocol": row[3],
            "status": row[4],
            "remaining": row[5],
            "first_seen": row[6],
            "last_check": row[7],
            "last_status_change": row[8],
            "notified_online": row[9],
            "notified_available": row[10],
            "url": row[11],
        }

    def update_server(self, server) -> Dict:
        conn = self._connect()
        c = conn.cursor()

        now = datetime.now().isoformat()
        changes = {
            "is_new": False,
            "went_online": False,
            "has_slots": False,
            "host": server.host,
        }

        c.execute(
            "SELECT status, accounts_remaining FROM servers WHERE host = ?",
            (server.host,),
        )
        existing = c.fetchone()

        if existing:
            old_status, old_remaining = existing

            if old_status != server.status:
                c.execute(
                    """
                    UPDATE servers
                    SET status=?, accounts_remaining=?, last_check=?, last_status_change=?
                    WHERE host=?
                    """,
                    (server.status, server.accounts_remaining, now, now, server.host),
                )
            else:
                c.execute(
                    """
                    UPDATE servers
                    SET accounts_remaining=?, last_check=?
                    WHERE host=?
                    """,
                    (server.accounts_remaining, now, server.host),
                )

            if old_status == "Offline" and server.status == "Online":
                changes["went_online"] = True
                self._add_alert(c, server, "online", f"Server {server.host} went online")

            if old_remaining == 0 and server.accounts_remaining > 0:
                changes["has_slots"] = True
                self._add_alert(c, server, "slots", f"Slots available on {server.host}")
        else:
            changes["is_new"] = True
            c.execute(
                """
                INSERT INTO servers (
                    host, country, server_type, protocol, status,
                    accounts_remaining, first_seen, last_check, last_status_change,
                    notified_online, notified_available, url
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    server.host,
                    server.country,
                    server.server_type,
                    server.protocol,
                    server.status,
                    server.accounts_remaining,
                    now,
                    now,
                    now,
                    0,
                    0,
                    server.url,
                ),
            )
            self._add_alert(c, server, "new", f"New server discovered: {server.host}")

        conn.commit()
        conn.close()
        return changes

    def _add_alert(self, cursor, server, alert_type: str, message: str):
        now = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO alerts (host, country, alert_type, timestamp, message)
            VALUES (?,?,?,?,?)
            """,
            (server.host, server.country, alert_type, now, message),
        )

    def get_all_servers(self) -> List[Dict]:
        conn = self._connect()
        c = conn.cursor()
        c.execute(
            """
            SELECT host, country, server_type, protocol, status, accounts_remaining,
                   first_seen, last_check, last_status_change, notified_online,
                   notified_available, url
            FROM servers
            ORDER BY server_type, country, host
            """
        )
        rows = c.fetchall()
        conn.close()
        return [self._row_to_server_dict(row) for row in rows]

    def get_servers_by_status(self, status: str) -> List[Dict]:
        conn = self._connect()
        c = conn.cursor()
        c.execute(
            """
            SELECT host, country, server_type, protocol, status, accounts_remaining,
                   first_seen, last_check, last_status_change, notified_online,
                   notified_available, url
            FROM servers
            WHERE status = ?
            ORDER BY server_type, country, host
            """,
            (status,),
        )
        rows = c.fetchall()
        conn.close()
        return [self._row_to_server_dict(row) for row in rows]

    def get_servers_by_type(self, server_type: str) -> List[Dict]:
        conn = self._connect()
        c = conn.cursor()
        c.execute(
            """
            SELECT host, country, server_type, protocol, status, accounts_remaining,
                   first_seen, last_check, last_status_change, notified_online,
                   notified_available, url
            FROM servers
            WHERE server_type = ?
            ORDER BY country, host
            """,
            (server_type,),
        )
        rows = c.fetchall()
        conn.close()
        return [self._row_to_server_dict(row) for row in rows]

    def get_server_by_country(self, country: str) -> Optional[Dict]:
        country = country.strip().lower()
        conn = self._connect()
        c = conn.cursor()
        c.execute(
            """
            SELECT host, country, server_type, protocol, status, accounts_remaining,
                   first_seen, last_check, last_status_change, notified_online,
                   notified_available, url
            FROM servers
            WHERE country = ?
            ORDER BY server_type, host
            LIMIT 1
            """,
            (country,),
        )
        row = c.fetchone()
        conn.close()
        return self._row_to_server_dict(row) if row else None

    def search_servers(self, term: str) -> List[Dict]:
        term = term.strip().lower()
        conn = self._connect()
        c = conn.cursor()
        c.execute(
            """
            SELECT host, country, server_type, protocol, status, accounts_remaining,
                   first_seen, last_check, last_status_change, notified_online,
                   notified_available, url
            FROM servers
            WHERE lower(host) LIKE ? OR lower(country) LIKE ? OR lower(server_type) LIKE ?
            ORDER BY server_type, country, host
            """,
            (f"%{term}%", f"%{term}%", f"%{term}%"),
        )
        rows = c.fetchall()
        conn.close()
        return [self._row_to_server_dict(row) for row in rows]

    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        conn = self._connect()
        c = conn.cursor()
        c.execute(
            """
            SELECT host, country, alert_type, timestamp, message
            FROM alerts
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "host": r[0],
                "country": r[1],
                "type": r[2],
                "time": r[3],
                "message": r[4],
            }
            for r in rows
        ]

    def get_stats(self) -> Dict:
        conn = self._connect()
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM servers WHERE status = 'Online'")
        online = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM servers WHERE status = 'Offline'")
        offline = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM servers WHERE server_type = 'udp'")
        udp_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM servers WHERE server_type = 'dnstt'")
        dnstt_count = c.fetchone()[0]

        c.execute("SELECT SUM(accounts_remaining) FROM servers")
        total_slots = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM alerts")
        total_alerts = c.fetchone()[0]

        conn.close()

        return {
            "online": online,
            "offline": offline,
            "udp": udp_count,
            "dnstt": dnstt_count,
            "total_slots": total_slots,
            "total_alerts": total_alerts,
            "total": online + offline,
        }

    def mark_notified(self, host: str, notification_type: str):
        conn = self._connect()
        c = conn.cursor()
        col = "notified_online" if notification_type == "online" else "notified_available"
        c.execute(f"UPDATE servers SET {col}=1 WHERE host=?", (host,))
        conn.commit()
        conn.close()
