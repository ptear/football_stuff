import pandas as pd

from fpl_v2 import optimize


def _pool():
    """Small pool: two options per position; higher-xP option is cheap enough."""
    return pd.DataFrame([
        {"code": 1, "web_name": "d_hi", "position": "DEF", "cost": 50, "team_name": "A", "xPoints": 30},
        {"code": 2, "web_name": "d_lo", "position": "DEF", "cost": 40, "team_name": "B", "xPoints": 10},
        {"code": 3, "web_name": "m_hi", "position": "MID", "cost": 60, "team_name": "C", "xPoints": 50},
        {"code": 4, "web_name": "m_lo", "position": "MID", "cost": 40, "team_name": "D", "xPoints": 20},
        {"code": 5, "web_name": "f_hi", "position": "FWD", "cost": 70, "team_name": "E", "xPoints": 40},
        {"code": 6, "web_name": "f_lo", "position": "FWD", "cost": 45, "team_name": "F", "xPoints": 15},
    ])


FORMATION = {"one-each": {"DEF": 1, "MID": 1, "FWD": 1, "budget": 500}}


def test_picks_highest_xpoints_and_captains_the_best():
    r = optimize.optimize(_pool(), formations=FORMATION, max_per_club=3)
    assert set(r.players["code"]) == {1, 3, 5}          # the three high-xP players
    assert r.captain_code == 3                          # m_hi, top xPoints
    assert r.total_cost == 180                          # 50 + 60 + 70
    assert r.total_xpoints == 30 + 50 + 40 + 50         # captain (m_hi) counted twice


def test_budget_forces_cheaper_pick():
    """A tight budget makes the expensive FWD infeasible, forcing f_lo."""
    tight = {"one-each": {"DEF": 1, "MID": 1, "FWD": 1, "budget": 155}}
    r = optimize.optimize(_pool(), formations=tight, max_per_club=3)
    assert 5 not in set(r.players["code"])              # f_hi (70) unaffordable here
    assert 6 in set(r.players["code"])
    assert r.total_cost <= 155


def test_club_cap_respected():
    """With every player on the same club and a cap of 1, only one can be picked."""
    pool = _pool()
    pool["team_name"] = "SAME"
    # Need 3 positions but max 1 per club -> infeasible -> ValueError.
    import pytest
    with pytest.raises(ValueError):
        optimize.optimize(pool, formations=FORMATION, max_per_club=1)
