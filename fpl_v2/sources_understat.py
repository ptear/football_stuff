"""Understat team xG data.

Understat renders its pages client-side (no embedded JSON, no reachable endpoint),
so a live scrape needs a headless browser. Instead we read a manually-downloaded
understat league table (season aggregate) from data/raw — see config.UNDERSTAT_LEAGUE_CSV.

Isolated here so defense.py depends only on the returned shape, not the source.
"""

import pandas as pd

from fpl_v2 import config


def team_season_xga(filename: str = None) -> pd.DataFrame | None:
    """Return per-team season xGA from the manual understat league table, or None.

    Team names are mapped from understat's spelling to FPL's via
    config.UNDERSTAT_TO_FPL_TEAM (unmapped names pass through unchanged).

    Args:
        filename: CSV under RAW_DIR; defaults to config.UNDERSTAT_LEAGUE_CSV.

    Returns:
        DataFrame[team_name, matches, xGA], or None if the file is absent.
    """
    path = config.RAW_DIR / (filename or config.UNDERSTAT_LEAGUE_CSV)
    if not path.exists():
        return None
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    df["team_name"] = df["team"].map(lambda n: config.UNDERSTAT_TO_FPL_TEAM.get(n, n))
    return df[["team_name", "matches", "xGA"]].copy()
