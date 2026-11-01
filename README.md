<h1 align="center">Fixup2X</h1>

<p align="center">
  <b>Автоматическая очистка и разворачивание ссылок в буфере обмена.</b><br>
  Заменяет ссылки на X/Twitter, Bluesky, Instagram, TikTok, Reddit, YouTube и другие
  на «чистые» и приватные альтернативы — прямо в момент копирования.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <img src="https://img.shields.io/badge/platforms-Windows%20%7C%20Linux-success" alt="Platforms">
  <a href="https://github.com/OWNER/Fixup2X/actions"><img src="https://github.com/OWNER/Fixup2X/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
</p>

<p align="center">
  <a href="#установка">Установка</a> ·
  <a href="#использование">Использование</a> ·
  <a href="#поддерживаемые-сервисы">Сервисы</a> ·
  <a href="#разработка">Разработка</a> ·
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

## Что это

Fixup2X — лёгкий фоновый трей-агент. Он следит за буфером обмена и **на лету**
переписывает ссылки:

- `x.com` / `twitter.com` → `fixupx.com` (встраиваемые превью в Discord, Telegram)
- `bsky.app` → `fxbsky.app`
- `instagram.com` → `ddinstagram.com`
- `tiktok.com` → `vxtiktok.com`
- `reddit.com` → `rxddit.com`
- `facebook.com` → `facebookez.com`
- YouTube, Amazon, LinkedIn, Spotify, Bilibili, Wikipedia, NYT, The Guardian —
  **удаляет UTM-метки и трекинг-параметры**, не меняя домен.

Дополнительно:

- разворачивает короткие ссылки (`bit.ly`, `t.co`, `tinyurl`, …);
- приводит мобильные URL к десктопным;
- убирает `amp.`-префиксы;
- умеет «свои правила» (своя замена домена, свои параметры для вырезания);
- не трогает буфер, если в нём есть картинки, файлы или OLE-данные;
- игнорирует выбранные приложения (менеджеры паролей, банковские клиенты);
- показывает уведомление с кнопкой **«Отменить»** (Windows);
- ведёт историю последних 50 замен;
- работает по горячей клавише (по требованию).

## Скриншоты

> Скриншоты кладутся в `docs/screenshots/` — см. [`docs/screenshots/README.md`](docs/screenshots/README.md).

| Настройки — Сервисы | Настройки — Тест | История замен |
|---|---|---|
| ![services](docs/screenshots/services.png) | ![test](docs/screenshots/test.png) | ![history](docs/screenshots/history.png) |

## Поддерживаемые сервисы

| Сервис | Замена домена | Очистка трекинга |
|---|:---:|:---:|
| X (Twitter) | `fixupx.com` | — |
| Bluesky | `fxbsky.app` | — |
| Instagram | `ddinstagram.com` | ✅ `igsh`, `img_index` |
| TikTok | `vxtiktok.com` | ✅ `_t`, `is_from_webapp`, … |
| Reddit | `rxddit.com` | ✅ `share_id`, `context`, … |
| Facebook | `facebookez.com` | ✅ `mibextid`, `rdid`, … |
| YouTube | — | ✅ `si`, `feature`, `pp` |
| Amazon | — | ✅ партнёрские `tag`, `ref_`, … |
| LinkedIn | — | ✅ `trk`, `lipi`, `midtoken` |
| Spotify | — | ✅ `si`, `context` |
| Bilibili | — | ✅ `share_source`, `spm_id_from`, … |
| Google Search / Maps | — | ✅ `sourceid`, `entry`, … |
| Wikipedia | — | ✅ `wprov` |
| The Guardian | — | ✅ `CMP`, `intcmp` |
| The New York Times | — | ✅ `smid`, `partner` |

Каждый сервис можно включить/выключить отдельно в настройках.

## Установка

### Windows (10/11)

**Готовый бинарник:**

1. Скачайте `fixup2x-windows.exe` из [Releases](https://github.com/OWNER/Fixup2X/releases).
2. Запустите. Появится иконка в системном трее.
3. Правый клик → «Настройки…» → выберите нужные сервисы.

**Из исходников:**

```powershell
git clone https://github.com/OWNER/Fixup2X.git
cd Fixup2X
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-windows.txt
python fixupx_watcher.py
```

Сборка exe:

```powershell
pyinstaller Fixup2X-windows.spec
# → dist/FixupX Watcher.exe
```

### Ubuntu / Debian / Kali

```bash
# системные зависимости
sudo apt update
sudo apt install -y \
    python3 python3-pip python3-tk \
    xclip xsel wl-clipboard \
    xdotool x11-utils \
    libnotify-bin \
    libgirepository1.0-dev gir1.2-appindicator3-0.1 libappindicator3-1 \
    python3-gi python3-gi-cairo

# репозиторий
git clone https://github.com/OWNER/Fixup2X.git
cd Fixup2X

# Python-зависимости
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-linux.txt

# запуск
python3 fixupx_watcher.py
```

Сборка бинарника:

```bash
pyinstaller Fixup2X-linux.spec
# → dist/fixupx-watcher
```

### Artix / Arch

```bash
sudo pacman -S --needed \
    python python-pip tk \
    xclip xsel wl-clipboard \
    xdotool xorg-xprop \
    libnotify libappindicator-gtk3 python-gobject

git clone https://github.com/OWNER/Fixup2X.git
cd Fixup2X
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-linux.txt
python fixupx_watcher.py
```

### Про Wayland

На Wayland работают: буфер обмена, трей, уведомления, история, настройки.
**Не работают** (отключаются автоматически, без падения):

- глобальная горячая клавиша (`pynput` не поддерживает Wayland);
- определение активного приложения для исключений.

Если нужны эти функции — используйте X11-сессию, либо запустите программу через `XWayland`:

```bash
GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb ./dist/fixupx-watcher
```

## Использование

### Трей-меню

- **Включить обработку ссылок** — глобальный переключатель;
- **Настройки…** — окно настроек (Сервисы / Общие / Разворачивание / Свои правила / Горячая клавиша / Исключения / Тест);
- **Автозагрузка при входе в Windows** (Windows) — запись в `HKCU\...\Run`, (Linux) — `~/.config/autostart/fixupx-watcher.desktop`;
- **История замен…** — последние 50 операций;
- **Открыть config.json / лог / папку с настройками** — для диагностики.

### Где хранятся файлы

| Windows | Linux |
|---|---|
| `%APPDATA%\FixupX Watcher\` | `$XDG_CONFIG_HOME/fixupx-watcher/` или `~/.config/fixupx-watcher/` |
| `config.json` | `config.json` |
| `history.json` | `history.json` |
| `undo_pending.json`, `undo_signal.json` | (аналогично) |
| `fixupx_watcher.log` | `fixupx_watcher.log` |

### Горячая клавиша (по требованию)

По умолчанию выключена. Включается в Настройки → Горячая клавиша.
Формат: `Ctrl+Shift+X` (Windows/Linux X11). Работает один раз — обрабатывает текущий буфер.

### Свои правила

`config.json`:

```json
"custom_rules": {
  "domain_replace": {
    "nitter.net": "x.com",
    "old.reddit.com": "reddit.com"
  },
  "param_strip": {
    "example.com": ["track", "session"],
    "*.news.com": ["ref"]
  }
}
```

Поддерживаются маски: `*.site.com` (все поддомены), `site.*` (любой TLD).

## Архитектура

Программа построена по принципу **«тонкое ядро + платформенный слой»**:

```
                ┌──────────────────────────────────┐
                │      fixupx_watcher.py           │
                │      (Watcher, tray, main)       │
                └───────────────┬──────────────────┘
                                │
                ┌───────────────▼──────────────────┐
                │         platform_layer/          │
                │  (автоопределение ОС на импорте) │
                └──┬──────────────────────────┬────┘
                   │                          │
        ┌──────────▼───────────┐   ┌──────────▼───────────┐
        │ platform_layer/      │   │ platform_layer/      │
        │    windows/          │   │    linux/            │
        │ clipboard, tray, …   │   │ clipboard, tray, …   │
        └──────────────────────┘   └──────────────────────┘
```

Бизнес-логика (`url_cleaner`, `url_expander`, `custom_rules`, `services`,
`history`, `config_manager`) **не знает о платформе**. Всё платформенно-зависимое
спрятано за единым фасадом `platform_layer`.

Подробнее — в [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Разработка

```bash
# линтер
pip install ruff
ruff check .

# тесты
pip install pytest
pytest -q

# форматирование
ruff format .
```

Перед PR прогоните `ruff check .` и `pytest -q` — CI проверит это же самое
на Windows и Linux.

## FAQ

**Q: Программа не видит ссылку — что делать?**
A: Ссылка должна быть **скопирована** (`Ctrl+C`), а не выделена. Watcher реагирует на изменения буфера.

**Q: На Linux не появляется иконка в трее.**
A: Установите `libappindicator-gtk3` (Arch) или `gir1.2-appindicator3-0.1` (Debian/Ubuntu) и перезапустите программу. Для GNOME может понадобиться расширение [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/).

**Q: Не работает горячая клавиша.**
A: Скорее всего вы на Wayland. Переключитесь на X11-сессию или запустите через XWayland.

**Q: Windows Defender ругается на exe.**
A: Это ложное срабатывание PyInstaller-сборок без code-signing. Запускайте из исходников, либо добавьте в исключения, либо соберите exe сами (`pyinstaller Fixup2X-windows.spec`).

**Q: Как исключить конкретное приложение?**
A: Настройки → Исключения → «＋» и введите имя процесса (`keepassxc` для Linux, `keepass.exe` для Windows). Есть кнопка «Рекомендуемые».

**Q: Куда уходят ссылки?**
A: **Никуда.** Программа не делает сетевых запросов, кроме опционального разворачивания коротких ссылок (`HEAD`-запрос к самому URL). Никакой телеметрии нет.

## Лицензия

[MIT](LICENSE) © 2025 Fixup2X contributors

---

<p align="center">
  <sub>Сделано с ❤️ для чистого и приватного веба.</sub>
</p>