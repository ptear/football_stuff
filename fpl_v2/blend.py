"""Multi-season xG baseline.

Blends per-player expected stats across one or more season snapshots into a single
baseline, weighted by config.BLEND_WEIGHTS and keyed on the permanent `code`.

The default weights use last season only, so this runs off a single live snapshot
with no history. Adding older seasons (once their snapshots exist) generalises the
`npxG_prev/2 + npxG_curr` idea from simplex_2425_halfway.ipynb.

Note on penalties: FPL `expected_goals` is total xG (penalties included), unlike the
non-penalty FBref npxG v1 used. See penalties.py / config for how that's handled.
"""

import pandas as pd

from fpl_v2 import config, sources_fpl

_STAT_COLS = ["expected_goals", "expected_assists", "minutes"]


def load_season_stats(season: str) -> pd.DataFrame:
    """Return per-player expected stats for `season` from its snapshot, keyed on code."""
    df = sources_fpl.load_snapshot(season)
    cols = ["code", "expected_goals", "expected_assists",
            "expected_goals_conceded", "minutes"]
    return df[cols].copy()


def blend_xg(weights: dict = None) -> pd.DataFrame:
    """Blend per-player xG/xAG/exposure across seasons.

    Args:
        weights: {season_label: weight}. Defaults to config.BLEND_WEIGHTS. Each
            season's snapshot totals are multiplied by its weight and summed.

    Returns:
        DataFrame[code, xG, xAG, s90] where s90 is blended 90s (minutes/90). A code
        missing from a season contributes 0 for that season.
    """
    weights = weights or config.BLEND_WEIGHTS
    acc = None
    for season, w in weights.items():
        s = load_season_stats(season).set_index("code")[_STAT_COLS] * w
        acc = s if acc is None else acc.add(s, fill_value=0.0)

    out = acc.reset_index()
    out = out.rename(columns={"expected_goals": "xG", "expected_assists": "xAG"})
    out["s90"] = out["minutes"] / 90.0
    return out[["code", "xG", "xAG", "s90"]]
