"""Feature-table invariants. Uses cached live data; skips if none is available."""

import pytest

from fpl_v2 import config, players


@pytest.fixture(scope="module")
def table():
    try:
        return players.build()
    except Exception as exc:  # no cached data and no network
        pytest.skip(f"player data unavailable: {exc}")


def test_codes_unique(table):
    assert table["code"].is_unique


def test_excluded_positions_absent(table):
    assert not table["position"].isin(config.EXCLUDE_POSITIONS).any()


def test_promoted_teams_absent(table):
    if config.EXCLUDE_PROMOTED:
        promoted = players._promoted_teams()
        assert not table["team_name"].isin(promoted).any()


def test_core_columns_populated(table):
    assert table[["cost", "xG", "xAG", "s90", "team_name"]].notna().all().all()
