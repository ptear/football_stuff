"""Explicit, version-controlled manual overrides.

Replaces v1's off-screen clipboard "cleaning" and the scattered inline edits
(`df.loc[... == 'Haaland', 'xG'] = 38`, `Cost = 76`, ...). Each override states what
it changes and why, is applied deterministically, and shows up in code review.

Add entries to OVERRIDES. Match a player by `code` (stable across seasons, preferred)
or `web_name`. `set` maps feature-table columns to new values. Applied after the xG
baseline is built, before xPoints.

Example:
    {"code": 223094, "set": {"xG": 38.0}, "why": "expected to outperform last season"}
"""

import pandas as pd

# List of override records. Empty by default so nothing is silently altered.
OVERRIDES: list[dict] = [
    # {"web_name": "Haaland", "set": {"xG": 38.0}, "why": "..."},
]


def apply(df: pd.DataFrame) -> pd.DataFrame:
    """Return `df` with every override in OVERRIDES applied (on a copy).

    Args:
        df: player feature table.

    Raises:
        KeyError: if an override matches no player (typo guard) or targets a column
            that doesn't exist.
    """
    df = df.copy()
    for ov in OVERRIDES:
        if "code" in ov:
            mask = df["code"] == ov["code"]
            ident = f"code={ov['code']}"
        else:
            mask = df["web_name"] == ov["web_name"]
            ident = f"web_name={ov['web_name']!r}"
        if not mask.any():
            raise KeyError(f"override matched no player: {ident}")
        for col, val in ov["set"].items():
            if col not in df.columns:
                raise KeyError(f"override targets unknown column {col!r} ({ident})")
            df.loc[mask, col] = val
    return df
