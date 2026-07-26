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


FORMATION = {"one-each": {"DEF": 1, "MID": 1, "FWD": 1}}


def test_picks_highest_xpoints_and_captains_the_best():
    r = optimize.optimize(_pool(), formations=FORMATION, budget=500, max_per_club=3)
    assert set(r.players["code"]) == {1, 3, 5}          # the three high-xP players
    assert r.captain_code == 3                          # m_hi, top xPoints
    assert r.total_cost == 180                          # 50 + 60 + 70
    assert r.total_xpoints == 30 + 50 + 40 + 50         # captain (m_hi) counted twice


def test_budget_forces_cheaper_pick():
    """A tight budget makes the expensive FWD infeasible, forcing f_lo."""
    r = optimize.optimize(_pool(), formations=FORMATION, budget=155, max_per_club=3)
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
        optimize.optimize(pool, formations=FORMATION, budget=500, max_per_club=1)


def test_gk_counts_toward_club_cap():
    """A GK shares the per-club cap with outfielders in the same joint optimisation."""
    pool = _pool()
    # Put the two best outfielders (m_hi=50, f_hi=40) on club ARS, plus an ARS GK.
    pool.loc[pool["code"].isin([3, 5]), "team_name"] = "ARS"
    gk = pd.DataFrame([
        {"code": 7, "web_name": "g_ars", "position": "GK", "cost": 45, "team_name": "ARS", "xPoints": 60},
        {"code": 8, "web_name": "g_oth", "position": "GK", "cost": 45, "team_name": "OTH", "xPoints": 30},
    ])
    pool = pd.concat([pool, gk], ignore_index=True)
    formation = {"gk-plus": {"GK": 1, "DEF": 1, "MID": 1, "FWD": 1}}

    r = optimize.optimize(pool, formations=formation, budget=500, max_per_club=2)
    picked = set(r.players["code"])
    ars = r.players[r.players["team_name"] == "ARS"]
    assert len(ars) <= 2                       # GK + outfielders from ARS obey the cap
    assert r.players[r.players["position"] == "GK"].shape[0] == 1
