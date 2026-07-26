"""Team defensive signals: expected clean sheets and expected "bad defensive games".

Both are threshold counts on a team's real per-match xG conceded (from
`sources_understat_match.team_match_xg`), not a probability model — see
config.CLEAN_SHEET_XGA_THRESHOLD / BAD_DEFENSIVE_GAME_XGA_THRESHOLD for the exact
rule. Rates are computed over whatever matches are available, then projected across
config.GAMES_PER_SEASON games, so this still works on a partial season.

`xBadGames` feeds the GK/DEF goals-conceded penalty (config.POINTS_FOR_CONCEDED).

Falls back to a Poisson estimate from FPL's own season-total `expected_goals_conceded`
when config.DEFENSE_USE_UNDERSTAT is off (no `xBadGames` in that path — it was never
tracked before the per-match source).
"""

import numpy as np
import pandas as pd

from fpl_v2 import config, sources_fpl, sources_understat_match


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


def _xclean_fpl() -> pd.DataFrame:
    """Fallback xClean per team from FPL-derived season xGA (Poisson: P(0 conceded) = exp(-xGA_per_game))."""
    xga_per_game = _team_season_xga_fpl() / config.GAMES_PER_SEASON
    xclean = config.GAMES_PER_SEASON * np.exp(-xga_per_game)
    return xclean.rename("xClean").reset_index()


def team_defensive_rates(season: str = None, refresh: bool = False) -> pd.DataFrame:
    """Per-team clean-sheet and bad-defensive-game rates from real per-match xG conceded.

    Args:
        season: understat season label, passed through to
            sources_understat_match.team_match_xg (defaults to config.UNDERSTAT_SEASON).
        refresh: force re-download instead of using the cached match data.

    Returns:
        DataFrame[team_name, xClean, xBadGames], both counted from a threshold on
        each match's xG conceded, then projected across config.GAMES_PER_SEASON games.
    """
    matches = sources_understat_match.team_match_xg(season, refresh=refresh)
    xga = matches.groupby("team_name")["xG_against"]
    games = xga.size()
    clean_games = xga.apply(lambda s: (s < config.CLEAN_SHEET_XGA_THRESHOLD).sum())
    bad_games = xga.apply(lambda s: (s > config.BAD_DEFENSIVE_GAME_XGA_THRESHOLD).sum())

    out = pd.DataFrame({"games": games, "clean_games": clean_games, "bad_games": bad_games})
    out["xClean"] = out["clean_games"] / out["games"] * config.GAMES_PER_SEASON
    out["xBadGames"] = out["bad_games"] / out["games"] * config.GAMES_PER_SEASON
    return out[["xClean", "xBadGames"]].reset_index()


def team_expected_clean_sheets(refresh: bool = False) -> pd.DataFrame:
    """Return DataFrame[team_name, xClean].

    Uses the per-match threshold-count rate when config.DEFENSE_USE_UNDERSTAT is
    on, otherwise the FPL-derived Poisson fallback.
    """
    if config.DEFENSE_USE_UNDERSTAT:
        return team_defensive_rates(refresh=refresh)[["team_name", "xClean"]]
    return _xclean_fpl()
