"""Expected-points model.

Combines a player's xG, xAG and their team's defensive signals into a single
season xPoints, using the position-dependent scoring weights in config:

    xPoints = xG * points_for_goal[pos]
            + xAG * points_for_assist
            + xClean * points_for_clean[pos] * (s90 / games_per_season)
            - xBadGames * points_for_conceded[pos] * (s90 / games_per_season)
            + expected_defcon_points
            + expected_appearance_points

The clean-sheet and bad-defensive-game terms are prorated by appearance share
(s90 / 38) so part-season players aren't credited with a full team's rate.
`expected_appearance_points` is not reprorated — see appearances.py.
"""

import pandas as pd

from fpl_v2 import config, defense


def breakdown(df: pd.DataFrame, team_rates: pd.DataFrame = None) -> pd.DataFrame:
    """Return `df` with `xClean`, `xBadGames` and the six xPoints component
    columns added: `goal_points`, `assist_points`, `clean_points`,
    `conceded_points`, `defcon_points`, `appearance_points`. These sum to `xPoints`.

    Args:
        df: player feature table (needs position, xG, xAG, s90, team_name).
        team_rates: DataFrame[team_name, xClean, xBadGames]. Defaults to
            defense.team_defensive_rates().
    """
    if team_rates is None:
        team_rates = defense.team_defensive_rates()

    df = df.merge(team_rates, on="team_name", how="left")
    df[["xClean", "xBadGames"]] = df[["xClean", "xBadGames"]].fillna(0.0)

    pts_goal = df["position"].map(config.POINTS_FOR_GOAL)
    pts_clean = df["position"].map(config.POINTS_FOR_CLEAN)
    pts_conceded = df["position"].map(config.POINTS_FOR_CONCEDED)

    df["goal_points"] = df["xG"] * pts_goal
    df["assist_points"] = df["xAG"] * config.POINTS_FOR_ASSIST
    df["clean_points"] = df["xClean"] * pts_clean * (df["s90"] / config.GAMES_PER_SEASON)
    df["conceded_points"] = -df["xBadGames"] * pts_conceded * (df["s90"] / config.GAMES_PER_SEASON)
    # Defensive-contribution and appearance points are already expected points
    # (not rates), computed upstream by defcon.py / appearances.py; add if present.
    df["defcon_points"] = df["expected_defcon_points"] if "expected_defcon_points" in df else 0.0
    df["appearance_points"] = df["expected_appearance_points"] if "expected_appearance_points" in df else 0.0
    return df


def compute(df: pd.DataFrame, team_rates: pd.DataFrame = None) -> pd.DataFrame:
    """Return `df` with `xClean`, `xBadGames` and an `xPoints` column added
    (plus the component columns from `breakdown`).

    Args:
        df: player feature table (needs position, xG, xAG, s90, team_name).
        team_rates: DataFrame[team_name, xClean, xBadGames]. Defaults to
            defense.team_defensive_rates().
    """
    df = breakdown(df, team_rates)
    df["xPoints"] = (df["goal_points"] + df["assist_points"] + df["clean_points"]
                     + df["conceded_points"] + df["defcon_points"] + df["appearance_points"])
    return df
