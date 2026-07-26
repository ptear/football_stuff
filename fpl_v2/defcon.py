"""Defensive-contribution expected points.

FPL 2025-26 awards 2 pts in a match when a player hits a defensive-action threshold
(DEF: CBIT >= 10; MID/FWD: CBIT + recoveries >= 12). We only have season totals, so
expected points come from a Poisson-threshold on the per-90 rate:

    expected_defcon_pts = 2 * P(Poisson(rate_per90) >= threshold) * expected_starts

Transferred players are rescaled by team style. A club's per-slot defensive intensity
(defensive actions per outfield-90) is treated as a stable property of how it plays;
a mover's rate is scaled by intensity_new / intensity_old. Stayers are unchanged. We
do NOT net the player out of his old club (that would assume the slot vanishes rather
than being refilled); see the project discussion. Movers are flagged for manual review.
"""

import numpy as np
import pandas as pd
from scipy.stats import poisson

from fpl_v2 import config, sources_vaastav


def _cbit(df: pd.DataFrame) -> pd.Series:
    return df["clearances_blocks_interceptions"] + df["tackles"]


def team_intensity(vdf: pd.DataFrame) -> pd.Series:
    """Per-team defensive intensity: defensive actions per outfield-90, by team name."""
    out = vdf[vdf["position"].isin(["DEF", "MID", "FWD"]) & (vdf["minutes"] > 0)].copy()
    out["actions"] = _cbit(out) + out["recoveries"]
    g = out.groupby("old_team_name").agg(actions=("actions", "sum"),
                                         minutes=("minutes", "sum"))
    return g["actions"] / (g["minutes"] / 90.0)


def expected_defcon_points(feature_df: pd.DataFrame, season: str = None,
                           refresh: bool = False) -> pd.DataFrame:
    """Add `expected_defcon_points`, `defcon_multiplier` and `is_mover` to `feature_df`.

    Args:
        feature_df: player table with code, position, team_name (current), s90.
        season: vaastav season for the defensive baseline (defaults to config).
        refresh: force re-download of the vaastav source.
    """
    vdf = sources_vaastav.defensive_stats(season, refresh)
    intensity = team_intensity(vdf)

    hist = vdf[vdf["minutes"] > 0].copy()
    hist["s90_hist"] = hist["minutes"] / 90.0
    hist["cbit"] = _cbit(hist)
    hist = hist[["code", "old_team_name", "s90_hist", "cbit", "recoveries"]]

    df = feature_df.merge(hist, on="code", how="left")

    threshold = df["position"].map({p: v["threshold"] for p, v in config.DEFCON.items()})
    use_recov = df["position"].map({p: v["recoveries"] for p, v in config.DEFCON.items()})
    actions = df["cbit"] + np.where(use_recov.fillna(False), df["recoveries"], 0.0)
    rate = actions / df["s90_hist"]

    old_int = df["old_team_name"].map(intensity)
    new_int = df["team_name"].map(intensity)
    df["defcon_multiplier"] = (new_int / old_int).fillna(1.0)
    df["is_mover"] = df["old_team_name"].notna() & (df["old_team_name"] != df["team_name"])

    adj_rate = rate * df["defcon_multiplier"]
    p_clear = pd.Series(1.0 - poisson.cdf(threshold - 1, adj_rate), index=df.index).fillna(0.0)
    df["expected_defcon_points"] = config.DEFCON_POINTS * p_clear * df["s90"]
    return df
