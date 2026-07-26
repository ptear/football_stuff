import pandas as pd

from fpl_v2 import blend


def _fake_stats():
    return pd.DataFrame({
        "code": [1, 2],
        "expected_goals": [10.0, 4.0],
        "expected_assists": [2.0, 1.0],
        "expected_goals_conceded": [0.0, 30.0],
        "minutes": [3420, 1710],   # 38 and 19 nineties
    })


def test_single_season_is_identity(monkeypatch):
    """Weights {season: 1.0} pass totals through unchanged; s90 = minutes/90."""
    monkeypatch.setattr(blend, "load_season_stats", lambda s: _fake_stats())
    out = blend.blend_xg({"2025-26": 1.0}).set_index("code")

    assert out.loc[1, "xG"] == 10.0
    assert out.loc[1, "xAG"] == 2.0
    assert out.loc[1, "s90"] == 38.0
    assert out.loc[2, "s90"] == 19.0


def test_weighted_blend_sums(monkeypatch):
    """Two seasons combine as weighted sums of totals."""
    monkeypatch.setattr(blend, "load_season_stats", lambda s: _fake_stats())
    out = blend.blend_xg({"cur": 1.0, "prev": 0.5}).set_index("code")

    # code 1: xG = 10*1.0 + 10*0.5 = 15; s90 = (3420 + 0.5*3420)/90 = 57
    assert out.loc[1, "xG"] == 15.0
    assert out.loc[1, "s90"] == 57.0
