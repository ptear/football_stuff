"""Expected appearance points, carried forward as-is from last season's actuals.

FPL awards 1 pt for any appearance and 2 pts for 60+ minutes in a match. Season-total
minutes alone can't tell you how many separate matches crossed the 60-minute mark
(a 90-minute start and three 20-minute sub appearances both sum to the same total
minutes but earn very different points), so this sums a real per-fixture points rule
over `sources_vaastav.fixture_minutes` instead.

We don't reproject this forward the way xClean/xBadGames are (`* s90/38`) — like
xG/xAG, last season's actual total *is* the estimate, on the assumption a player's
role next season mirrors last season until the first few games say otherwise.
"""

import numpy as np
import pandas as pd

from fpl_v2 import config, sources_vaastav


def expected_appearance_points(feature_df: pd.DataFrame, season: str = None,
                               refresh: bool = False) -> pd.DataFrame:
    """Add `expected_appearance_points` to `feature_df`, keyed on `code`.

    Args:
        feature_df: player table with a `code` column.
        season: vaastav season for the fixture-level minutes (defaults to
            config.VAASTAV_SEASON).
        refresh: force re-download of the vaastav source.
    """
    fixtures = sources_vaastav.fixture_minutes(season, refresh)
    per_fixture = np.select(
        [fixtures["minutes"] >= 60, fixtures["minutes"] > 0],
        [config.APPEARANCE_POINTS_FULL, config.APPEARANCE_POINTS_SHORT],
        default=0,
    )
    per_player = pd.Series(per_fixture, index=fixtures.index).groupby(fixtures["code"]).sum()
    per_player = per_player.rename("expected_appearance_points").reset_index()

    df = feature_df.merge(per_player, on="code", how="left")
    df["expected_appearance_points"] = df["expected_appearance_points"].fillna(0.0)
    return df
