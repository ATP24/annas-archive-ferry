"""
Configuration management for Anna's Archive Ferry.
Decouples runtime persistent state from package source directories.
"""

import os
import json
from pathlib import Path

# User persistent runtime paths
USER_CONFIG_DIR = Path.home() / ".annas_ferry"
USER_CONFIG_FILE = USER_CONFIG_DIR / "config.json"
CACHE_DIR = Path.home() / ".annas_ferry_cache"

def ensure_user_dirs():
    """Lazily and safely ensures user config and cache directories exist."""
    try:
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

DEFAULT_CONFIG = {
    "primary_mirror": "https://zh.annas-archive.gl",
    "official_fallbacks": [
        "https://annas-archive.gl",
        "https://annas-archive.pk",
        "https://annas-archive.gd"
    ],
    "beacons": [
        "https://shadowlibraries.github.io/DirectDownloads/AnnasArchive/",
        "https://open-slum.pages.dev/"
    ],
    "heavy_threshold_mb": 30,
    "proxy": "auto",
    "default_download_dir": "~/Downloads/AnnasFerry",
    "default_format": "pdf",
    "auto_convert_djvu": True,
    "timeout_seconds": 180,
    "headless": True
}

def get_default_config():
    """Returns a copy of the default configuration."""
    return dict(DEFAULT_CONFIG)

def load_config(custom_path=None, expand_paths=True):
    """Loads configuration with fallback hierarchy:
    1. custom_path (if provided and exists)
    2. USER_CONFIG_FILE (~/.annas_ferry/config.json)
    3. Local config.json in project or scripts folder
    4. DEFAULT_CONFIG
    """
    cfg = get_default_config()

    candidate_files = []
    if custom_path:
        candidate_files.append(Path(custom_path))
    candidate_files.append(USER_CONFIG_FILE)

    # Local project fallback for backward compatibility
    pkg_dir = Path(__file__).resolve().parent
    candidate_files.append(pkg_dir.parent / "scripts" / "config.json")
    candidate_files.append(pkg_dir.parent / "config.json")

    for f in candidate_files:
        if f.exists() and f.is_file():
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if isinstance(data, dict):
                        cfg.update(data)
                        break
            except Exception:
                pass

    if expand_paths:
        raw_dir = cfg.get("default_download_dir", "~/Downloads/AnnasFerry")
        cfg["default_download_dir"] = str(Path(os.path.expandvars(os.path.expanduser(raw_dir))))
    return cfg

def save_dynamic_config(updates):
    """Safely updates dynamic configuration into ~/.annas_ferry/config.json."""
    ensure_user_dirs()
    # Load raw config without path expansion to preserve portable ~ paths
    current = load_config(expand_paths=False)
    current.update(updates)
    try:
        with open(USER_CONFIG_FILE, "w", encoding="utf-8") as fp:
            json.dump(current, fp, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[-] 写入用户配置失败: {e}", flush=True)
        return False

def get_config_value(key, default=None):
    """Retrieves a single configuration key value."""
    cfg = load_config()
    return cfg.get(key, default)
