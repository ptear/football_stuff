"""Penalty-taker xG bonus.

Data-driven replacement for v1's hardcoded taker list: the bonus is applied to
whoever is the nailed taker (`penalties_order == 1`) for their club, using the
constants in config.

IMPORTANT: FPL `expected_goals` already includes penalties, so applying this on top
double-counts for an established taker. It is therefore gated by
config.APPLY_PENALTY_BONUS (off by default). See config for the rationale.
"""

import pandas as pd

from fpl_v2 import config


def penalty_bonus_xg() -> float:
    """Expected extra xG from being a nailed penalty taker for a full season.

    (mean penalties per team) * (xG per penalty). The top/bottom-team refinement
    from v1 (PENALTY_TOP_BOTTOM_DIFF) is left as an extension once team strength is
    populated; a flat bonus is used here.
    """
    return config.PENALTY_BASE_PER_TEAM * config.PENALTY_XG


def apply(df: pd.DataFrame) -> pd.DataFrame:
    """Return `df` with the penalty bonus added to nailed takers' xG.

    No-op unless config.APPLY_PENALTY_BONUS is True. Operates on a copy.

    Args:
        df: player feature table with `xG` and `penalties_order` columns.
    """
    df = df.copy()
    if not config.APPLY_PENALTY_BONUS:
        return df
    takers = df["penalties_order"] == 1
    df.loc[takers, "xG"] = df.loc[takers, "xG"] + penalty_bonus_xg()
    return df
