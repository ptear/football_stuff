"""Goalkeeper expected-points ranking.

GKs are excluded from the outfield optimiser, so this is a standalone shortlist.
The model captures the save-volume signal directly: a keeper on a team that faces
many low-danger shots earns save points AND keeps clean sheets, so high
`saves_per_90` with low xGA scores on both terms.

    GK_xPoints ≈ expected_saves / saves_per_point        (1 pt per 3 saves)
               + clean_sheet_pts · appearance_share       (4 pts per clean sheet)
               − expected_goals_conceded / 2              (−1 pt per 2 conceded)

Appearance points are omitted to stay on the same scale as the outfield xPoints
model (which also omits them) — otherwise GKs look ~2·starts points better than
they are, distorting captaincy and the GK-vs-outfield budget tradeoff in the joint
optimiser. Expected goals conceded uses the team's understat xGA per game (the same
defensive signal as the outfield model), falling back to the keeper's own xGC.
"""

import numpy as np
import pandas as pd

from fpl_v2 import config, defense, sources_fpl, sources_understat


def build(refresh: bool = False) -> pd.DataFrame:
    """Return all goalkeepers with a GK_xPoints column."""
    elems = sources_fpl.elements(refresh)
    teams = sources_fpl.teams(refresh)
    gk = elems[elems["position"] == "GK"].copy()
    gk["team_name"] = gk["team"].map(teams.set_index("id")["name"])
    gk["s90"] = gk["minutes"] / 90.0

    xclean = defense.team_expected_clean_sheets()
    gk = gk.merge(xclean, on="team_name", how="left")
    gk["xClean"] = gk["xClean"].fillna(0.0)

    # Team xGA per game for the goals-conceded penalty (understat, else own xGC/90).
    season_xga = sources_understat.team_season_xga()
    if season_xga is not None:
        season_xga = season_xga.assign(xga_pg=season_xga["xGA"] / season_xga["matches"])
        gk = gk.merge(season_xga[["team_name", "xga_pg"]], on="team_name", how="left")
    else:
        gk["xga_pg"] = np.nan
    own_pg = gk["expected_goals_conceded"] / gk["s90"].replace(0, np.nan)
    gk["xga_pg"] = gk["xga_pg"].fillna(own_pg).fillna(own_pg.median())

    exp_saves = gk["saves_per_90"] * gk["s90"]
    exp_conceded = gk["xga_pg"] * gk["s90"]

    gk["GK_xPoints"] = (
        exp_saves / config.SAVES_PER_POINT
        + config.POINTS_FOR_CLEAN["GK"] * gk["xClean"] * (gk["s90"] / config.GAMES_PER_SEASON)
        - exp_conceded / config.GOALS_CONCEDED_PER_NEG_POINT
    )
    return gk


def rank(refresh: bool = False, min_minutes: int = 1000) -> pd.DataFrame:
    """Return goalkeepers sorted by GK_xPoints, filtered to regular starters.

    Args:
        min_minutes: drop keepers below this many prior-season minutes (backups /
            no-history), whose signal is unreliable.
    """
    gk = build(refresh)
    gk = gk[gk["minutes"] >= min_minutes]
    cols = ["web_name", "team_name", "now_cost", "s90", "saves_per_90",
            "xga_pg", "xClean", "GK_xPoints"]
    return gk.sort_values("GK_xPoints", ascending=False)[cols].reset_index(drop=True)
