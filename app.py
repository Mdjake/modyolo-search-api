import re
import random
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse as uparse
import json

BASE = "https://modyolo.com"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Linux; Android 13; Pixel 7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Mobile Safari/537.36"),
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "image/avif,image/webp,*/*;q=0.8"),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE + "/",
}
APP_RE = re.compile(r"^/[a-z0-9][a-z0-9\-]*\.html$", re.I)
TITLE_RE = re.compile(
    r"^(.+?)\s+(\d+(?:\.\d+)+[a-zA-Z]?)\s*\+?\s*(\d+(?:\.\d+)?\s*M?B?)?.*$", re.I
)


def search(query: str):
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get(BASE + "/", timeout=15)
    time.sleep(random.uniform(0.5, 1.2))
    url = f"{BASE}/?s={query}"
    r = s.get(url, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "img", "noscript", "iframe", "svg"]):
        tag.decompose()

    seen, out = set(), []
    for a in soup.find_all("a", href=True):
        full = urljoin(BASE, a["href"].strip())
        p = urlparse(full)
        if "modyolo.com" not in p.netloc or not APP_RE.match(p.path):
            continue
        if full in seen:
            continue
        seen.add(full)
        raw = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
        m = TITLE_RE.match(raw)
        if m:
            size = (m.group(3) or "").strip()
            title = f"{m.group(1)} {m.group(2)}" + (f" + {size}" if size else "")
        else:
            title = raw
        out.append({"title": title, "url": full})
    return out


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(uparse(self.path).query)
        query = (params.get("q", ["Whatsapp"])[0] or "Whatsapp").strip()
        try:
            data = search(query)
            body = json.dumps({"query": query, "count": len(data), "results": data})
            status = 200
        except Exception as e:
            body = json.dumps({"error": str(e)})
            status = 500

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
