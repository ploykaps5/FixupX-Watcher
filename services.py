"""
Определения сервисов: домены, замены, категории, примеры.
Пользователь видит в GUI только name / description / пример.
"""

SERVICES = {
    # ---------------- Соцсети ----------------
    "x_twitter": {
        "name": "X (Twitter)",
        "description": "Ссылки на твиты и профили. Заменяет x.com и twitter.com на fixupx.com.",
        "category": "social",
        "domains": ["x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"],
        "replacement": "fixupx.com",
        "utm_clean": False,
        "example_from": "https://fixupx.com/user/status/1234567890?s=20",
        "example_to": "https://fixupx.com/user/status/1234567890?s=20",
        "enabled_by_default": True,
    },
    "bluesky": {
        "name": "Bluesky",
        "description": "Ссылки на посты. Заменяет bsky.app на fxbsky.app.",
        "category": "social",
        "domains": ["bsky.app"],
        "replacement": "fxbsky.app",
        "utm_clean": False,
        "example_from": "https://fxbsky.app/profile/user/post/abc",
        "example_to": "https://fxbsky.app/profile/user/post/abc",
        "enabled_by_default": True,
    },
    "instagram": {
        "name": "Instagram",
        "description": "Посты и reels. Заменяет instagram.com на ddinstagram.com, убирает igsh.",
        "category": "social",
        "domains": ["instagram.com", "www.instagram.com"],
        "replacement": "ddinstagram.com",
        "utm_clean": True,
        "example_from": "https://ddinstagram.com/p/ABC123/?igsh=xyz",
        "example_to": "https://ddinstagram.com/p/ABC123/",
        "enabled_by_default": True,
    },
    "tiktok": {
        "name": "TikTok",
        "description": "Видео. Заменяет tiktok.com на vxtiktok.com.",
        "category": "social",
        "domains": ["tiktok.com", "www.tiktok.com", "vm.tiktok.com"],
        "replacement": "vxtiktok.com",
        "utm_clean": True,
        "example_from": "https://www.tiktok.com/@user/video/123?_t=xyz",
        "example_to": "https://vxtiktok.com/@user/video/123",
        "enabled_by_default": True,
    },
    "reddit": {
        "name": "Reddit",
        "description": "Посты. Заменяет reddit.com на rxddit.com.",
        "category": "social",
        "domains": ["reddit.com", "www.reddit.com", "old.reddit.com", "redd.it"],
        "replacement": "rxddit.com",
        "utm_clean": True,
        "example_from": "https://rxddit.com/r/sub/comments/abc/?share_id=xyz",
        "example_to": "https://rxddit.com/r/sub/comments/abc/",
        "enabled_by_default": True,
    },
    "facebook": {
        "name": "Facebook",
        "description": "Посты. Заменяет facebook.com на facebookez.com.",
        "category": "social",
        "domains": ["facebook.com", "www.facebook.com", "m.facebook.com", "fb.watch"],
        "replacement": "facebookez.com",
        "utm_clean": True,
        "example_from": "https://facebookez.com/user/posts/123?mibextid=abc",
        "example_to": "https://facebookez.com/user/posts/123",
        "enabled_by_default": True,
    },
    "linkedin": {
        "name": "LinkedIn",
        "description": "Посты и профили. Убирает trk-параметры.",
        "category": "social",
        "domains": ["linkedin.com", "www.linkedin.com"],
        "replacement": None,
        "utm_clean": True,
        "example_from": "https://www.linkedin.com/posts/user_123?trk=public",
        "example_to": "https://www.linkedin.com/posts/user_123",
        "enabled_by_default": True,
    },
    # ---------------- Видео ----------------
    "youtube": {
        "name": "YouTube",
        "description": "Видео. Убирает si и прочие параметры трекинга.",
        "category": "video",
        "domains": ["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com", "music.youtube.com"],
        "replacement": None,
        "utm_clean": True,
        "example_from": "https://youtu.be/dQw4w9WgXcQ?si=abc123&feature=share",
        "example_to": "https://youtu.be/dQw4w9WgXcQ",
        "enabled_by_default": True,
    },
    "bilibili": {
        "name": "Bilibili",
        "description": "Видео. Убирает share_source, spm_id_from и т.п.",
        "category": "video",
        "domains": ["bilibili.com", "www.bilibili.com"],
        "replacement": None,
        "utm_clean": True,
        "example_from": "https://www.bilibili.com/video/BV1xx?spm_id_from=333",
        "example_to": "https://www.bilibili.com/video/BV1xx",
        "enabled_by_default": True,
    },
    # ---------------- Магазины ----------------
    "amazon": {
        "name": "Amazon",
        "description": "Товары. Убирает партнёрский тег и реферальные параметры.",
        "category": "shop",
        "domains": ["amazon.com", "www.amazon.com", "amzn.to", "amzn.eu"],
        "replacement": None,
        "utm_clean": True,
        "example_from": "https://www.amazon.com/dp/B0XXXXX?tag=aff-20&ref_=xyz",
        "example_to": "https://www.amazon.com/dp/B0XXXXX",
        "enabled_by_default": True,
    },
    # ---------------- Поиск и карты ----------------
    "google_search": {
        "name": "Google Search",
        "description": "Поисковые запросы. Убирает sourceid, gws_rd, ei и подобное.",
        "category": "search",
        "domains": ["google.com/search", "www.google.com/search"],
        "replacement": None,
        "utm_clean": True,
        "example_from": "https://www.google.com/search?q=python&sourceid=chrome&ie=UTF-8",
        "example_to": "https://www.google.com/search?q=python",
        "enabled_by_default": False,
    },
    "google_maps": {
        "name": "Google Maps",
        "description": "Ссылки на карты. Убирает entry, g_ep.",
        "category": "search",
        "domains": ["google.com/maps", "maps.google.com", "www.google.com/maps"],
        "replacement": None,
        "utm_clean": True,
        "example_from": "https://maps.google.com/?q=55.75,37.61&entry=yt",
        "example_to": "https://maps.google.com/?q=55.75,37.61",
        "enabled_by_default": False,
    },
    # ---------------- Музыка ----------------
    "spotify": {
        "name": "Spotify",
        "description": "Треки и плейлисты. Убирает si.",
        "category": "music",
        "domains": ["spotify.com", "open.spotify.com"],
        "replacement": None,
        "utm_clean": True,
        "example_from": "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT?si=abc",
        "example_to": "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT",
        "enabled_by_default": True,
    },
    # ---------------- Статьи ----------------
    "wikipedia": {
        "name": "Wikipedia",
        "description": "Статьи. Убирает wprov.",
        "category": "reference",
        "domains": ["wikipedia.org", "en.wikipedia.org", "ru.wikipedia.org"],
        "replacement": None,
        "utm_clean": True,
        "example_from": "https://en.wikipedia.org/wiki/Python?wprov=sfla1",
        "example_to": "https://en.wikipedia.org/wiki/Python",
        "enabled_by_default": True,
    },
    "the_guardian": {
        "name": "The Guardian",
        "description": "Статьи. Убирает CMP и реферальные метки.",
        "category": "news",
        "domains": ["theguardian.com", "www.theguardian.com"],
        "replacement": None,
        "utm_clean": True,
        "example_from": "https://www.theguardian.com/world/2025/x?CMP=share_btn_tw",
        "example_to": "https://www.theguardian.com/world/2025/x",
        "enabled_by_default": True,
    },
    "nytimes": {
        "name": "The New York Times",
        "description": "Статьи. Убирает smid и партнёрские метки.",
        "category": "news",
        "domains": ["nytimes.com", "www.nytimes.com"],
        "replacement": None,
        "utm_clean": True,
        "example_from": "https://www.nytimes.com/2025/x.html?smid=tw-share",
        "example_to": "https://www.nytimes.com/2025/x.html",
        "enabled_by_default": True,
    },
}


# Пресеты для кнопок в окне настроек
PRESETS = {
    "only_x": {
        "label": "Только X",
        "services": ["x_twitter"],
    },
    "social": {
        "label": "Соцсети",
        "services": ["x_twitter", "bluesky", "instagram", "tiktok",
                     "facebook", "reddit", "linkedin"],
    },
    "media_news": {
        "label": "Видео и новости",
        "services": ["youtube", "bilibili", "the_guardian", "nytimes", "wikipedia"],
    },
    "all": {
        "label": "Всё включить",
        "services": list(SERVICES.keys()),
    },
    "none": {
        "label": "Всё выключить",
        "services": [],
    },
}


def get_service(key: str) -> dict:
    return SERVICES.get(key, {})


def all_service_keys():
    return list(SERVICES.keys())