"""Expected bonus points, carried forward as-is from last season's actual total.

Real FPL bonus points come from a proprietary BPS ranking (the top 3 players by BPS
in a match get 3/2/1 points) built from inputs we don't have (tackles won, chances
created, etc.), so we don't attempt to model it. Instead we carry forward last
season's actual `bonus` total per player — same "until the first few games say
otherwise" assumption as appearances.py's appearance points. Bonus skews toward
goal involvements, so this term tends to lift forwards/attacking mids relative to
defenders more than the rest of the model does on its own.
"""

import pandas as pd

from fpl_v2 import sources_vaastav


def expected_bonus_points(feature_df: pd.DataFrame, season: str = None,
                          refresh: bool = False) -> pd.DataFrame:
    """Add `expected_bonus_points` to `feature_df`, keyed on `code`.

    Args:
        feature_df: player table with a `code` column.
        season: vaastav season for last season's bonus total (defaults to
            config.VAASTAV_SEASON, via sources_vaastav).
        refresh: force re-download of the vaastav source.
    """
    bonus = sources_vaastav.bonus_points(season, refresh)
    df = feature_df.merge(bonus, on="code", how="left")
    df = df.rename(columns={"bonus": "expected_bonus_points"})
    df["expected_bonus_points"] = df["expected_bonus_points"].fillna(0.0)
    return df
