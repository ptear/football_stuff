"""Player feature table.

Joins current-season identity (price, position, club, availability, set-piece order)
from the live API onto the blended xG baseline, keyed on the permanent `code`. This
is the single source of truth the downstream model consumes — no fuzzy matching.

Prices come from the live `elements`; xG/xAG/90s come from `blend` (snapshot-backed,
so they survive the new-season stats reset). Both share the same `code`.
"""

import pandas as pd

from fpl_v2 import blend, config, sources_fpl

# Identity/attribute columns kept from the live elements frame (xG comes from blend).
_KEEP = [
    "code", "web_name", "first_name", "second_name", "position", "team",
    "now_cost", "status", "chance_of_playing_next_round",
    "penalties_order", "direct_freekicks_order", "corners_and_indirect_freekicks_order",
]


def _promoted_teams() -> set[str]:
    """Team names whose squad logged < PROMOTED_MIN_MINUTES prior-season PL minutes."""
    snap = sources_fpl.load_snapshot()
    tmap = sources_fpl.teams().set_index("id")["name"]
    by_team = snap.groupby("team")["minutes"].sum()
    return {tmap[tid] for tid, mins in by_team.items() if mins < config.PROMOTED_MIN_MINUTES}


def build(refresh: bool = False, weights: dict = None) -> pd.DataFrame:
    """Build the player feature table.

    Args:
        refresh: force re-download of live API data.
        weights: season blend weights passed to blend.blend_xg (defaults to config).

    Returns:
        One row per selectable player with columns: code, name, position, team/
        team_name, cost (FPL tenths), xG, xAG, s90, plus availability and set-piece
        order. Excludes GK and (when EXCLUDE_PROMOTED) promoted-team players.
    """
    elems = sources_fpl.elements(refresh)[_KEEP].copy()
    teams = sources_fpl.teams(refresh)
    xg = blend.blend_xg(weights)

    df = elems.merge(xg, on="code", how="left")
    df[["xG", "xAG", "s90"]] = df[["xG", "xAG", "s90"]].fillna(0.0)

    df["team_name"] = df["team"].map(teams.set_index("id")["name"])
    df = df.rename(columns={"now_cost": "cost"})

    df = df[~df["position"].isin(config.EXCLUDE_POSITIONS)]
    if config.EXCLUDE_PROMOTED:
        df = df[~df["team_name"].isin(_promoted_teams())]

    return df.reset_index(drop=True)
