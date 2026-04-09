"""
Utilidad de configuración persistente.
Guarda preferencias del usuario (última vista, tema) en un JSON local.
No se versiona — está en .gitignore.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
CONFIG_FILE = BASE_DIR / "data" / "config.json"

DEFAULTS = {
    "last_view": "dashboard",
    "theme": "dark",
}


def _load() -> dict:
    try:
        if CONFIG_FILE.exists():
            return {**DEFAULTS, **json.loads(CONFIG_FILE.read_text())}
    except Exception:
        pass
    return dict(DEFAULTS)


def _save(cfg: dict) -> None:
    try:
        CONFIG_FILE.parent.mkdir(exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    except Exception:
        pass


def get(key: str):
    return _load().get(key, DEFAULTS.get(key))


def set(key: str, value) -> None:
    cfg = _load()
    cfg[key] = value
    _save(cfg)
