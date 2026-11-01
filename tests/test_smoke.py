"""
Базовые smoke-тесты. Запускаются в CI на Windows и Linux.

Цель — убедиться, что:
- весь пакет импортируется;
- platform_layer поднимает правильную платформу;
- чистка URL и нормализация доменов не сломаны.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_platform_layer_imports():
    import platform_layer
    assert platform_layer.PLATFORM in ("windows", "linux")


def test_url_cleaner_strips_global_tracking():
    from url_cleaner import clean_urls_in_text
    text = "https://example.com/x?utm_source=a&fbclid=b&keep=1"
    out = clean_urls_in_text(text, {})
    assert "utm_source" not in out
    assert "fbclid" not in out
    assert "keep=1" in out


def test_url_cleaner_service_params():
    from url_cleaner import clean_urls_in_text
    domains = {"youtube": ["youtube.com", "youtu.be"]}
    text = "https://youtu.be/abc?si=xyz&feature=share&t=10"
    out = clean_urls_in_text(text, domains)
    assert "si=" not in out
    assert "feature=" not in out
    assert "t=10" in out


def test_expander_mobile():
    from url_expander import normalize_mobile
    assert normalize_mobile("https://m.youtube.com/watch?v=1") == \
           "https://www.youtube.com/watch?v=1"
    assert normalize_mobile("https://mobile.twitter.com/u/status/1") == \
           "https://x.com/u/status/1"
    assert normalize_mobile("https://example.com/a") == "https://example.com/a"


def test_config_defaults_have_all_services():
    from config_manager import default_config
    from services import all_service_keys
    cfg = default_config()
    for key in all_service_keys():
        assert key in cfg["services"], f"missing service {key}"


def test_custom_rules_param_strip():
    from custom_rules import build_param_strip_rules, apply_param_strip
    rules = build_param_strip_rules({
        "param_strip": {"example.com": ["track", "session"]}
    })
    text = "https://example.com/x?track=1&session=2&ok=3"
    out = apply_param_strip(text, rules)
    assert "track=" not in out
    assert "session=" not in out
    assert "ok=3" in out