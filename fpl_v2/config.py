"""Central configuration for fpl_v2.

Every tunable the model uses lives here so the modules stay free of magic numbers.
All monetary values are in FPL tenths (e.g. 55 == £5.5m), matching the API's `now_cost`.
"""

from pathlib import Path

# --- Paths -------------------------------------------------------------------
PACKAGE_DIR = Path(__file__).resolve().parent
RAW_DIR = PACKAGE_DIR / "data" / "raw"
PROCESSED_DIR = PACKAGE_DIR / "data" / "processed"

# --- Season ------------------------------------------------------------------
# Label for the season whose data the live API currently serves. Used to name
# snapshots so we accumulate our own history (see cache.snapshot_bootstrap).
CURRENT_SEASON = "2025-26"           # season the xG finals belong to
UPCOMING_SEASON = "2026-27"          # season the prices/teams belong to

# --- Sources -----------------------------------------------------------------
FPL_API_BASE = "https://fantasy.premierleague.com/api"
UNDERSTAT_LEAGUE = "EPL"
UNDERSTAT_SEASON = "2025"             # understat labels a season by its start year (2025 == 2025/26)
# Manually downloaded understat league table (season aggregate, one row per team,
# semicolon-separated) placed in data/raw. Used for the defensive xGA signal.
UNDERSTAT_LEAGUE_CSV = "league-chemp.csv"
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fpl_v2/0.1)"}

# --- Position encoding (FPL element_type -> short code) ----------------------
POSITIONS = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

# --- Scoring rules -----------------------------------------------------------
# FPL points awarded per event, by position. Editable so the xPoints model can
# be re-pointed without touching xpoints.py.
POINTS_FOR_GOAL = {"GK": 6, "DEF": 6, "MID": 5, "FWD": 4}
POINTS_FOR_CLEAN = {"GK": 4, "DEF": 4, "MID": 1, "FWD": 0}
POINTS_FOR_ASSIST = 3                 # was hardcoded as *3 in v1; now configurable

# Number of league games used to prorate a season-long clean-sheet expectation.
GAMES_PER_SEASON = 38

# --- Penalty-taker bonus -----------------------------------------------------
# A nailed penalty taker earns extra xG on top of open-play npxG. Derived, not
# hardcoded per player: applied to whoever has penalties_order == 1 for their club.
#   base = mean penalties awarded per team per season (last 5 seasons)
#   top/bottom teams win ~top_bottom_diff more/fewer than the mean
#   each penalty is worth penalty_xg expected goals (Opta ~0.79)
PENALTY_SEASON_TOTALS = [99, 106, 81, 106, 92]   # league-wide pens per season, last 5
PENALTY_BASE_PER_TEAM = sum(PENALTY_SEASON_TOTALS) / 20 / len(PENALTY_SEASON_TOTALS)
PENALTY_TOP_BOTTOM_DIFF = 1.2
PENALTY_XG = 0.79
# v1 added this bonus because FBref npxG EXCLUDED penalties. FPL expected_goals is
# TOTAL xG (penalties already in it), so enabling the bonus double-counts for an
# established taker. Left off by default; enable only if you first strip realised
# penalty xG from the base, or to credit a newly-nailed taker.
APPLY_PENALTY_BONUS = False

# --- Multi-season blend ------------------------------------------------------
# Weight applied to each season snapshot when building the xG baseline. Default
# uses last season only, so the model runs with a single live snapshot and no
# history. Add older seasons (keys must match snapshot season labels) to blend.
BLEND_WEIGHTS = {CURRENT_SEASON: 1.0}

# --- Optimizer ---------------------------------------------------------------
SQUAD_SIZE = 10                       # outfield players selected (GK handled separately)
MAX_PER_CLUB = 3

# Formation -> per-position caps + budget (FPL tenths). Budget excludes the GK
# and bench allowance, matching v1's £78.5m for the 10 starting outfielders.
FORMATIONS = {
    "3-5-2": {"DEF": 3, "MID": 5, "FWD": 2, "budget": 785},
    "3-4-3": {"DEF": 3, "MID": 4, "FWD": 3, "budget": 785},
    "4-4-2": {"DEF": 4, "MID": 4, "FWD": 2, "budget": 785},
    "4-5-1": {"DEF": 4, "MID": 5, "FWD": 1, "budget": 785},
}

# --- Flags -------------------------------------------------------------------
EXCLUDE_PROMOTED = True               # drop players whose club has no prior-season PL xG
# A club is treated as promoted/new if its whole squad logged fewer than this many
# prior-season PL minutes. Established clubs sit ~30k+, newcomers under ~1k, so any
# value in the gap works.
PROMOTED_MIN_MINUTES = 5000
EXCLUDE_POSITIONS = {"GK"}            # v1 optimised outfield only
DEFENSE_USE_UNDERSTAT = True          # False -> skip scrape, use FPL strength_defence only

# --- Team name map (understat -> FPL) ----------------------------------------
# Understat spells clubs out in full; the FPL API abbreviates. Only clubs whose
# names differ need an entry. Extend per season as promoted teams change.
UNDERSTAT_TO_FPL_TEAM = {
    "Manchester City": "Man City",
    "Manchester United": "Man Utd",
    "Newcastle United": "Newcastle",
    "Tottenham": "Spurs",
    "Wolverhampton Wanderers": "Wolves",
    "Nottingham Forest": "Nott'm Forest",
    "Sheffield United": "Sheffield Utd",
}
