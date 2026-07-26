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
- **Team defensive strength** — `expected_goals_conceded` (→ expected clean sheets).

Because player xG *and* price/position/club come from the same FPL element, there is **no
name matching** — the old FBref↔FPL fuzzy join and manual cleaning are gone.

We **snapshot each season's `bootstrap-static`** to `data/raw/` (see `cache.snapshot_bootstrap`)
so we accumulate our own multi-season history rather than depending on a third-party mirror.

### Known caveats / decisions

- **Team match-by-match xG (understat)** is stubbed. Understat now renders data via JS
  (no embedded JSON, no reachable endpoint), so a live scrape needs a headless browser.
  Until that's decided, `defense.py` derives expected clean sheets from FPL
  `expected_goals_conceded` (Poisson: `P(clean sheet) = exp(-xGA_per_game)`).
- **Penalty bonus is OFF by default** (`config.APPLY_PENALTY_BONUS`). FPL `expected_goals`
  already includes penalties, so v1's additive bonus would double-count.
- **Promoted teams excluded** — clubs with < `PROMOTED_MIN_MINUTES` prior-season minutes.
- **Preseason hybrid**: the live API currently serves next season's prices/teams with last
  season's final xG in one payload — ideal for planning, but the xG resets when GW1 nears,
  which is why the snapshot matters.

## Layout

```
config.py            tunables: scoring weights, formations+budgets, blend weights, flags
cache.py             fetch-or-load + dated bootstrap snapshots
sources_fpl.py       official FPL API -> tidy frames
sources_understat.py team season xGA (manual league-table CSV)
sources_vaastav.py   defensive-contribution stats (preseason API wipes them)
blend.py             multi-season xG baseline (default: last season only)
players.py           player feature table (identity + blended xG), keyed on `code`
penalties.py         data-driven pen-taker bonus (off by default)
overrides.py         explicit, version-controlled manual overrides
defense.py           team expected clean sheets (xClean)
defcon.py            expected defensive-contribution points (+ transfer adjustment)
goalkeepers.py       GK xPoints model (also folded into the squad pool)
xpoints.py           xPoints = xG*g + xAG*a + xClean*c*(s90/38) + defcon
optimize.py          PuLP squad optimiser: full XI (GK+10), budget, club<=3, captain
pipeline.py          end-to-end orchestration
notebooks/driver.ipynb   thin driver: run + inspect
tests/               pytest unit tests
```

### Goalkeepers (`goalkeepers.py`)

GK xPoints = saves/3 + clean sheets − goals_conceded/2 (appearance points omitted to
match the outfield scale). Captures the save-volume signal: a keeper facing many
low-danger shots scores on saves *and* clean sheets.

The GK is **folded into the squad optimiser** — `pipeline.run()` picks a full XI
(1 GK + 10 outfield) under one budget (`config.SQUAD_BUDGET`, the XI budget; the rest
funds the bench), so the max-3-per-club cap counts the keeper. For a standalone view:

```python
from fpl_v2 import goalkeepers
goalkeepers.rank().head(10)
```

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
