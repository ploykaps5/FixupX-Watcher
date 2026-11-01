"""Горячая клавиша — кроссплатформенно."""
from platform_layer import HotkeyListener, HAS_HOTKEY

# Совместимость со старым именем
HAS_PYNPUT = HAS_HOTKEY

__all__ = ["HotkeyListener", "HAS_HOTKEY", "HAS_PYNPUT"]