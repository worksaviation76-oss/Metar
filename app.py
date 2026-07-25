"""
Own-station (VNKT) METAR QC service.

GET /api/check?station=VNKT
    -> fetches latest raw METAR for the station from the AWC Data API
       and runs it through metar_validator.validate()

Run:
    pip install fastapi uvicorn httpx --break-system-packages
    uvicorn app:app --reload --port 8000

Then open static/index.html (served below at /) in a browser.

NOTE on data source: this uses the public Aviation Weather Center API
(https://aviationweather.gov/data/api/) as a stand-in feed. For real
pre-dissemination QC at VNKT you'd point FETCH_URL at your own internal
METAR generation/staging output instead of (or in addition to) AWC —
swap out `fetch_raw_metar()` for that source when you're ready; the
validator and alerting layer don't need to change.
"""

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from metar_validator import validate

app = FastAPI(title="METAR QC")

AWC_URL = "https://aviationweather.gov/api/data/metar"


async def fetch_raw_metar(station: str) -> str:
    params = {"ids": station, "format": "raw"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(AWC_URL, params=params)
        resp.raise_for_status()
        text = resp.text.strip()
        if not text:
            raise HTTPException(status_code=404, detail=f"No METAR returned for {station}")
        # AWC raw format returns one line per report; take the latest (first)
        return text.splitlines()[0]


@app.get("/api/check")
async def check(station: str = "VNKT"):
    raw = await fetch_raw_metar(station.upper())
    result = validate(raw, station_hint=station.upper())
    return result


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")
