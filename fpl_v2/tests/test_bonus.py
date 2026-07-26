import pandas as pd

from fpl_v2 import bonus


def test_expected_bonus_points(monkeypatch):
    monkeypatch.setattr(bonus.sources_vaastav, "bonus_points",
                        lambda season=None, refresh=False: pd.DataFrame({
                            "code": [1, 2], "bonus": [43, 0],
                        }))

    feature = pd.DataFrame({"code": [1, 2, 3]})  # 3 has no bonus history at all
    out = bonus.expected_bonus_points(feature).set_index("code")

    assert out.loc[1, "expected_bonus_points"] == 43
    assert out.loc[2, "expected_bonus_points"] == 0
    assert out.loc[3, "expected_bonus_points"] == 0   # missing -> 0, no NaN
