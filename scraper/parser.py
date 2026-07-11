import cloudscraper
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ServerInfo:
    country: str
    server_type: str
    host: str
    protocol: str
    ssh_port: str
    validity: str
    status: str
    accounts_remaining: int
    url: str

class SSHOceanScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def fetch_page(self, url: str) -> Optional[str]:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://sshocean.com/",
                "Connection": "keep-alive",
            }

            response = self.scraper.get(url, headers=headers, timeout=30)
            print(f"[FETCH] {url} -> {response.status_code} | {len(response.text)} chars")

            if response.status_code != 200:
                print(response.text[:300])
                return None

            return response.text
        except Exception as e:
            print(f"Erreur fetch {url}: {e}")
            return None

    def parse_server_card(self, html: str, country: str, server_type: str, url: str) -> Optional[ServerInfo]:
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Host
        host_match = re.search(r'[a-z0-9]+\.ssht\.site', html)
        host = host_match.group() if host_match else 'unknown'

        # Status
        status = 'Online' if 'online' in html.lower() and soup.find(text=re.compile(r'online', re.I)) else 'Offline'

        # Accounts
        remaining = 0
        match = re.search(r'(\d+)\s*Remaining', html, re.I)
        if match:
            remaining = int(match.group(1))

        return ServerInfo(
            country=country,
            server_type=server_type,
            host=host,
            protocol='UDP' if 'udp' in url else 'DNS',
            ssh_port='1:65535',
            validity='7 days',
            status=status,
            accounts_remaining=remaining,
            url=url
        )

    def check_all_servers(self) -> List[ServerInfo]:
        from config import UDP_SERVERS, DNSTT_SERVERS

        all_servers = []

        for country, url in UDP_SERVERS.items():
            html = self.fetch_page(url)
            server = self.parse_server_card(html, country, 'udp', url)
            if server:
                all_servers.append(server)

        for country, url in DNSTT_SERVERS.items():
            html = self.fetch_page(url)
            server = self.parse_server_card(html, country, 'dnstt', url)
            if server:
                all_servers.append(server)

        return all_servers

    def check_single_country(self, country: str) -> Optional[ServerInfo]:
        from config import UDP_SERVERS, DNSTT_SERVERS

        # Check UDP first
        if country in UDP_SERVERS:
            html = self.fetch_page(UDP_SERVERS[country])
            return self.parse_server_card(html, country, 'udp', UDP_SERVERS[country])

        # Check DNSTT
        if country in DNSTT_SERVERS:
            html = self.fetch_page(DNSTT_SERVERS[country])
            return self.parse_server_card(html, country, 'dnstt', DNSTT_SERVERS[country])

        return None
