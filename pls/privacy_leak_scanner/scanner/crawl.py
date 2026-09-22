from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import time

DOC_EXTS = {".pdf", ".xlsx", ".xlsm", ".csv"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
SUPPORTED_EXTS = DOC_EXTS | IMAGE_EXTS


def local_discover(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            yield p


def http_discover(base_url: str, max_pages=100, delay=0.25):
    parsed = urlparse(base_url)
    host = parsed.netloc
    seen = set()
    queue = [base_url]
    for _ in range(max_pages):
        if not queue:
            break
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        u = urlparse(url)
        if u.netloc != host:
            continue
        req = Request(url, headers={"User-Agent": "PrivacyLeakScanner/0.1 (authorized audit)"})
        try:
            with urlopen(req, timeout=10) as r:
                body = r.read()
                ctype = r.headers.get("Content-Type", "")
        except Exception:
            continue
        if any(url.lower().split("?")[0].endswith(ext) for ext in SUPPORTED_EXTS):
            yield ("remote", url, body, ctype)
        elif "text/html" in ctype:
            soup = BeautifulSoup(body, "html.parser")
            for a in soup.find_all("a", href=True):
                nxt = a["href"]
                if nxt.startswith("/"):
                    nxt = f"{parsed.scheme}://{host}{nxt}"
                if nxt.startswith(("http://", "https://")) and urlparse(nxt).netloc == host:
                    queue.append(nxt)
        time.sleep(delay)
