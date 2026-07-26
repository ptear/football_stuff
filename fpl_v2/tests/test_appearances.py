import pandas as pd

from fpl_v2 import appearances


def _fake_fixtures():
    """Player 1: a 90-min start and a 90-min start (2 full apps, both GWs).
    Player 2: a 90-min start then subbed off at 45 (1 full, 1 short app).
    Player 3: never came on (0 minutes, no points)."""
    return pd.DataFrame({
        "code": [1, 1, 2, 2, 3],
        "minutes": [90, 90, 90, 45, 0],
    })


def test_expected_appearance_points(monkeypatch):
    monkeypatch.setattr(appearances.sources_vaastav, "fixture_minutes",
                        lambda season=None, refresh=False: _fake_fixtures())

    feature = pd.DataFrame({"code": [1, 2, 3, 4]})  # 4 has no fixture history at all
    out = appearances.expected_appearance_points(feature).set_index("code")

    assert out.loc[1, "expected_appearance_points"] == 4   # 2 + 2
    assert out.loc[2, "expected_appearance_points"] == 3    # 2 + 1
    assert out.loc[3, "expected_appearance_points"] == 0
    assert out.loc[4, "expected_appearance_points"] == 0     # missing -> 0, no NaN
