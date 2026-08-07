"""
config_loader.py
=================
Loads config.json, fills in sane defaults for anything missing, and
gives the rest of the bot a single, typed object to work with instead
of scattering hardcoded values across the codebase.

Usage:
    from config_loader import load_config
    CONFIG = load_config()

If config.json does not exist, this copies config.example.json to
config.json on first run so the bot still starts with working defaults.
"""
import json
import os
import shutil
import sys

# Resolve paths relative to THIS file's location, not the process's current
# working directory. Otherwise, running the bot from a different folder (or
# via an IDE debug config with a different cwd) silently fails to find
# config.json / config.example.json, even though they're right next to
# config_loader.py.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
EXAMPLE_PATH = os.path.join(BASE_DIR, "config.example.json")

DEFAULTS = {
    "bot_name": "CORTEX",
    "version": "v0.1.0",
    "author": "Nero",
    "intro": {
        "enabled": True,
        "ascii_art": "CORTEX",
        "subtitle": "",
        "boot_lines": [],
    },
    "status_rotation": {
        "enabled": True,
        "interval_minutes": 5,
        "messages": [{"type": "watching", "text": "everything"}],
    },
    "personas": {
        "CORTEX": {
            "display_name": "CORTEX",
            "is_default": True,
            "system_prompt": "You are a helpful Discord assistant.",
        }
    },
    "pocket": {
        "enabled": True,
        "open_to_all": True,
        "allowed_user_ids": [],
    },
    "llm": {
        "base_url": "http://localhost:1234/v1",
        "model": "local-model",
        "max_tokens_response": 800,
        "temperature": 0.8,
        "max_history_messages": 20,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Merges override into base, recursively. override wins on conflicts."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _validate(config: dict) -> list[str]:
    """Returns a list of human-readable problems found in the config."""
    problems = []

    personas = config.get("personas", {})
    if not personas:
        problems.append("No personas defined under 'personas'.")

    default_count = sum(1 for p in personas.values() if p.get("is_default"))
    if default_count == 0:
        problems.append(
            "No persona has 'is_default': true. Add it to exactly one persona."
        )
    elif default_count > 1:
        problems.append(
            "More than one persona has 'is_default': true. Only one is allowed."
        )

    for key, persona in personas.items():
        if not persona.get("system_prompt", "").strip():
            problems.append(f"Persona '{key}' has an empty system_prompt.")

    valid_types = {"playing", "watching", "listening", "streaming", "competing"}
    for msg in config.get("status_rotation", {}).get("messages", []):
        if msg.get("type") not in valid_types:
            problems.append(
                f"status_rotation message has invalid type '{msg.get('type')}'. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )

    return problems


def load_config(path: str = CONFIG_PATH) -> dict:
    if not os.path.exists(path):
        if os.path.exists(EXAMPLE_PATH):
            shutil.copyfile(EXAMPLE_PATH, path)
            print(
                f"[config] No '{path}' found — created one from '{EXAMPLE_PATH}'. "
                "Edit it to personalize your bot, then restart."
            )
        else:
            print(
                f"[config] No '{path}' and no '{EXAMPLE_PATH}' found. "
                "Using built-in defaults. This is probably not what you want."
            )
            return DEFAULTS

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[config] ERROR: '{path}' is not valid JSON: {e}")
        print("[config] Check for a missing comma, quote, or bracket.")
        sys.exit(1)

    merged = _deep_merge(DEFAULTS, raw)

    problems = _validate(merged)
    if problems:
        print(f"[config] Found {len(problems)} problem(s) in '{path}':")
        for problem in problems:
            print(f"  - {problem}")
        print("[config] Fix these and restart the bot.")
        sys.exit(1)

    return merged


def get_default_persona_key(config: dict) -> str:
    for key, persona in config["personas"].items():
        if persona.get("is_default"):
            return key
    # _validate() guarantees exactly one default exists, so this is unreachable
    # in practice, but keeps this function safe to call standalone.
    return next(iter(config["personas"]))
