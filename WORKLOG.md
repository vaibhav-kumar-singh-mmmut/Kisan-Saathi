# WORKLOG.md — Kisan Saathi / Fasal Rakshak Build Log

> Fill this IN REAL TIME during the build. Reconstruct after the fact = low-value log.

---

## Phase 0 — Scaffold

**Date/Time:** 2026-08-28  
**Tool/Agent:** Antigravity AI (Claude Sonnet 4.6 thinking)  
**What happened:**
- Scaffolded all six directories: `/backend`, `/web-dashboard`, `/mobile-app`, `/ml-model`, `/docs`, `/seed-data`
- Created `backend/main.py` (FastAPI + CORS + `/health` open endpoint)
- Created `app/core/config.py` (pydantic-settings), `app/core/database.py` (async SQLAlchemy), `app/api/v1/router.py`, ping endpoint
- Created `ml-model/ml_service.py` stub (FastAPI, `/predict` mock response)
- Scaffolded `web-dashboard` with Vite + React + TypeScript
- Applied dark-mode design system (`index.css`) with zone-color tokens
- Shell `App.tsx` pings `/health` and renders phase road-map grid
- Root `.env.example` documents all 6 required env vars (DB_URL, WEATHER_API_KEY, MAPS_API_KEY, JWT_SECRET, ML_MODEL_ENDPOINT, AGRISTACK_UFSI_KEY)

**Gate status:** ✅ backend starts with `uvicorn main:app`, web shell renders, zero errors

**AI suggestion I rejected / corrected:** _[fill in first real one you catch]_

**Remaining risk for this phase:** PostgreSQL+PostGIS not yet running locally; backend starts but DB calls will fail until Phase 1 sets up the DB.

---

## Phase 1 — Schema + Seed Data ✅

**Date/Time:** 2026-08-28
**Tool/Agent:** Antigravity AI (Claude Sonnet 4.6 Thinking)
**What happened:**
- Created all 10 SQLAlchemy ORM models: `jurisdictions`, `officials`, `farmers`,
  `crop_entries`, `disease_lookup`, `disease_reports`, `weather_daily`, `zone_status`,
  `subsidy_flags`, `retraining_data`
- Created seed orchestrator (`app/db/run_seeds.py`) + two seed scripts
  (`seed_disease_lookup.py`, `seed_villages.py`)
- Created `seed-data/villages.json` — 9 villages spanning all required zone scenarios
- Added `aiosqlite>=0.21.0` to requirements.txt (needed for SQLite async engine in dev)
- Ran `python -m app.db.run_seeds` → **195 rows inserted across all 10 tables**
  - 10 tables created ✅ | 38 disease_lookup entries ✅ | 13 jurisdictions ✅
  - 8 officials | 18 farmers | 9 crop_entries | 37 disease_reports | 63 weather_daily | 9 zone_status ✅

**Gate verification (human-reviewed seed output vs disease_lookup.json rules):**

| Ref | Village | Crop | Disease | Rpts | Wx? | Zone | Rationale — verified correct |
|---|---|---|---|---|---|---|---|
| V1 | Rampur Khurd | Wheat | wheat_yellow_rust | 8 | Y | RED | severity=high, 8 rpts, temp≤15°C + hum≥70% matches triggers ✓ |
| V2 | Sonbarsa | Rice | rice_blast | 6 | Y | RED | severity=high, 6 rpts, hum≥85% + temp 24-28°C matches triggers ✓ |
| V3 | Fatehpur Mafi | Potato | solanaceous_late_blight | 3 | N | ORANGE | hum=82% < 90% required → no weather trigger → orange (not red) ✓ |
| V4 | Mahmoodpur | Mustard | mustard_pests_diseases | 2 | N | GREEN | only 2 rpts, severity=medium, no weather trigger → green ✓ |
| V5 | Gajraula | Wheat | (spread risk only) | 0 | Y | INCOMING_RISK | zero own reports; ~4km from V1 (RED wheat_yellow_rust), spread_radius_km=50, NW wind matches direction ✓ |
| V6 | Deoria Khurd | Sugarcane | sugarcane_red_rot | 5 | N | RED | irreversible=true, 5 rpts, drainage_quality_poor + ratoon_crop risk factors → red regardless of weather ✓ |
| V7 | Naugaon | Chickpea | chickpea_wilt | 1 | N | GREEN | 1 report, confidence=0.65 < 0.70 → needs_expert_review, no weather trigger → green ✓ |
| V8 | Laharpur | Onion | onion_purple_blotch | 4 | Y | ORANGE | severity=high, 4 rpts, compound risk (thrips co-infection) → orange/red boundary → orange ✓ |
| V9 | Bisnathpur | Rice | rice_tungro | 6 | N | RED ⚠️ VIRAL | severity=high, irreversible, 6 rpts. **CRITICAL: pathogen_type=viral — Phase 6 MUST route to no-cure advisory only** ✓ |

**AI suggestion I rejected / corrected:** Seed script initially had `pathogen_type` hard-coded
inline per disease row. Refactored to use a single `PATHOGEN_TYPE_MAP` dict so all 38
mappings are visible together for one-pass human review — less error-prone than scattered
inline strings.

**Tests run:**
```
pytest tests/test_health.py -v
3 passed in 0.26s  (test_health_endpoint, test_ping_endpoint, test_docs_available)
```

**Gate status:** ✅ All 9 village zones match expected logic. V9 viral fixture confirmed seeded.
Seed verification complete — safe to proceed to Phase 2.

**Remaining risk for this phase:**
- Using SQLite for local dev (PostGIS features like `ST_Distance` not available).
  Zone scoring service (Phase 8) will need real PostgreSQL+PostGIS.
  The `aiosqlite` path gives us a working dev loop now; swap to `asyncpg` for prod.
- `disease_lookup.json` ipm_steps are in English — Hindi translation review required
  before Phase 13 ships to farmers.

---

## Phase 2 — Auth + Jurisdiction-Aware Access _(pending)_

---

_[continue for each phase]_
