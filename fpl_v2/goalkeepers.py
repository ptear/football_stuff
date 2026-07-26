"""Goalkeeper expected-points ranking.

GKs are excluded from the outfield optimiser, so this is a standalone shortlist.
The model captures the save-volume signal directly: a keeper on a team that faces
many low-danger shots earns save points AND keeps clean sheets, so high
`saves_per_90` with low xGA scores on both terms.

    GK_xPoints ≈ expected_saves / saves_per_point            (1 pt per 3 saves)
               + clean_sheet_pts · appearance_share           (4 pts per clean sheet)
               − conceded_pts · bad_game_share                (1 pt per bad defensive game)
               + expected_appearance_points
               + expected_bonus_points

`xClean` and `xBadGames` both come from the team's real per-match xG conceded (see
defense.py) — the same defensive signal the outfield model uses. Appearance and
bonus points come from appearances.py / bonus.py — same sources, same "carry last
season forward as-is" treatment as the outfield model, so GK and outfield xPoints
stay on one scale.
"""

import pandas as pd

from fpl_v2 import appearances, bonus, config, defense, sources_fpl


def build(refresh: bool = False) -> pd.DataFrame:
    """Return all goalkeepers with a GK_xPoints column."""
    elems = sources_fpl.elements(refresh)
    teams = sources_fpl.teams(refresh)
    gk = elems[elems["position"] == "GK"].copy()
    gk["team_name"] = gk["team"].map(teams.set_index("id")["name"])
    gk["s90"] = gk["minutes"] / 90.0

    rates = defense.team_defensive_rates(refresh=refresh)
    gk = gk.merge(rates, on="team_name", how="left")
    gk[["xClean", "xBadGames"]] = gk[["xClean", "xBadGames"]].fillna(0.0)
    gk = appearances.expected_appearance_points(gk, refresh=refresh)
    gk = bonus.expected_bonus_points(gk, refresh=refresh)

    exp_saves = gk["saves_per_90"] * gk["s90"]

    gk["GK_xPoints"] = (
        exp_saves / config.SAVES_PER_POINT
        + config.POINTS_FOR_CLEAN["GK"] * gk["xClean"] * (gk["s90"] / config.GAMES_PER_SEASON)
        - config.POINTS_FOR_CONCEDED["GK"] * gk["xBadGames"] * (gk["s90"] / config.GAMES_PER_SEASON)
        + gk["expected_appearance_points"]
        + gk["expected_bonus_points"]
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
            "xClean", "xBadGames", "expected_appearance_points",
            "expected_bonus_points", "GK_xPoints"]
    return gk.sort_values("GK_xPoints", ascending=False)[cols].reset_index(drop=True)
