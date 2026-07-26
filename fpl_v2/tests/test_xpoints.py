import pandas as pd

from fpl_v2 import xpoints


def test_xpoints_formula():
    """xPoints matches the hand-computed value for each position."""
    df = pd.DataFrame([
        {"code": 1, "position": "FWD", "xG": 10, "xAG": 5, "s90": 38, "team_name": "A"},
        {"code": 2, "position": "DEF", "xG": 2, "xAG": 1, "s90": 19, "team_name": "A"},
        {"code": 3, "position": "MID", "xG": 8, "xAG": 4, "s90": 38, "team_name": "B"},
    ])
    team_rates = pd.DataFrame({"team_name": ["A", "B"], "xClean": [10.0, 6.0], "xBadGames": [5.0, 2.0]})

    out = xpoints.compute(df, team_rates).set_index("code")["xPoints"]

    # FWD: 10*4 + 5*3 + 10*0*(38/38) - 5*0*(38/38) = 55
    assert out[1] == 55
    # DEF: 2*6 + 1*3 + 10*4*(19/38) - 5*1*(19/38) = 12 + 3 + 20 - 2.5 = 32.5
    assert out[2] == 32.5
    # MID: 8*5 + 4*3 + 6*1*(38/38) - 2*0*(38/38) = 40 + 12 + 6 = 58
    assert out[3] == 58


def test_missing_team_rates_default_to_zero():
    """A team with no rates row contributes 0 to clean-sheet/conceded terms, no NaN."""
    df = pd.DataFrame([
        {"code": 1, "position": "DEF", "xG": 0, "xAG": 0, "s90": 38, "team_name": "Z"},
    ])
    out = xpoints.compute(df, pd.DataFrame({"team_name": [], "xClean": [], "xBadGames": []}))
    assert out.loc[0, "xClean"] == 0
    assert out.loc[0, "xBadGames"] == 0
    assert out.loc[0, "xPoints"] == 0


def test_appearance_points_pass_through():
    """expected_appearance_points (already points, not a rate) is added as-is if present,
    and defaults to 0 (no NaN) if the column is absent entirely."""
    team_rates = pd.DataFrame({"team_name": ["A"], "xClean": [0.0], "xBadGames": [0.0]})

    with_appearances = pd.DataFrame([
        {"code": 1, "position": "MID", "xG": 0, "xAG": 0, "s90": 0, "team_name": "A",
         "expected_appearance_points": 40},
    ])
    out = xpoints.compute(with_appearances, team_rates)
    assert out.loc[0, "appearance_points"] == 40
    assert out.loc[0, "xPoints"] == 40

    without_appearances = pd.DataFrame([
        {"code": 1, "position": "MID", "xG": 0, "xAG": 0, "s90": 0, "team_name": "A"},
    ])
    out = xpoints.compute(without_appearances, team_rates)
    assert out.loc[0, "appearance_points"] == 0
    assert out.loc[0, "xPoints"] == 0


def test_bonus_points_pass_through():
    """expected_bonus_points (already points, not a rate) is added as-is if present,
    and defaults to 0 (no NaN) if the column is absent entirely."""
    team_rates = pd.DataFrame({"team_name": ["A"], "xClean": [0.0], "xBadGames": [0.0]})

    with_bonus = pd.DataFrame([
        {"code": 1, "position": "FWD", "xG": 0, "xAG": 0, "s90": 0, "team_name": "A",
         "expected_bonus_points": 43},
    ])
    out = xpoints.compute(with_bonus, team_rates)
    assert out.loc[0, "bonus_points"] == 43
    assert out.loc[0, "xPoints"] == 43

    without_bonus = pd.DataFrame([
        {"code": 1, "position": "FWD", "xG": 0, "xAG": 0, "s90": 0, "team_name": "A"},
    ])
    out = xpoints.compute(without_bonus, team_rates)
    assert out.loc[0, "bonus_points"] == 0
    assert out.loc[0, "xPoints"] == 0
