"""
intro.py
========
Reusable boot-screen for any of your bots (Cortex, E.R.G.O, SENTINEL, INIT, ...).
Fully driven by the "intro" section of config.json — no per-bot code changes needed,
just point it at a different config.

Usage:
    from intro import show_intro
    show_intro(config)
"""
import ctypes
import os
import shutil
import sys
import time


def set_console_title(title: str):
    """Sets the terminal window title. Windows + Unix-safe."""
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception:
            pass  # non-fatal — some terminals (e.g. certain CI runners) don't support this
    else:
        sys.stdout.write(f"\33]0;{title}\a")
        sys.stdout.flush()


def slow_type(text: str, speed: float = 0.02, newline: bool = True):
    """Prints text character by character for a 'booting up' feel."""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(speed)
    if newline:
        print()


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def show_intro(config: dict):
    """
    Renders the boot intro based on config["intro"], config["bot_name"],
    config["version"], and config["author"]. Does nothing if
    config["intro"]["enabled"] is False — useful for quiet/production restarts.
    """
    intro_cfg = config.get("intro", {})
    if not intro_cfg.get("enabled", True):
        return

    bot_name = config.get("bot_name", "BOT")
    version = config.get("version", "v0.0.0")
    author = config.get("author", "unknown")

    clear_screen()
    set_console_title(f"{bot_name} — {version}")

    ascii_art = intro_cfg.get("ascii_art", bot_name)
    width = shutil.get_terminal_size((80, 20)).columns
    for line in ascii_art.strip("\n").split("\n"):
        print(line.center(width))

    print()
    subtitle = intro_cfg.get("subtitle", "")
    if subtitle:
        print(subtitle.center(width))

    time.sleep(1)
    print()
    slow_type(f"  {bot_name} {version} — by {author}", speed=0.02)
    time.sleep(0.5)

    boot_lines = intro_cfg.get("boot_lines", [])
    for line in boot_lines:
        slow_type(f"  [BOOT] {line}", speed=0.015)
        time.sleep(0.15)

    print()
    slow_type("  system ready.", speed=0.03)
    time.sleep(0.5)
    print()
