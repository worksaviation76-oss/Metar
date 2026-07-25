# METAR QC — starter project

Detects malformed / logically inconsistent METAR groups against ICAO
Annex 3 App.3 / WMO No. 782 code form, and flags operationally
significant phenomena (TS, wind shear, etc.) with an audible alert.

## What's here
- `rules.py` — the rule set: one entry per METAR group, each with a
  regex and a `ref` back to the Annex 3 / WMO 782 paragraph it encodes.
  **This is a starter set** — wind, visibility, temp/dewpoint, QNH,
  cloud, plus gust-logic and CAVOK-exclusivity cross-checks. It does not
  yet cover RVR tendency, trend groups (BECMG/TEMPO), RMK free text, or
  every present-weather combination — extend it the same way as you
  formalize more of the spec.
- `metar_validator.py` — parses a raw METAR into groups, runs the rules,
  and separately scans for significant phenomena (siren triggers).
- `app.py` — FastAPI backend. `/api/check?station=VNKT` fetches the
  latest raw METAR (currently from the public AWC API) and validates it.
- `static/index.html` — dashboard: shows the raw report, pass/fail with
  the specific rule + citation on failure, and plays a siren (Web Audio
  API, no audio files needed) on error or significant weather.
- `test_validator.py` — offline sanity tests, no network needed.

## Run it locally
```bash
pip install -r requirements.txt --break-system-packages
uvicorn app:app --reload --port 8000
```
Open http://localhost:8000 in a browser.

## Push to GitHub
```bash
cd metar-qc
git init
git add .
git commit -m "Initial METAR QC starter"
git branch -M main
git remote add origin https://github.com/<your-username>/metar-qc.git
git push -u origin main
```
Create the empty repo on github.com first (no README/license, so it stays empty for the push).

## Deploy it live (so it's actually reachable, not just stored on GitHub)
GitHub itself only stores code — it doesn't run Python. To get a live URL:

**Render.com (free tier, easiest)**
1. Sign up at render.com, connect your GitHub account
2. "New +" → "Web Service" → pick the `metar-qc` repo
3. Render auto-detects `render.yaml` in this repo and fills in the build/start commands — just click Create
4. Wait for the build; you'll get a URL like `metar-qc.onrender.com`

**Railway.app (alternative, also has a free tier)**
1. Sign up, "New Project" → "Deploy from GitHub repo" → pick `metar-qc`
2. Railway reads the `Procfile` automatically
3. Deploy, then generate a public domain in the service settings

Either way: free tiers on both sleep after inactivity and wake on the next
request (a few seconds delay), which is fine for occasional checks but
worth knowing if you want it always-instant.

## Roadmap (own station → multi-station)
1. **Now**: validates VNKT (or any ICAO station AWC has) against the
   public feed — good for testing the rule engine and UI end to end.
2. **Real pre-dissemination QC**: swap `fetch_raw_metar()` in `app.py`
   to pull from your actual internal METAR generation/staging output
   at VNKT instead of AWC, so you're checking the report *before* it
   goes out on GTS, not after. The validator and alert layer don't
   need to change — only the fetch source.
3. **Multi-station**: change `/api/check` to accept a list of station
   IDs, loop, and have the frontend poll/display a table instead of a
   single card. AWC's API supports comma-separated `ids` in one call.
4. **Harden the rule set**: the current rules cover the highest-value
   checks. Go through Annex 3 App.3 section by section and add: RVR
   mandatory conditions, trend group syntax, full present-weather
   combination table, remarks parsing — tag each with its paragraph
   reference as you go, same pattern as the existing rules.
5. **Alerting beyond the browser tab**: if you want it running
   unattended, add server-side alerting (e.g. push to a phone) rather
   than relying on a browser tab staying open and focused.
