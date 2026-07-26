"""On-disk caching + season snapshots.

Two jobs:
  1. `fetch_json` / `fetch_text` — fetch-or-load helper so notebook reruns are fast
     and reproducible; pass refresh=True to force a re-download.
  2. `snapshot_bootstrap` — persist a dated copy of the live bootstrap-static so we
     build our own multi-season history (the live API only holds the current season).
"""

import json
from datetime import date
from pathlib import Path

import requests

from fpl_v2 import config


def _get(url: str) -> requests.Response:
    resp = requests.get(url, headers=config.HTTP_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp


def fetch_json(url: str, cache_name: str, refresh: bool = False) -> dict:
    """Return JSON from `url`, caching it at data/raw/<cache_name>.

    Args:
        url: endpoint to fetch.
        cache_name: filename (with .json extension) under RAW_DIR.
        refresh: if True, always re-download and overwrite the cache.
    """
    path = config.RAW_DIR / cache_name
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    data = _get(url).json()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


def fetch_text(url: str, cache_name: str, refresh: bool = False) -> str:
    """Return raw text from `url`, caching it at data/raw/<cache_name>."""
    path = config.RAW_DIR / cache_name
    if path.exists() and not refresh:
        return path.read_text()
    text = _get(url).text
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return text


def snapshot_bootstrap(season: str = config.CURRENT_SEASON) -> Path:
    """Save a dated snapshot of the live bootstrap-static for `season`.

    The live API overwrites expected-stats totals when a new season starts, so a
    snapshot taken while last season's finals are still served preserves them for
    future multi-season blending. Idempotent per (season, date).

    Args:
        season: label to tag the snapshot with (the season the stats belong to).

    Returns:
        Path to the written snapshot.
    """
    data = _get(f"{config.FPL_API_BASE}/bootstrap-static/").json()
    path = config.RAW_DIR / f"bootstrap_{season}_{date.today().isoformat()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return path
