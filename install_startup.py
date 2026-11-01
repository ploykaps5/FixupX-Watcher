"""
Ручное управление автозагрузкой из CLI.
  python install_startup.py add
  python install_startup.py remove
  python install_startup.py status
"""
import sys
from platform_layer import (
    install_startup, uninstall_startup, is_startup_enabled, PLATFORM,
)


def main(argv):
    action = argv[1] if len(argv) > 1 else "add"
    if action == "add":
        ok = install_startup()
        print(f"[{'✓' if ok else '!'}] Добавление в автозагрузку: {ok}")
    elif action == "remove":
        ok = uninstall_startup()
        print(f"[{'✓' if ok else '!'}] Удаление из автозагрузки: {ok}")
    elif action == "status":
        print(f"Платформа: {PLATFORM}")
        print(f"В автозагрузке: {is_startup_enabled()}")
    else:
        print("Использование: python install_startup.py [add|remove|status]")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))