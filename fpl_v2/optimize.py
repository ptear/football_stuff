"""Squad optimisation via integer programming.

Maximises total xPoints (captain counted twice) over each configured formation,
subject to budget, exact per-position shape, squad size, and max-per-club. Returns
the best formation's squad.

Players are keyed by the permanent `code`, so distinct players never collide (v1
keyed on surname, which did).
"""

from dataclasses import dataclass

import pandas as pd
import pulp

from fpl_v2 import config


@dataclass
class SquadResult:
    """Outcome of one optimisation run."""
    formation: str
    players: pd.DataFrame        # selected rows from the feature table
    captain_code: int
    total_cost: int              # FPL tenths
    total_xpoints: float         # objective value (includes captain's doubled xP)

    @property
    def captain(self) -> pd.Series:
        return self.players.set_index("code").loc[self.captain_code]


def _solve_formation(df: pd.DataFrame, name: str, spec: dict,
                     max_per_club: int) -> SquadResult | None:
    """Solve one formation; return its SquadResult or None if infeasible."""
    codes = df["code"].tolist()
    xp = dict(zip(df["code"], df["xPoints"]))
    cost = dict(zip(df["code"], df["cost"]))
    pos = dict(zip(df["code"], df["position"]))
    club = dict(zip(df["code"], df["team_name"]))
    squad_size = sum(spec[p] for p in ("DEF", "MID", "FWD"))

    prob = pulp.LpProblem(f"fpl_{name}", pulp.LpMaximize)
    x = pulp.LpVariable.dicts("x", codes, cat="Binary")   # selected
    c = pulp.LpVariable.dicts("c", codes, cat="Binary")   # captain

    # Objective: captain's xPoints counts twice.
    prob += pulp.lpSum(xp[i] * (x[i] + c[i]) for i in codes)

    prob += pulp.lpSum(cost[i] * x[i] for i in codes) <= spec["budget"]
    for p in ("DEF", "MID", "FWD"):
        prob += pulp.lpSum(x[i] for i in codes if pos[i] == p) == spec[p]
    prob += pulp.lpSum(x[i] for i in codes) == squad_size
    for cl in set(club.values()):
        prob += pulp.lpSum(x[i] for i in codes if club[i] == cl) <= max_per_club
    prob += pulp.lpSum(c[i] for i in codes) == 1          # exactly one captain
    for i in codes:
        prob += c[i] <= x[i]                              # captain must be selected

    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    if pulp.LpStatus[prob.status] != "Optimal":
        return None

    picked = [i for i in codes if x[i].value() == 1]
    captain = next(i for i in codes if c[i].value() == 1)
    players = df[df["code"].isin(picked)].copy()
    return SquadResult(
        formation=name,
        players=players,
        captain_code=captain,
        total_cost=int(players["cost"].sum()),
        total_xpoints=float(pulp.value(prob.objective)),
    )


def optimize(df: pd.DataFrame, formations: dict = None,
             max_per_club: int = config.MAX_PER_CLUB) -> SquadResult:
    """Return the best squad across all formations by total xPoints.

    Args:
        df: feature table with xPoints, cost, position, team_name, code.
        formations: {name: {DEF, MID, FWD, budget}}. Defaults to config.FORMATIONS.
        max_per_club: cap on players from any one club.

    Raises:
        ValueError: if no formation is feasible.
    """
    formations = formations or config.FORMATIONS
    results = [
        r for name, spec in formations.items()
        if (r := _solve_formation(df, name, spec, max_per_club)) is not None
    ]
    if not results:
        raise ValueError("no feasible squad for any formation")
    return max(results, key=lambda r: r.total_xpoints)
