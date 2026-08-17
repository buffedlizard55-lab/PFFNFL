"""
PFFScraper base class - optimized for reverse engineering profootballfocus.com

Features:
- Aggressive caching (critical for RE work)
- __NEXT_DATA__ extraction (often contains the real structured data)
- Easy sample saving/loading for offline development
- Rate limiting + graceful fallbacks
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.pff.com/",
}

CACHE_DIR = Path("data/raw")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SAMPLES_DIR = Path("data/samples")
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


class PFFScraper:
    def __init__(
        self,
        base_url: str = "https://www.pff.com",
        cache_enabled: bool = True,
        rate_limit: float = 1.8,
        timeout: int = 25,
    ):
        self.base_url = base_url.rstrip("/")
        self.cache_enabled = cache_enabled
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.last_request_time = 0.0

        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

        retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    def _cache_path(self, url: str) -> Path:
        h = hashlib.sha256(url.encode()).hexdigest()[:16]
        safe = url.replace("https://", "").replace("/", "_")[:70]
        return CACHE_DIR / f"{safe}_{h}.html"

    def get(self, url: str, force_refresh: bool = False) -> str:
        cache_path = self._cache_path(url)

        if self.cache_enabled and not force_refresh and cache_path.exists():
            console.log(f"[dim]CACHE HIT[/dim] {url}")
            return cache_path.read_text(encoding="utf-8", errors="ignore")

        self._rate_limit()
        console.log(f"[cyan]FETCH[/cyan] {url}")

        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            console.log(f"[red]FAILED[/red] {url} → {e}")
            if cache_path.exists():
                return cache_path.read_text(encoding="utf-8", errors="ignore")
            return ""

        if self.cache_enabled:
            cache_path.write_text(html, encoding="utf-8")
            (cache_path.with_suffix(".meta.json")).write_text(
                json.dumps({"url": url, "cached_at": time.time()}, indent=2)
            )

        return html

    def parse_next_data(self, html: str) -> Optional[Dict[str, Any]]:
        """Extract __NEXT_DATA__ — this is gold for reverse engineering PFF."""
        soup = BeautifulSoup(html, "lxml")
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                return json.loads(script.string)
            except Exception:
                pass
        return None

    def save_sample(self, name: str, html: str):
        path = SAMPLES_DIR / f"{name}.html"
        path.write_text(html, encoding="utf-8")
        console.log(f"[green]Saved sample[/green] {path}")

    def load_sample(self, name: str) -> str:
        path = SAMPLES_DIR / f"{name}.html"
        if path.exists():
            return path.read_text(encoding="utf-8")
        raise FileNotFoundError(name)

    def close(self):
        self.session.close()
