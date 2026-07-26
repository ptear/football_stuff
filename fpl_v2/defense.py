"""Team defensive strength -> expected clean sheets (xClean).

`xClean` is the expected number of clean sheets a team keeps over a season; the
xPoints model prorates it by each player's appearance share.

Primary source is understat team xGA (manual league-table download — see
sources_understat). Fallback derives team season xGA from FPL
`expected_goals_conceded`. Either way, expected clean sheets come from a Poisson
model: P(clean sheet) = P(0 conceded) = exp(-xGA_per_game).
"""

import numpy as np
import pandas as pd

from fpl_v2 import config, sources_fpl, sources_understat


def _team_season_xga_fpl() -> pd.Series:
    """Team season xGA from the snapshot, indexed by team name.

    Uses the largest `expected_goals_conceded` among a club's players, i.e. the
    ever-present goalkeeper — a clean proxy for the team's full-season xGA.
    """
    snap = sources_fpl.load_snapshot()
    tmap = sources_fpl.teams().set_index("id")["name"]
    xga = snap.groupby("team")["expected_goals_conceded"].max()
    xga.index = xga.index.map(tmap).rename("team_name")
    return xga


def _xclean_from_xga(xga_per_game: pd.Series) -> pd.Series:
    """Poisson expected clean sheets over a season from per-game xGA."""
    return config.GAMES_PER_SEASON * np.exp(-xga_per_game)


def _xclean_fpl() -> pd.DataFrame:
    """Fallback xClean per team from FPL-derived season xGA."""
    xga = _team_season_xga_fpl()
    xclean = _xclean_from_xga(xga / config.GAMES_PER_SEASON)
    return xclean.rename("xClean").reset_index()


def _xclean_understat(season_xga: pd.DataFrame) -> pd.DataFrame:
    """xClean per team from understat season xGA (Poisson on per-game xGA)."""
    per_game = season_xga["xGA"] / season_xga["matches"]
    xclean = _xclean_from_xga(per_game)
    out = season_xga[["team_name"]].copy()
    out["xClean"] = xclean.values
    return out


def team_expected_clean_sheets(refresh: bool = False) -> pd.DataFrame:
    """Return DataFrame[team_name, xClean].

    Uses understat team xGA when available and enabled, otherwise the FPL-derived
    fallback.
    """
    if config.DEFENSE_USE_UNDERSTAT:
        season_xga = sources_understat.team_season_xga()
        if season_xga is not None:
            return _xclean_understat(season_xga)
    return _xclean_fpl()
