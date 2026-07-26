"""End-to-end orchestration: sources -> features -> xPoints -> optimised squad.

    from fpl_v2 import pipeline
    forecast, squad = pipeline.run()

`build_forecast` returns the full player table with xPoints; `run` also solves for
the best squad. Set refresh=True to re-pull live data.
"""

import pandas as pd

from fpl_v2 import config, optimize, overrides, penalties, players, xpoints
from fpl_v2.optimize import SquadResult


def build_forecast(refresh: bool = False, weights: dict = None) -> pd.DataFrame:
    """Build the full player forecast table (xPoints per player).

    Order: feature table -> manual overrides -> penalty bonus -> xPoints.
    """
    df = players.build(refresh=refresh, weights=weights)
    df = overrides.apply(df)
    df = penalties.apply(df)
    df = xpoints.compute(df)
    return df


def run(refresh: bool = False, weights: dict = None,
        save: bool = False) -> tuple[pd.DataFrame, SquadResult]:
    """Build the forecast and optimise the squad.

    Args:
        refresh: force re-pull of live data.
        weights: season blend weights (defaults to config).
        save: if True, write the forecast to data/processed/forecast.csv.

    Returns:
        (forecast table, best SquadResult).
    """
    forecast = build_forecast(refresh=refresh, weights=weights)
    if save:
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        forecast.sort_values("xPoints", ascending=False).to_csv(
            config.PROCESSED_DIR / "forecast.csv", index=False
        )
    return forecast, optimize.optimize(forecast)
