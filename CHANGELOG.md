# Changelog

Все заметные изменения документируются здесь.
Формат — [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версии — [SemVer](https://semver.org/lang/ru/).

## [Unreleased]

## [1.0.0] — 2025-XX-XX

### Added
- Кроссплатформенный слой `platform_layer/` (Windows + Linux).
- Поддержка Ubuntu / Debian / Kali / Artix.
- Linux-реализация: `pyperclip` (xclip/xsel/wl-clipboard), `pystray`,
  `notify-send`, `xdotool`/`xprop`, `~/.config/autostart`, `fcntl.flock`.
- Автоопределение ОС на этапе импорта.
- GitHub Actions: CI (lint + smoke-тесты на Windows/Linux) и Release
  (сборка бинарников PyInstaller).

### Changed
- Windows-логика перенесена в `platform_layer/windows/*` без изменения
  поведения.
- `tray_win32.py` → `platform_layer/windows/tray.py` (файл `tray_win32.py`
  оставлен как заглушка для обратной совместимости).
- `save_config` теперь пишет атомарно (tempfile + `os.replace`).
- `os.startfile` заменён на `_open_path` (Windows: `startfile`, Linux: `xdg-open`).

### Fixed
- Падение при отсутствии `psutil`/`pynput` — теперь функции мягко
  отключаются с записью в лог.