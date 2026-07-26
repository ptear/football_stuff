"""Expected-points model.

Combines a player's xG, xAG and their team's expected clean sheets into a single
season xPoints, using the position-dependent scoring weights in config:

    xPoints = xG * points_for_goal[pos]
            + xAG * points_for_assist
            + xClean * points_for_clean[pos] * (s90 / games_per_season)

The clean-sheet term is prorated by appearance share (s90 / 38) so part-season
players aren't credited with a full team's clean sheets.
"""

import pandas as pd

from fpl_v2 import config, defense


def compute(df: pd.DataFrame, xclean: pd.DataFrame = None) -> pd.DataFrame:
    """Return `df` with an `xClean` and `xPoints` column added.

    Args:
        df: player feature table (needs position, xG, xAG, s90, team_name).
        xclean: DataFrame[team_name, xClean]. Defaults to defense.team_expected_clean_sheets().
    """
    if xclean is None:
        xclean = defense.team_expected_clean_sheets()

    df = df.merge(xclean, on="team_name", how="left")
    df["xClean"] = df["xClean"].fillna(0.0)

    pts_goal = df["position"].map(config.POINTS_FOR_GOAL)
    pts_clean = df["position"].map(config.POINTS_FOR_CLEAN)

    df["xPoints"] = (
        df["xG"] * pts_goal
        + df["xAG"] * config.POINTS_FOR_ASSIST
        + df["xClean"] * pts_clean * (df["s90"] / config.GAMES_PER_SEASON)
    )
    return df
