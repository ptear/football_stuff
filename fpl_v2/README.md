# fpl_v2

A clean, modular rebuild of the season-long FPL squad optimiser. Builds a per-player
expected-points model from xG data and solves an integer program for the best squad +
captain under budget / position / club / formation constraints.

Rewrite of `../fpl/simplex.ipynb`, dropping FBref (no longer available) and the fragile
fuzzy-name-matching + off-screen spreadsheet cleaning it relied on.

## Data sources

Everything except team match xG comes from the **official FPL API**
(`fantasy.premierleague.com/api/bootstrap-static`):

- **Player xG / xAG / minutes** — `expected_goals`, `expected_assists` (per element).
- **Price / club / position** — `now_cost`, `team`, `element_type`.
- **Availability & set-piece order** — `status`, `penalties_order`, etc.
- **Team defensive strength** — real per-match team xG conceded, via `soccerdata`'s
  Understat reader (see `sources_understat_match.py`); falls back to FPL's own
  season-total `expected_goals_conceded` when `config.DEFENSE_USE_UNDERSTAT` is off.
- **Appearance points** — real per-fixture minutes from vaastav's `merged_gw.csv`
  (see `appearances.py`), summed into last season's actual appearance-points total.
- **Bonus points** — last season's actual `bonus` total from vaastav (see `bonus.py`),
  carried forward as-is; not modelled, since real bonus comes from a proprietary BPS
  ranking we don't have the inputs to reproduce.

Because player xG *and* price/position/club come from the same FPL element, there is **no
name matching** — the old FBref↔FPL fuzzy join and manual cleaning are gone.

We **snapshot each season's `bootstrap-static`** to `data/raw/` (see `cache.snapshot_bootstrap`)
so we accumulate our own multi-season history rather than depending on a third-party mirror.

### Known caveats / decisions

- **Team match-by-match xG (understat)**: a direct scrape doesn't work — Understat's
  team/league pages render client-side now (the data variables its own JS declares are
  never populated in the static HTML). `sources_understat_match.py` gets around this
  using the `soccerdata` package's Understat reader, which bypasses the site's bot
  detection with a TLS-fingerprint client rather than a real browser. `soccerdata` does
  pull in `seleniumbase` as a hard dependency for its *other* readers (FBref, etc.) —
  unused here, but worth knowing if the dependency footprint looks heavier than expected.
  This is a bypass technique, not an official API, so it could break if Understat
  changes its bot defenses again.
- **Clean sheets and the goals-conceded penalty are threshold counts, not a probability
  model**: `defense.py` counts, per team, how many real matches had xG conceded below
  `config.CLEAN_SHEET_XGA_THRESHOLD` (clean sheet) or above
  `config.BAD_DEFENSIVE_GAME_XGA_THRESHOLD` (a "bad defensive game", flat penalty
  regardless of how much higher — a 4-0 and a 6-0 both just count as one bad game), then
  projects that rate across `config.GAMES_PER_SEASON` games. Falls back to a Poisson
  estimate (`P(clean sheet) = exp(-xGA_per_game)`) from FPL's season-total
  `expected_goals_conceded` when `config.DEFENSE_USE_UNDERSTAT` is off (no goals-conceded
  penalty in that fallback path — it was never tracked before the per-match source).
  **The two thresholds (0.8 / 2.2) are retuned, not the naive 1.0 / 2.0** — a naive
  cutoff overstates both league-wide (a match sitting anywhere below the clean-sheet
  cutoff gets full weight regardless of how close it is: at `xGA=0.9`, true clean-sheet
  probability under Poisson is only ~41%). Retuned by grid search against every team's
  real 2025-26 outcomes (actual clean sheets; actual games with 3+ conceded), minimizing
  squared error across all 20 teams — see the comment above the constants in `config.py`
  for the numbers, and the sanity check below for the before/after evidence.
- **Appearance points are carried forward as last season's actual total, not
  reprojected** (`appearances.py`) — same treatment as `xG`/`xAG`. This assumes a
  player's role next season mirrors last season, which is deliberate: it's a
  reasonable prior until the first few games of the new season give evidence
  otherwise (a transfer, a new #1 keeper, an injury-enforced change in pecking
  order). Minutes are summed **per fixture** (not per season-total ÷ 60, which would
  overcount — e.g. three 20-minute sub appearances summing to the same total minutes
  as one 60-minute start earn very different real points), so double gameweeks are
  handled correctly for free.
- **Bonus points are carried forward as last season's actual total, not modelled**
  (`bonus.py`) — same "carry forward as-is" treatment as appearance points, for the
  same reason: we don't have the BPS inputs (tackles won, chances created, etc.) to
  reproduce FPL's proprietary top-3-per-match ranking. Bonus skews toward goal
  involvements, so this term lifts forwards/attacking mids more than defenders.
- **Penalty bonus is OFF by default** (`config.APPLY_PENALTY_BONUS`). FPL `expected_goals`
  already includes penalties, so v1's additive bonus would double-count.
- **Promoted teams excluded** — clubs with < `PROMOTED_MIN_MINUTES` prior-season minutes.
- **Preseason hybrid**: the live API currently serves next season's prices/teams with last
  season's final xG in one payload — ideal for planning, but the xG resets when GW1 nears,
  which is why the snapshot matters.

### Sanity check: xPoints vs real `total_points`

Before the threshold retuning above, Arsenal's historically dominant defense (33 real
xGA, the league's most bad-game-free season) got so much clean-sheet credit that the
goalkeeper (Raya, real 162 points last season) out-ranked every outfield player and won
the optimiser's captaincy — a real calibration bug, not a coding one. Checking each
player's projected `xPoints` against their actual 2025-26 `total_points` caught it:

| Player | xPoints (before) | xPoints (after retuning + bonus) | Real `total_points` |
|---|---|---|---|
| Haaland | 178.0 | 221.0 | 239 |
| B.Fernandes | 180.4 | 218.7 | 235 |
| Gabriel | 191.8 | 209.0 | 209 |
| Virgil | 191.9 | 198.9 | 175 |
| Senesi | 179.7 | 188.9 | 175 |
| Raya | 192.3 | 187.7 | 162 |
| Guéhi | 177.9 | 174.4 | 179 |

Before: Raya's projection (192.3) exceeded his own real total by 30 points and topped
elite attackers who scored far more in reality (Haaland real 239, projected only 178).
After retuning the clean-sheet/bad-game thresholds and adding bonus points (which skews
toward goal involvements — see below), the ordering lines up with reality much more
closely, and **the optimiser's captain changes from Raya to Haaland**, as it should. This
isn't an exact match by design — `xPoints` is a forward-looking projection for next
season, not a reproduction of last season's actual (bonus-affected, luck-affected) total
— but the gap shouldn't be this lopsided, and now it isn't.

## Layout

```
config.py            tunables: scoring weights, formations+budgets, blend weights, flags
cache.py             fetch-or-load + dated bootstrap snapshots
sources_fpl.py       official FPL API -> tidy frames
sources_understat_match.py  per-match team xG for/against (via soccerdata)
sources_vaastav.py   defensive-contribution stats + per-fixture minutes (preseason API wipes them)
blend.py             multi-season xG baseline (default: last season only)
players.py           player feature table (identity + blended xG), keyed on `code`
penalties.py         data-driven pen-taker bonus (off by default)
overrides.py         explicit, version-controlled manual overrides
defense.py           team expected clean sheets + bad defensive games (xClean, xBadGames)
defcon.py            expected defensive-contribution points (+ transfer adjustment)
appearances.py       expected appearance points (last season's actual, carried forward as-is)
bonus.py             expected bonus points (last season's actual, carried forward as-is)
goalkeepers.py       GK xPoints model (also folded into the squad pool)
xpoints.py           xPoints = xG*g + xAG*a + xClean*c*(s90/38) - xBadGames*p*(s90/38) + defcon + appearance + bonus
optimize.py          PuLP squad optimiser: full XI (GK+10), budget, club<=3, captain
pipeline.py          end-to-end orchestration
notebooks/driver.ipynb   thin driver: run + inspect
tests/               pytest unit tests
```

### Goalkeepers (`goalkeepers.py`)

GK xPoints = saves/3 + clean-sheet term − bad-defensive-game term + appearance points
+ bonus points. Captures the save-volume signal: a keeper facing many low-danger shots
scores on saves *and* clean sheets. The clean-sheet, goals-conceded, appearance and
bonus terms all use the same `xClean` / `xBadGames` / `expected_appearance_points` /
`expected_bonus_points` signals as the outfield model (see the xPoints formula below)
— no separate GK-specific calculation, so GK and outfield xPoints stay on one scale.

The GK is **folded into the squad optimiser** — `pipeline.run()` picks a full XI
(1 GK + 10 outfield) under one budget (`config.SQUAD_BUDGET`, the XI budget; the rest
funds the bench), so the max-3-per-club cap counts the keeper. For a standalone view:

```python
from fpl_v2 import goalkeepers
goalkeepers.rank().head(10)
```

### xPoints formula

`data/processed/forecast.csv` has one row per player; the columns feed the formula
(`xpoints.py`) directly:

```
xPoints = xG * POINTS_FOR_GOAL[position]
        + xAG * POINTS_FOR_ASSIST
        + xClean * POINTS_FOR_CLEAN[position] * (s90 / GAMES_PER_SEASON)
        - xBadGames * POINTS_FOR_CONCEDED[position] * (s90 / GAMES_PER_SEASON)
        + expected_defcon_points
        + expected_appearance_points
        + expected_bonus_points
```

- `xG`, `xAG` — season expected goals / assists (from `blend.py`, defaults to last
  season's FPL `expected_goals` / `expected_assists`).
- `xClean` — the player's *club's* expected clean sheets over the season: a count of
  real matches with team xG conceded below `config.CLEAN_SHEET_XGA_THRESHOLD`,
  projected across a full season (from `defense.py`).
- `xBadGames` — the club's expected "bad defensive games": a count of real matches
  with team xG conceded above `config.BAD_DEFENSIVE_GAME_XGA_THRESHOLD`, flat per
  match no matter how much higher (a 4-0 and a 6-0 both count once) — a threshold-count
  approximation of FPL's real "-1 per 2 goals conceded" rule, using process (xG) rather
  than the noisier final score. `POINTS_FOR_CONCEDED` is 0 for MID/FWD, so the term
  only bites for GK/DEF, matching the real rule's scope.
  Both `xClean` and `xBadGames` are scaled down by `s90 / GAMES_PER_SEASON` so a
  part-season player isn't credited with (or docked for) a full season of them.
- `s90` — expected 90s played this season.
- `expected_defcon_points`, `expected_appearance_points`, `expected_bonus_points` —
  already expressed in points, not a rate (from `defcon.py` / `appearances.py` /
  `bonus.py` respectively); added as-is, not scaled by `s90 / GAMES_PER_SEASON` again.
  The latter two in particular are just last season's real totals carried forward
  unchanged (see the caveats above) — neither is derived from `s90` at all.
- `POINTS_FOR_GOAL`, `POINTS_FOR_CLEAN`, `POINTS_FOR_CONCEDED`, `POINTS_FOR_ASSIST`,
  `GAMES_PER_SEASON` — from `config.py`; the first three are per-position dicts
  (`{"GK": 6, "DEF": 6, "MID": 5, "FWD": 4}`, `{"GK": 4, "DEF": 4, "MID": 1, "FWD": 0}`,
  `{"GK": 1, "DEF": 1, "MID": 0, "FWD": 0}`), the rest are scalars
  (`POINTS_FOR_ASSIST = 3`, `GAMES_PER_SEASON = 38`).

Worked example — Gabriel, the current #1 defender (`position=DEF`, so goal weight 6,
clean weight 4, conceded weight 1):

```
xPoints = 2.94*6 + 1.75*3 + 22.0*4*(30.56/38) - 3.0*1*(30.56/38) + 25.74 + 62.0 + 30.0
        = 17.64  + 5.25   + 70.76                - 2.41            + 25.74 + 62.0 + 30.0
        = 208.98
```

`xpoints.breakdown()` computes these same seven terms as their own columns
(`goal_points`, `assist_points`, `clean_points`, `conceded_points`, `defcon_points`,
`appearance_points`, `bonus_points`, summing to `xPoints`) — used by the defender
xPoints-breakdown chart in `notebooks/defender_points_breakdown.ipynb`, but not
currently persisted to `forecast.csv` (only `pipeline.run(save=True)`'s output
columns are).

### Defensive contribution (`defcon.py`)

FPL 2025-26 DefCon points (DEF: CBIT ≥ 10/match; MID/FWD: CBIT+recoveries ≥ 12),
estimated from season totals via a Poisson-threshold on the per-90 rate. Sourced
from vaastav (the preseason official API zeroes these fields).

**Transfers:** a mover's rate is scaled by `intensity_new / intensity_old`, where a
club's per-slot defensive intensity (actions per outfield-90) is a stable style
trait — e.g. Palace (8.1/90) defends more than Chelsea (7.0/90), so a Palace→Chelsea
mover scales ×0.86. We do *not* net the player out of his old club (the slot gets
refilled, not vacated). Every mover is flagged (`is_mover`) for manual review, since
one season can't separate player propensity from team system — that needs multi-season
data (a future extension). Toggle via `pipeline.run(..., defensive_contribution=False)`.

## Usage

```python
from fpl_v2 import pipeline

forecast, squad = pipeline.run(save=True)   # refresh=True to re-pull live data
squad.formation, squad.total_cost / 10, squad.captain["web_name"]
forecast.sort_values("xPoints", ascending=False).head(20)
```

Config-drive everything else: edit scoring in `config.POINTS_*`, formations in
`config.FORMATIONS` (including "non-nailed" partial-budget variants), blend across seasons
via `config.BLEND_WEIGHTS`, and one-off fixes in `overrides.OVERRIDES`.

## Tests

```
uv run pytest fpl_v2/tests -q
```

Runs from the repo-root shared `.venv`.
