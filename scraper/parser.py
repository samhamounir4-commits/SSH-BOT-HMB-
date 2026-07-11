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
            response = self.scraper.get(url, timeout=30)
            return response.text if response.status_code == 200 else None
        except Exception as e:
            print(f"Erreur: {e}")
            return None

    @staticmethod
    def _extract_host(html: str) -> str:
        host_match = re.search(r"([a-z0-9.-]+\.ssht\.site)", html, re.I)
        return host_match.group(1).lower() if host_match else "unknown"

    @staticmethod
    def _extract_status(html: str, soup: BeautifulSoup) -> str:
        visible_text = soup.get_text(" ", strip=True).lower()
        if re.search(r"\bonline\b", visible_text):
            return "Online"
        if re.search(r"\boffline\b", visible_text):
            return "Offline"
        return "Offline"

    @staticmethod
    def _extract_remaining(html: str) -> int:
        patterns = [
            r"(\d+)\s*Remaining",
            r"(\d+)\s*remaining",
            r"(\d+)\s*accounts?\s*remaining",
            r"(\d+)\s*slots?\s*remaining",
            r"(\d+)\s*Available",
            r"(\d+)\s*available",
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                return int(match.group(1))
        return 0

    @staticmethod
    def _extract_ssh_port(html: str) -> str:
        patterns = [
            r"SSH\s*Port[:\s]+([0-9]{1,5})",
            r"Port[:\s]+([0-9]{1,5})",
            r"Port\s*([0-9]{1,5})",
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                return match.group(1)
        return "unknown"

    @staticmethod
    def _extract_validity(html: str) -> str:
        patterns = [
            r"Validity[:\s]+([^\n<]+)",
            r"Exp[:\s]+([^\n<]+)",
            r"Expires?[:\s]+([^\n<]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                return match.group(1).strip()
        return "unknown"

    def parse_server_card(self, html: str, country: str, server_type: str, url: str) -> Optional[ServerInfo]:
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        host = self._extract_host(html)
        status = self._extract_status(html, soup)
        remaining = self._extract_remaining(html)
        ssh_port = self._extract_ssh_port(html)
        validity = self._extract_validity(html)

        return ServerInfo(
            country=country,
            server_type=server_type,
            host=host,
            protocol="UDP" if "udp" in url else "DNS",
            ssh_port=ssh_port,
            validity=validity,
            status=status,
            accounts_remaining=remaining,
            url=url,
        )

    def check_all_servers(self) -> List[ServerInfo]:
        from config import UDP_SERVERS, DNSTT_SERVERS

        all_servers = []

        for country, url in UDP_SERVERS.items():
            html = self.fetch_page(url)
            server = self.parse_server_card(html, country, "udp", url)
            if server:
                all_servers.append(server)

        for country, url in DNSTT_SERVERS.items():
            html = self.fetch_page(url)
            server = self.parse_server_card(html, country, "dnstt", url)
            if server:
                all_servers.append(server)

        return all_servers

    def check_single_country(self, country: str) -> Optional[ServerInfo]:
        from config import UDP_SERVERS, DNSTT_SERVERS

        country = country.strip().lower()

        if country in UDP_SERVERS:
            html = self.fetch_page(UDP_SERVERS[country])
            return self.parse_server_card(html, country, "udp", UDP_SERVERS[country])

        if country in DNSTT_SERVERS:
            html = self.fetch_page(DNSTT_SERVERS[country])
            return self.parse_server_card(html, country, "dnstt", DNSTT_SERVERS[country])

        return None
