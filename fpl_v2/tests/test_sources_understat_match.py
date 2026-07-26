import pandas as pd

from fpl_v2 import sources_understat_match


class _FakeReader:
    """Stands in for sd.Understat so the test doesn't hit the network."""

    def __init__(self, **kwargs):
        pass

    def read_schedule(self):
        df = pd.DataFrame([
            {"date": pd.Timestamp("2025-08-15"), "home_team": "Arsenal", "away_team": "Manchester United",
             "home_xg": 2.0, "away_xg": 0.5},
            {"date": pd.Timestamp("2025-08-22"), "home_team": "Manchester United", "away_team": "Arsenal",
             "home_xg": 1.0, "away_xg": 1.5},
        ])
        return df.set_index(["date"])


def test_team_match_xg_one_row_per_team_per_match(monkeypatch):
    monkeypatch.setattr(sources_understat_match.sd, "Understat", _FakeReader)

    out = sources_understat_match.team_match_xg()

    assert len(out) == 4  # 2 matches x 2 teams
    arsenal = out[out["team_name"] == "Arsenal"].sort_values("date")
    assert list(arsenal["xG_for"]) == [2.0, 1.5]
    assert list(arsenal["xG_against"]) == [0.5, 1.0]

    man_utd = out[out["team_name"] == "Man Utd"].sort_values("date")  # UNDERSTAT_TO_FPL_TEAM mapping applied
    assert list(man_utd["xG_for"]) == [0.5, 1.0]
    assert list(man_utd["xG_against"]) == [2.0, 1.5]
