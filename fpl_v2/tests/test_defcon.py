import numpy as np
import pandas as pd
from scipy.stats import poisson

from fpl_v2 import config, defcon


def _fake_vaastav():
    """Two teams: A defends twice as much as B (per outfield-90)."""
    return pd.DataFrame({
        "code": [1, 2, 3, 4],
        "element_type": [2, 3, 2, 3],
        "position": ["DEF", "MID", "DEF", "MID"],
        "minutes": [3420, 3420, 3420, 3420],
        "clearances_blocks_interceptions": [380, 300, 190, 150],
        "tackles": [0, 0, 0, 0],
        "recoveries": [0, 120, 0, 60],
        "old_team_name": ["A", "A", "B", "B"],
        "defensive_contribution": [0, 0, 0, 0],
    })


def test_team_intensity_ratio():
    inten = defcon.team_intensity(_fake_vaastav())
    # A total actions 800, B 400, equal minutes -> A twice B
    assert abs(inten["A"] / inten["B"] - 2.0) < 1e-9


def test_stayer_vs_mover_multiplier(monkeypatch):
    monkeypatch.setattr(defcon.sources_vaastav, "defensive_stats",
                        lambda season=None, refresh=False: _fake_vaastav())
    feature = pd.DataFrame({
        "code": [1, 3],
        "position": ["DEF", "DEF"],
        "team_name": ["A", "A"],   # player 3 moved B -> A
        "s90": [38.0, 38.0],
    })
    out = defcon.expected_defcon_points(feature).set_index("code")

    assert out.loc[1, "defcon_multiplier"] == 1.0 and not out.loc[1, "is_mover"]
    assert out.loc[3, "is_mover"]
    assert abs(out.loc[3, "defcon_multiplier"] - 2.0) < 1e-9   # intensity[A]/intensity[B]


def test_poisson_expected_points(monkeypatch):
    monkeypatch.setattr(defcon.sources_vaastav, "defensive_stats",
                        lambda season=None, refresh=False: _fake_vaastav())
    feature = pd.DataFrame({"code": [1], "position": ["DEF"], "team_name": ["A"], "s90": [38.0]})
    out = defcon.expected_defcon_points(feature).iloc[0]

    # player 1: CBIT rate = 380 / (3420/90) = 10.0 per 90, DEF threshold 10
    rate, thr, starts = 10.0, 10, 38.0
    expected = config.DEFCON_POINTS * (1 - poisson.cdf(thr - 1, rate)) * starts
    assert abs(out["expected_defcon_points"] - expected) < 1e-9
