"""Исключения по активному приложению — кроссплатформенно."""
from platform_layer import (
    is_excluded,
    get_foreground_app_name,
    SUGGESTED_EXCLUSIONS,
    HAS_EXCLUSIONS,
)

# Обратная совместимость: в старом коде использовался HAS_PSUTIL
HAS_PSUTIL = HAS_EXCLUSIONS

__all__ = [
    "is_excluded", "get_foreground_app_name",
    "SUGGESTED_EXCLUSIONS", "HAS_EXCLUSIONS", "HAS_PSUTIL",
]