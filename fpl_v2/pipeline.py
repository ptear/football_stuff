"""End-to-end orchestration: sources -> features -> xPoints -> optimised squad.

    from fpl_v2 import pipeline
    forecast, squad = pipeline.run()

`build_forecast` returns the full player table with xPoints; `run` also solves for
the best squad. Set refresh=True to re-pull live data.
"""

import pandas as pd

from fpl_v2 import (appearances, bonus, config, defcon, goalkeepers, optimize,
                    overrides, penalties, players, xpoints)
from fpl_v2.optimize import SquadResult

# Columns the optimiser needs; the shared schema for the outfield + GK pool.
_POOL_COLS = ["code", "web_name", "position", "team_name", "cost", "xPoints"]

# Slim summary columns: identity + the direct xPoints constituents (not the
# intermediate signals used to derive them, e.g. xG/xClean/expected_defcon_points).
_SUMMARY_COLS = ["web_name", "team_name", "position", "cost",
                 "goal_points", "assist_points", "clean_points", "conceded_points",
                 "defcon_points", "appearance_points", "bonus_points", "xPoints"]


def build_forecast(refresh: bool = False, weights: dict = None,
                   defensive_contribution: bool = True) -> pd.DataFrame:
    """Build the full player forecast table (xPoints per player).

    Order: feature table -> manual overrides -> penalty bonus -> DefCon points ->
    appearance points -> bonus points -> xPoints.

    Args:
        defensive_contribution: include expected DefCon points (needs the vaastav source).
    """
    df = players.build(refresh=refresh, weights=weights)
    df = overrides.apply(df)
    df = penalties.apply(df)
    if defensive_contribution:
        df = defcon.expected_defcon_points(df, refresh=refresh)
    df = appearances.expected_appearance_points(df, refresh=refresh)
    df = bonus.expected_bonus_points(df, refresh=refresh)
    df = xpoints.compute(df)
    return df


def goalkeeper_pool(refresh: bool = False) -> pd.DataFrame:
    """GK rows with a unified `xPoints` (= GK_xPoints), filtered to squad-worthy keepers.

    Excludes promoted-team keepers and backups (< GK_MIN_MINUTES) so the optimiser
    only considers realistic starters.
    """
    gk = goalkeepers.build(refresh)
    gk = gk.rename(columns={"now_cost": "cost", "GK_xPoints": "xPoints"})
    gk = gk[~gk["team_name"].isin(players._promoted_teams())
            & (gk["minutes"] >= config.GK_MIN_MINUTES)]
    return gk[_POOL_COLS]


def player_pool(refresh: bool = False, weights: dict = None,
                defensive_contribution: bool = True) -> pd.DataFrame:
    """Combined outfield + goalkeeper pool with a shared schema for the optimiser."""
    outfield = build_forecast(refresh=refresh, weights=weights,
                              defensive_contribution=defensive_contribution)
    gk = goalkeeper_pool(refresh=refresh)
    return pd.concat([outfield[_POOL_COLS], gk], ignore_index=True)


def run(refresh: bool = False, weights: dict = None,
        save: bool = False) -> tuple[pd.DataFrame, SquadResult]:
    """Build the forecast and optimise a full XI (GK + 10 outfield).

    Args:
        refresh: force re-pull of live data.
        weights: season blend weights (defaults to config).
        save: if True, write the outfield forecast to data/processed/forecast.csv,
            plus a slim data/processed/forecast_summary.csv (surname, team, position,
            cost and the xPoints constituents only).

    Returns:
        (outfield forecast table, best SquadResult over the GK+outfield pool).
    """
    forecast = build_forecast(refresh=refresh, weights=weights)
    if save:
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        ranked = forecast.sort_values("xPoints", ascending=False)
        ranked.to_csv(config.PROCESSED_DIR / "forecast.csv", index=False)
        ranked[_SUMMARY_COLS].rename(columns={"web_name": "surname"}).to_csv(
            config.PROCESSED_DIR / "forecast_summary.csv", index=False
        )
    pool = pd.concat([forecast[_POOL_COLS], goalkeeper_pool(refresh=refresh)],
                     ignore_index=True)
    return forecast, optimize.optimize(pool)
