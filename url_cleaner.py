"""
Очистка URL от параметров трекинга.
"""

import re
import urllib.parse

URL_RE = re.compile(r'https?://[^\s<>"\')]+')

# Глобальные параметры, которые можно смело удалять у любого сервиса
GLOBAL_TRACKING = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_name", "utm_reader",
    "fbclid", "gclid", "dclid", "gclsrc", "wbraid", "gbraid",
    "mc_cid", "mc_eid", "_ga", "_gl", "yclid", "msclkid",
    "igshid", "twclid", "ttclid", "li_fat_id", "epik",
    "ref_src", "ref_url",
}

# Специфичные для сервисов (в нижнем регистре).
# Параметры, оканчивающиеся на "_", означают префикс (pf_rd_*).
SERVICE_TRACKING = {
    "youtube":      {"si", "feature", "pp", "ab_channel"},
    "spotify":      {"si", "context"},
    "amazon":       {"tag", "ref_", "ref", "pf_rd_", "psc", "th",
                     "linkcode", "language", "content-id", "ascsubtag",
                     "smid", "_encoding", "keywords"},
    "nytimes":      {"smid", "partner", "rref", "module", "pgtype"},
    "the_guardian": {"cmp", "intcmp", "ref"},
    "bilibili":     {"share_source", "share_medium", "share_plat",
                     "share_tag", "spm_id_from", "vd_source", "from_source",
                     "unique_k"},
    "linkedin":     {"trk", "trkinfo", "lipi", "midtoken", "midsig",
                     "trackingid", "original_referer"},
    "reddit":       {"share_id", "context", "correlation_id", "ref"},
    "tiktok":       {"_t", "is_from_webapp", "sender_device", "web_id"},
    "instagram":    {"igsh", "img_index"},
    "facebook":     {"mibextid", "rdid", "share_url", "paipv", "eav"},
    "google_search": {"sourceid", "ie", "uact", "oq", "aqs", "gws_rd",
                      "ei", "ved", "usta", "usg", "sa", "sclient",
                      "biw", "bih"},
    "google_maps":  {"entry", "g_ep", "hl", "source"},
    "wikipedia":    {"wprov"},
}


def _should_strip(key: str, params: set) -> bool:
    k = key.lower()
    if k in params:
        return True
    for p in params:
        if p.endswith("_") and k.startswith(p):
            return True
    return False


def _clean_one(url: str, params: set) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return url
    if not parsed.query:
        return url
    qs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    kept = [(k, v) for k, v in qs if not _should_strip(k, params)]
    new_query = urllib.parse.urlencode(kept)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def _match_service(url: str, service_domains: dict):
    """Определяет, к какому сервису относится URL."""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return None
    host = parsed.netloc.lower().split(":")[0]
    path = parsed.path or ""
    for key, domains in service_domains.items():
        for d in domains:
            d = d.lower()
            if "/" in d:
                d_host, d_path = d.split("/", 1)
                d_path = "/" + d_path
                if (host == d_host or host.endswith("." + d_host)) and d_path in path:
                    return key
            else:
                if host == d or host.endswith("." + d):
                    return key
    return None


def clean_urls_in_text(text: str, service_domains: dict) -> str:
    """
    service_domains: {service_key: [domains]} — только для сервисов с включённой очисткой.
    """
    if not text:
        return text

    def repl(m):
        url = m.group(0)
        key = _match_service(url, service_domains)
        params = set(GLOBAL_TRACKING)
        if key:
            params |= SERVICE_TRACKING.get(key, set())
        return _clean_one(url, params)

    return URL_RE.sub(repl, text)


def preview_clean(url: str, service_domains: dict) -> str:
    """Для тест-строки: обработать одну ссылку (или целую строку)."""
    return clean_urls_in_text(url, service_domains)