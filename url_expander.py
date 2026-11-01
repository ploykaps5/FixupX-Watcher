"""
Разворачивание коротких ссылок и приведение мобильных к десктопным.
"""

import re
import logging
import urllib.parse

log = logging.getLogger("FixupX_Watcher")


URL_RE = re.compile(r'https?://[^\s<>"\')]+')


MOBILE_TO_DESKTOP = {
    "m.youtube.com":       "www.youtube.com",
    "m.facebook.com":      "www.facebook.com",
    "mobile.twitter.com":  "x.com",
    "m.twitter.com":       "x.com",
    "m.reddit.com":        "www.reddit.com",
    "amp.reddit.com":      "www.reddit.com",
    "m.instagram.com":     "www.instagram.com",
    "m.tiktok.com":        "www.tiktok.com",
    "amp.theguardian.com": "www.theguardian.com",
    "amp.nytimes.com":     "www.nytimes.com",
}


AMP_PATTERNS = [
    re.compile(r'^https?://(?:www\.)?google\.com/amp/s/(.+)$'),
    re.compile(r'^https?://(?:www\.)?google\.com/amp/(.+)$'),
    re.compile(r'^(https?://[^/]+)/amp/?$'),
    re.compile(r'^(https?://[^/]+)/amp/(.+)$'),
]


SHORT_URL_HOSTS = {
    "bit.ly", "t.co", "tinyurl.com", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "rebrand.ly", "cutt.ly", "shorte.st", "adf.ly",
    "bl.ink", "shorturl.at", "rb.gy", "tiny.cc", "soo.gd",
    "s2r.co", "clck.ru", "vk.cc", "u.to", "qps.ru",
    "trib.al", "dlvr.it", "ift.tt",
}


def normalize_mobile(url):
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return url
    host = parsed.netloc.lower()
    new_host = MOBILE_TO_DESKTOP.get(host)
    if not new_host and host.startswith("www."):
        new_host = MOBILE_TO_DESKTOP.get(host[4:])
    if new_host:
        return urllib.parse.urlunparse(parsed._replace(netloc=new_host))
    return url


def normalize_amp(url):
    for pat in AMP_PATTERNS:
        m = pat.match(url)
        if m:
            return pat.sub(
                lambda mm: mm.group(0)
                    .replace("/amp/s/", "/")
                    .replace("/amp/", "/")
                    .rstrip("/"),
                url,
            ).replace("google.com/amp/", "")
    # проще: руками
    if "google.com/amp/s/" in url:
        return url.replace("google.com/amp/s/", "").replace("https://www.", "https://", 1) \
            if url.startswith("https://www.google.com/amp/s/") else \
            url.replace("https://google.com/amp/s/", "https://", 1)
    if "google.com/amp/" in url:
        return url.replace("https://www.google.com/amp/", "https://", 1) \
            .replace("https://google.com/amp/", "https://", 1)
    # site.com/amp/ → site.com/
    m = re.match(r'^(https?://[^/]+)/amp/?$', url)
    if m:
        return m.group(1)
    m = re.match(r'^(https?://[^/]+)/amp/(.+)$', url)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return url


def _is_short(url):
    try:
        host = urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return False
    if host.startswith("www."):
        host = host[4:]
    return host in SHORT_URL_HOSTS


def _resolve_one(url, timeout=5):
    try:
        import requests
    except ImportError:
        log.info("requests не установлен — разворачивание недоступно")
        return None
    headers = {"User-Agent": "Mozilla/5.0 (compatible; FixupX-Watcher)"}
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout,
                          headers=headers)
        if r.url and r.url != url:
            return r.url
        r = requests.get(url, allow_redirects=True, timeout=timeout,
                         headers=headers, stream=True)
        return r.url if r.url != url else None
    except Exception as e:
        log.debug("Не удалось развернуть %s: %s", url, e)
        return None


def expand_urls_in_text(text, expand_short=False,
                        normalize_mobile_flag=True,
                        normalize_amp_flag=False,
                        resolver=_resolve_one):
    if not text:
        return text

    def repl(m):
        url = m.group(0)
        if normalize_mobile_flag:
            url = normalize_mobile(url)
        if normalize_amp_flag:
            url = normalize_amp(url)
        if expand_short and _is_short(url):
            resolved = resolver(url)
            if resolved:
                log.info("Развёрнуто: %s → %s", url, resolved)
                return resolved
        return url

    return URL_RE.sub(repl, text)