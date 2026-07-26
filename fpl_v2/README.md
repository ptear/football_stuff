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
sources_understat.py team match xG (stubbed; needs headless browser)
blend.py             multi-season xG baseline (default: last season only)
players.py           player feature table (identity + blended xG), keyed on `code`
penalties.py         data-driven pen-taker bonus (off by default)
overrides.py         explicit, version-controlled manual overrides
defense.py           team expected clean sheets (xClean)
xpoints.py           xPoints = xG*g + xAG*a + xClean*c*(s90/38)
optimize.py          PuLP squad optimiser (formations, budget, club<=3, captain)
pipeline.py          end-to-end orchestration
notebooks/driver.ipynb   thin driver: run + inspect
tests/               pytest unit tests
```

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
