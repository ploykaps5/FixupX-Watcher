"""
Кроссплатформенный буфер обмена.
Вся платформенная логика — в platform_layer.clipboard.
"""
from platform_layer import (
    read_text,
    replace_text_if_safe,
    read_format_list,
)

__all__ = ["read_text", "replace_text_if_safe", "read_format_list"]