"""
METAR / SPECI rule set based on:
  - ICAO Annex 3, Appendix 3 (Technical Specifications Related to
    Meteorological Observations and Reports)
  - WMO No. 782 (Aerodrome Reports and Forecasts, code form FM 15-XV METAR)

Each rule has a `ref` field so a flagged violation can be traced back to
the specific paragraph — keep this updated if you diff against the actual
Annex 3 / WMO 782 text, rather than trusting this as gospel.

This is a STARTER rule set covering the groups most likely to carry
transcription/coding errors. It is not a complete implementation of the
full code form (e.g. it does not yet handle RMK free text, full RVR
tendency logic for all runway configurations, or all present-weather
combinations exhaustively).
"""

import re

# Valid present-weather phenomena components (WMO 782 Table for ww)
WX_INTENSITY = r"[+-]?"
WX_DESCRIPTOR = r"(MI|BC|PR|DR|BL|SH|TS|FZ)?"
WX_PHENOMENA = (
    r"(DZ|RA|SN|SG|IC|PL|GR|GS|UP|"
    r"BR|FG|FU|VA|DU|SA|HZ|"
    r"PO|SQ|FC|SS|DS)+"
)
WX_GROUP_RE = re.compile(
    rf"^{WX_INTENSITY}{WX_DESCRIPTOR}{WX_PHENOMENA}$|^VC(TS|SH|FG|PO|DS|SS|FC)$"
)

RULES = [
    {
        "id": "wind_group",
        "ref": "Annex 3 App.3 §4.1 / WMO 782 FM15 Ddd ff Gfmfm",
        "pattern": re.compile(r"^(?P<dir>\d{3}|VRB)(?P<spd>\d{2,3})(G(?P<gust>\d{2,3}))?(?P<unit>KT|MPS)$"),
        "required": True,
        "check": lambda m: (
            None
            if m
            else "wind group missing or malformed — expected dddffGfmfmKT/MPS (e.g. 27008G18KT)"
        ),
    },
    {
        "id": "wind_gust_logic",
        "ref": "WMO 782 — gust must exceed mean speed",
        "cross_check": True,
    },
    {
        "id": "visibility_group",
        "ref": "Annex 3 App.3 §4.3",
        "pattern": re.compile(r"^(CAVOK|\d{4}|////|\d{1,2}SM)$"),
        "required": True,
        "check": lambda m: (
            None if m else "visibility group missing/malformed — expected 4-digit metres or CAVOK"
        ),
    },
    {
        "id": "temp_dewpoint_group",
        "ref": "Annex 3 App.3 §4.7",
        "pattern": re.compile(r"^(M?\d{2})/(M?\d{2})$"),
        "required": True,
        "check": lambda m: (
            None if m else "temperature/dewpoint group missing/malformed — expected TT/TdTd (e.g. 18/12 or M02/M05)"
        ),
    },
    {
        "id": "temp_ge_dewpoint",
        "ref": "Physical constraint — air temp must be >= dewpoint",
        "cross_check": True,
    },
    {
        "id": "qnh_group",
        "ref": "Annex 3 App.3 §4.8",
        "pattern": re.compile(r"^Q(?P<val>\d{4})$|^A(?P<inhg>\d{4})$"),
        "required": True,
        "check": lambda m: (
            None if m else "QNH group missing/malformed — expected Qpppp (hPa) or Apppp (inHg)"
        ),
    },
    {
        "id": "cloud_group",
        "ref": "Annex 3 App.3 §4.5",
        "pattern": re.compile(r"^(FEW|SCT|BKN|OVC)\d{3}(CB|TCU)?$|^(NSC|NCD|VV\d{3}|VV///)$"),
        "required": False,  # absent only valid if CAVOK
    },
    {
        "id": "cavok_excludes_cloud_wx",
        "ref": "Annex 3 App.3 §4.3 — CAVOK excludes cloud & weather groups",
        "cross_check": True,
    },
]


def check_wx_group(token: str) -> bool:
    """Validate a present-weather token against allowed intensity+descriptor+phenomena combos."""
    return bool(WX_GROUP_RE.match(token))
