"""
Пользовательские правила.

Хранятся в config.json:
  "custom_rules": {
      "domain_replace": { "nitter.net": "twitter.com", "old.reddit.com": "reddit.com" },
      "param_strip":    { "example.com": ["track", "session"], "*.news.com": ["ref"] }
  }

Правила param_strip работают поверх встроенных: применяются ДО замены доменов.
Поддерживаются маски: "*.site.com" — все поддомены, "site.*" — все TLD.
"""

import re
import urllib.parse


URL_RE = re.compile(r'https?://[^\s<>"\')]+')


def build_domain_replace_rules(custom_rules):
    """Список (compiled_pattern, replacement) для замены доменов."""
    rules = []
    for from_d, to_d in (custom_rules.get("domain_replace") or {}).items():
        if not from_d or not to_d:
            continue
        pat = re.compile(
            r'(?<![\w.-])' + re.escape(from_d.strip()) + r'(?=/|$|\?)',
            re.IGNORECASE,
        )
        rules.append((pat, to_d.strip()))
    return rules


def build_param_strip_rules(custom_rules):
    """{host_pattern_lower: set(params_lower)}."""
    result = {}
    for host, params in (custom_rules.get("param_strip") or {}).items():
        if not host or not params:
            continue
        result[host.lower().strip()] = {p.lower().strip() for p in params if p and p.strip()}
    return result


def _host_matches(host, pattern):
    host = host.lower()
    pattern = pattern.lower()
    if pattern.startswith("*."):
        suffix = pattern[1:]         # ".site.com"
        return host.endswith(suffix) or host == pattern[2:]
    if pattern.endswith(".*"):
        return host.startswith(pattern[:-1])
    return host == pattern or host.endswith("." + pattern)


def apply_param_strip(text, param_rules):
    if not text or not param_rules:
        return text

    def repl(m):
        url = m.group(0)
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception:
            return url
        if not parsed.query:
            return url
        host = parsed.netloc.lower().split(":")[0]
        strip = set()
        for pattern, params in param_rules.items():
            if _host_matches(host, pattern):
                strip |= params
        if not strip:
            return url
        qs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        kept = [(k, v) for k, v in qs if k.lower() not in strip]
        if len(kept) == len(qs):
            return url
        return urllib.parse.urlunparse(
            parsed._replace(query=urllib.parse.urlencode(kept))
        )

    return URL_RE.sub(repl, text)


def validate_domain_replace(rules):
    errors = []
    for from_d, to_d in (rules or {}).items():
        if not from_d or not str(from_d).strip():
            errors.append("Пустой исходный домен")
            continue
        if not to_d or not str(to_d).strip():
            errors.append(f"{from_d}: пустой целевой домен")
        if " " in str(from_d) or " " in str(to_d):
            errors.append(f"{from_d} → {to_d}: пробелы в домене")
    return errors


def validate_param_strip(rules):
    errors = []
    for host, params in (rules or {}).items():
        if not host or not str(host).strip():
            errors.append("Пустой хост в param_strip")
        if not isinstance(params, list) or not params:
            errors.append(f"{host}: пустой список параметров")
    return errors