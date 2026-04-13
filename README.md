# HOST

HOST is a FastAPI backend for an architecture TFG about Madrid 2050. It mixes:

- scoring logic for adaptive reuse proposals
- demo/sample data for quick testing
- real official public data from Madrid Open Data, INE, and Catastro

## Project Structure

- `backend/app/main.py`: FastAPI entrypoint
- `backend/app/api/routes.py`: legacy demo routes and new real-data routes
- `backend/app/models/schemas.py`: shared typed dictionaries and Pydantic models
- `backend/app/services/scoring_engine.py`: all scoring and proposal logic
- `backend/app/services/climate_service.py`: current climate-risk logic
- `backend/app/services/madrid_api.py`: official Madrid Open Data access
- `backend/app/services/ine_api.py`: official INE JSON API access
- `backend/app/services/catastro_api.py`: official public Catastro access
- `backend/app/services/data_normalizers.py`: converts official raw data into HOST input models
- `backend/app/services/real_data_service.py`: orchestration for the new real-data endpoints

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn backend.app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/app`
- `http://127.0.0.1:8000/docs`

## Deploy Online

The easiest way to publish HOST so other people can open it is `Render`.

This repository now includes a ready-to-use `render.yaml` file. It tells Render to:

- install dependencies from `requirements.txt`
- run the app with `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- use `/` as the health check

### One-time setup on Render

1. Push this project to GitHub.
2. Log in to Render.
3. Click `New +` -> `Blueprint`.
4. Select your GitHub repository.
5. Render will detect `render.yaml` and create the web service automatically.
6. Wait for the first deploy to finish.
7. Open the public URL Render gives you, then visit:
   - `/app`
   - `/docs`

Example:

- `https://your-render-service.onrender.com/app`
- `https://your-render-service.onrender.com/docs`

### Notes

- The free Render plan can sleep when unused, so the first request after inactivity may take a little longer.
- The app depends on public Madrid, INE, and Catastro services. If one of those official services is down, some real-data routes may return fallback or partial results.
- You do not need to expose port `8000` or `8001` on Render. Render provides its own `PORT` environment variable automatically.

## TFG Demo Flow

If you want a simple presentation flow inside Swagger UI:

1. Open `/docs`
2. Start with `GET /real/examples` to show the available official-data requests
3. Run `GET /real/district/Centro` to explain district normalization
4. Run `GET /real/building/by-address` with `street_name=ALCALA` and `street_number=45`
5. Run `GET /real/proposal/Centro` or `POST /real/analyze` to show the full HOST pipeline

This sequence is beginner-friendly because it moves from simple district data to full proposal generation step by step.

If you want a more visual presentation, open `/app`. It includes:

- a demo mode using the built-in sample data
- an official-data mode connected to the real endpoints
- all 21 Madrid districts in the official-data selector
- a free interactive MapLibre 3D viewer for looked-up buildings
- cards for the main indices
- program and climate strategy sections
- the raw JSON response for explanation and debugging

## New Real-Data Endpoints

- `GET /real/district/{district_name}`
  - returns normalized district data built from official Madrid and INE sources
- `GET /real/building/by-address`
  - uses structured Catastro address lookup
  - required query params: `street_name`, `street_number`
  - optional query params: `street_type`, `province`, `municipality`, `block`, `stair`, `floor`, `door`
- `GET /real/proposal/{district_name}`
  - district proposal from official data
  - add address query params if you want a full district + building proposal
- `POST /real/analyze`
  - accepts a JSON body with `district_name`, optional `building_address`, optional `building_overrides`, and `refresh`
- `GET /real/examples`
  - returns ready-to-use example requests for Swagger, Postman, or a TFG live demo

Example `POST /real/analyze` body:

```json
{
  "district_name": "Centro",
  "building_address": {
    "street_type": "CL",
    "street_name": "ALCALA",
    "street_number": "45"
  },
  "building_overrides": {
    "roof_usable": 1,
    "outdoor_space": 0
  }
}
```

## Official Sources Used

### Madrid Open Data

- Latest district padrón dataset for age structure and population
- District indicator panel for density, households, green-space metrics, and municipal equipment

### INE

- Official JSON API tables for municipal household size and household type context in Madrid city

### Catastro

- Public non-protected address lookup and cadastral data services

## Important Limitations

- Catastro public non-protected services do not expose every architectural variable used by HOST.
- For that reason, some building fields are estimated from lawful public descriptors such as use, age, surface, and observed floors.
- If Catastro returns multiple candidate properties for one address, HOST reports a partial result and recommends adding floor and door information.
- Climate logic is still local and heuristic in this first version. The code is now separated so official climate/environment sources can be plugged in later.
