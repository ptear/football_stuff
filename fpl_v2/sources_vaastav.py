"""vaastav mirror — defensive-contribution stats only.

The preseason official API zeroes the defensive-actions fields at season rollover,
so we read them from vaastav's end-of-season players_raw for the baseline season.
Quarantined here; the rest of the codebase uses the official API. The long-term
plan is to replace this with our own in-season bootstrap snapshots.
"""

import io

import pandas as pd

from fpl_v2 import cache, config

# Raw defensive components + identity needed to compute DefCon and detect moves.
_COLS = [
    "code", "element_type", "team", "minutes",
    "clearances_blocks_interceptions", "tackles", "recoveries",
    "defensive_contribution",
]


def defensive_stats(season: str = None, refresh: bool = False) -> pd.DataFrame:
    """Return per-player defensive components for `season`, keyed on `code`.

    Args:
        season: vaastav season label (defaults to config.VAASTAV_SEASON).
        refresh: force re-download.

    Returns:
        DataFrame with _COLS plus `position` and `old_team_name` (the club the
        player logged those stats at that season).
    """
    season = season or config.VAASTAV_SEASON
    base = f"{config.VAASTAV_BASE}/{season}"
    players = pd.read_csv(io.StringIO(
        cache.fetch_text(f"{base}/players_raw.csv", f"vaastav_players_{season}.csv", refresh)))
    teams = pd.read_csv(io.StringIO(
        cache.fetch_text(f"{base}/teams.csv", f"vaastav_teams_{season}.csv", refresh)))

    df = players[_COLS].copy()
    df["position"] = df["element_type"].map(config.POSITIONS)
    df["old_team_name"] = df["team"].map(teams.set_index("id")["name"])
    return df
