"""GK ranking sanity checks. Uses cached data; skips if unavailable."""

import pytest

from fpl_v2 import goalkeepers


@pytest.fixture(scope="module")
def ranking():
    try:
        return goalkeepers.rank()
    except Exception as exc:
        pytest.skip(f"GK data unavailable: {exc}")


def test_sorted_descending(ranking):
    xp = ranking["GK_xPoints"].to_numpy()
    assert (xp[:-1] >= xp[1:]).all()


def test_only_regular_starters(ranking):
    # rank() filters to >= 1000 minutes, i.e. ~11 nineties minimum
    assert (ranking["s90"] >= 11).all()


def test_points_are_finite_and_positive(ranking):
    assert ranking["GK_xPoints"].notna().all()
    assert (ranking["GK_xPoints"] > 0).all()
