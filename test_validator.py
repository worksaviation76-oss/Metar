from metar_validator import validate

cases = [
    "VNKT 251200Z 27008KT 9999 FEW030 22/12 Q1015 NOSIG",         # valid
    "VNKT 251200Z 27008G05KT 9999 FEW030 22/12 Q1015",             # gust <= speed (bad)
    "VNKT 251200Z 27008KT 9999 FEW030 12/22 Q1015",                # dewpoint > temp (bad)
    "VNKT 251200Z 27015G28KT 3000 +TSRA BKN010CB 24/23 Q1008",     # valid syntax, TS significant
    "VNKT 251200Z CAVOK BKN020 22/12 Q1015",                       # CAVOK + cloud (bad)
    "VNKT 251200Z VRB03KT CAVOK 22/12 Q1015",                      # valid, CAVOK clean
]

for raw in cases:
    r = validate(raw)
    print(f"\nRAW: {raw}")
    print(f"  valid: {r['valid']}")
    for e in r["errors"]:
        print(f"  ERROR [{e['id']}]: {e['message']}  ({e['ref']})")
    for s in r["significant"]:
        print(f"  SIGNIFICANT: {s['code']} - {s['message']}")
