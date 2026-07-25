"""
Validates a raw METAR string against the rule set in rules.py.

Returns a dict:
{
  "raw": "...",
  "station": "VNKT",
  "valid": bool,
  "errors": [ {"id": ..., "ref": ..., "message": ...}, ... ],
  "significant": [ {"code": "TS", "message": "..."}, ... ]  # siren triggers
}

Note: this is a starter implementation covering the highest-value checks
(wind, visibility, temp/dewpoint, QNH, cloud, present weather, gust logic,
temp>=dewpoint, CAVOK exclusivity). Extend `rules.py` and the SIGNIFICANT_WX
list below as you formalize more of Annex 3 App.3 / WMO 782.
"""

import re
from rules import RULES, check_wx_group

# Phenomena that should trigger an audible/visual alert regardless of
# whether the group is syntactically valid — these are operationally
# significant per SIGMET-adjacent criteria (TS, severe icing/turb mentions,
# wind shear, volcanic ash, sand/duststorm).
SIGNIFICANT_WX_CODES = {
    "TS": "Thunderstorm",
    "+TSRA": "Heavy thunderstorm with rain",
    "GR": "Hail",
    "FC": "Funnel cloud / tornado",
    "SS": "Sandstorm",
    "DS": "Duststorm",
    "VA": "Volcanic ash",
    "SQ": "Squall",
}
SIGNIFICANT_TOKENS = {"WS", "WSHFT"}  # wind shear related


def tokenize(raw: str) -> list[str]:
    return raw.strip().split()


def find_group(tokens: list[str], pattern: re.Pattern) -> tuple[str | None, re.Match | None]:
    for t in tokens:
        m = pattern.match(t)
        if m:
            return t, m
    return None, None


def validate(raw: str, station_hint: str | None = None) -> dict:
    tokens = tokenize(raw)
    errors: list[dict] = []
    significant: list[dict] = []

    station = tokens[1] if len(tokens) > 1 and re.match(r"^[A-Z]{4}$", tokens[1]) else station_hint
    is_cavok = "CAVOK" in tokens

    matches: dict[str, re.Match | None] = {}

    for rule in RULES:
        if rule.get("cross_check"):
            continue
        token, m = find_group(tokens, rule["pattern"])
        matches[rule["id"]] = m
        if rule["required"] and not m and not (rule["id"] == "cloud_group" and is_cavok):
            errors.append({
                "id": rule["id"],
                "ref": rule["ref"],
                "message": rule["check"](m) if "check" in rule else f"{rule['id']} missing/malformed",
            })

    # --- cross-field checks ---
    wind_m = matches.get("wind_group")
    if wind_m and wind_m.group("gust"):
        spd, gust = int(wind_m.group("spd")), int(wind_m.group("gust"))
        if gust <= spd:
            errors.append({
                "id": "wind_gust_logic",
                "ref": "WMO 782 — gust must exceed mean speed",
                "message": f"gust ({gust}) is not greater than mean wind speed ({spd})",
            })

    td_m = matches.get("temp_dewpoint_group")
    if td_m:
        def to_c(s: str) -> int:
            return -int(s[1:]) if s.startswith("M") else int(s)
        t, td = to_c(td_m.group(1)), to_c(td_m.group(2))
        if td > t:
            errors.append({
                "id": "temp_ge_dewpoint",
                "ref": "Physical constraint — dewpoint cannot exceed air temperature",
                "message": f"dewpoint ({td}C) exceeds air temperature ({t}C)",
            })

    if is_cavok:
        cloud_present = any(re.match(RULES_BY_ID["cloud_group"]["pattern"], t) for t in tokens if t not in ("CAVOK",))
        wx_present = any(check_wx_group(t) for t in tokens)
        if cloud_present or wx_present:
            errors.append({
                "id": "cavok_excludes_cloud_wx",
                "ref": "Annex 3 App.3 §4.3",
                "message": "CAVOK reported alongside cloud and/or weather groups — mutually exclusive",
            })

    # --- present weather / significant phenomena scan ---
    for t in tokens:
        stripped = t.lstrip("+-")
        base = stripped[2:] if stripped[:2] == "VC" else stripped
        if check_wx_group(t):
            for code, label in SIGNIFICANT_WX_CODES.items():
                if code.lstrip("+") in t:
                    significant.append({"code": code, "message": f"{label} reported"})
        if t in SIGNIFICANT_TOKENS or t.startswith("WS"):
            significant.append({"code": t, "message": "Wind shear reported"})

    return {
        "raw": raw,
        "station": station,
        "valid": len(errors) == 0,
        "errors": errors,
        "significant": significant,
    }


RULES_BY_ID = {r["id"]: r for r in RULES}
