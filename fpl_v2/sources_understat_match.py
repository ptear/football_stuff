"""Per-match team xG from Understat, via the `soccerdata` package.

`sources_understat.py` only has a manual season-aggregate CSV — a direct scrape
doesn't work because Understat now renders team/league pages client-side (the data
variables its own JS declares, e.g. `datesData`, are never populated in the static
HTML; there's no embedded JSON to regex out anymore).

`soccerdata`'s Understat reader gets past this with a TLS-fingerprint client (not a
full headless browser — that's only needed for its other readers, e.g. FBref), and
caches results locally under `data/raw` like the rest of this package's sources.
"""

import pandas as pd
import soccerdata as sd

from fpl_v2 import config


def team_match_xg(season: str = None, league: str = None, refresh: bool = False) -> pd.DataFrame:
    """Return one row per team per match: [team_name, date, xG_for, xG_against].

    Args:
        season: Understat season label (defaults to config.UNDERSTAT_SEASON — the
            year a season started, e.g. 2025 for 2025/26).
        league: soccerdata league key (defaults to config.UNDERSTAT_LEAGUE).
        refresh: force re-download instead of using soccerdata's local cache.

    Returns:
        Two rows per fixture (one per side), sorted by team_name then date. Team
        names are mapped to FPL's spelling via config.UNDERSTAT_TO_FPL_TEAM.
    """
    season = season or config.UNDERSTAT_SEASON
    league = league or config.UNDERSTAT_LEAGUE

    reader = sd.Understat(leagues=league, seasons=season, no_cache=refresh,
                          data_dir=config.RAW_DIR / "understat_match")
    sched = reader.read_schedule().reset_index()

    home = sched[["date", "home_team", "home_xg", "away_xg"]].rename(
        columns={"home_team": "team", "home_xg": "xG_for", "away_xg": "xG_against"})
    away = sched[["date", "away_team", "away_xg", "home_xg"]].rename(
        columns={"away_team": "team", "away_xg": "xG_for", "home_xg": "xG_against"})

    out = pd.concat([home, away], ignore_index=True)
    out["team_name"] = out["team"].map(lambda n: config.UNDERSTAT_TO_FPL_TEAM.get(n, n))
    out[["xG_for", "xG_against"]] = out[["xG_for", "xG_against"]].astype(float)
    return out[["team_name", "date", "xG_for", "xG_against"]].sort_values(
        ["team_name", "date"]).reset_index(drop=True)
