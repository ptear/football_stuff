"""Official FPL API access.

Thin wrappers that return tidy pandas frames from the public endpoints, all going
through the on-disk cache. `bootstrap` holds the live season's players + teams;
`load_snapshot` reads a dated snapshot saved by cache.snapshot_bootstrap (used for
the xG baseline so it survives the new-season reset).
"""

import glob
import json

import pandas as pd

from fpl_v2 import cache, config

# Columns pulled from a bootstrap `elements` record for the player table.
_ELEMENT_COLS = [
    "code", "id", "web_name", "first_name", "second_name",
    "element_type", "team", "now_cost", "status", "chance_of_playing_next_round",
    "minutes", "total_points", "starts",
    "expected_goals", "expected_assists", "expected_goal_involvements",
    "expected_goals_conceded", "expected_goals_per_90",
    "saves", "saves_per_90", "goals_conceded", "goals_conceded_per_90",
    "penalties_order", "direct_freekicks_order", "corners_and_indirect_freekicks_order",
]

_NUMERIC_COLS = [
    "expected_goals", "expected_assists", "expected_goal_involvements",
    "expected_goals_conceded", "expected_goals_per_90",
    "saves", "saves_per_90", "goals_conceded", "goals_conceded_per_90", "starts",
]


def bootstrap(refresh: bool = False) -> dict:
    """Return the live bootstrap-static payload (cached)."""
    return cache.fetch_json(
        f"{config.FPL_API_BASE}/bootstrap-static/", "bootstrap_static.json", refresh
    )


def _elements_frame(payload: dict) -> pd.DataFrame:
    """Build the tidy players frame from a bootstrap payload."""
    df = pd.DataFrame(payload["elements"])[_ELEMENT_COLS].copy()
    df[_NUMERIC_COLS] = df[_NUMERIC_COLS].apply(pd.to_numeric, errors="coerce")
    df["position"] = df["element_type"].map(config.POSITIONS)
    return df


def elements(refresh: bool = False) -> pd.DataFrame:
    """Live players frame: prices, positions, availability, set-piece order, xG."""
    return _elements_frame(bootstrap(refresh))


def teams(refresh: bool = False) -> pd.DataFrame:
    """Teams frame with FPL strength ratings, indexed by team id."""
    df = pd.DataFrame(bootstrap(refresh)["teams"])
    keep = [
        "id", "name", "short_name", "strength",
        "strength_overall_home", "strength_overall_away",
        "strength_attack_home", "strength_attack_away",
        "strength_defence_home", "strength_defence_away",
    ]
    return df[keep].copy()


def fixtures(refresh: bool = False) -> pd.DataFrame:
    """Season fixtures frame (team_h/team_a, event, kickoff)."""
    data = cache.fetch_json(
        f"{config.FPL_API_BASE}/fixtures/", "fixtures.json", refresh
    )
    return pd.DataFrame(data)


def load_snapshot(season: str = config.CURRENT_SEASON) -> pd.DataFrame:
    """Return the players frame from the most recent dated snapshot for `season`.

    Used as the xG-stats baseline so it keeps returning last season's finals even
    after the live API resets them. Falls back to the live payload if no snapshot
    exists yet.

    Args:
        season: season label to look up (matches cache.snapshot_bootstrap naming).
    """
    pattern = str(config.RAW_DIR / f"bootstrap_{season}_*.json")
    matches = sorted(glob.glob(pattern))
    if not matches:
        return elements()
    payload = json.loads(open(matches[-1]).read())
    return _elements_frame(payload)
