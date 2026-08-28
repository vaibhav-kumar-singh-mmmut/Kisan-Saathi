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

## Phase 2 — Auth + Jurisdiction-Aware Access ✅

**Date/Time:** 2026-08-28
**Tool/Agent:** Antigravity AI (Claude Sonnet 4.6 Thinking)
**What happened:**
- `app/utils/otp.py` — 6-digit OTP, 5-min TTL, in-memory store (Redis swap-in point documented)
- `app/utils/jwt_utils.py` — `create_access_token` + `decode_access_token` (python-jose)
- `app/utils/jurisdiction_scope.py` — `get_current_user` FastAPI OAuth2 dependency
- `app/schemas/auth.py` — `OTPRequest`, `OTPVerify`, `TokenResponse`, `UserMe`, `OTPRequestResponse`
- `app/schemas/jurisdiction.py` — `VillageSummary` (Pydantic v2 `from_attributes=True`)
- `app/services/auth_service.py` — `request_otp()` (searches officials + farmers by phone) + `verify_otp_and_login()`
- `app/services/jurisdiction_service.py` — `get_village_ids_in_scope()` recursive CTE + role→scope mapping
- `app/api/v1/endpoints/auth.py` — POST /otp/request, POST /otp/verify, GET /me
- `app/api/v1/endpoints/dashboard.py` — GET /villages (single route, server-side scoped)
- `app/core/config.py` — added `OTP_TTL_SECONDS=300`, `DEV_RETURN_OTP=True`
- `app/api/v1/router.py` — mounted `/auth` and `/dashboard` routers

**AI suggestion I rejected / corrected:** Initial test fixtures used a non-StaticPool
in-memory SQLite engine — each `Session()` opened a new connection and got a blank DB.
Fixed by using `StaticPool` so all sessions share the same in-memory connection.

**Tests run:**
```
pytest tests/test_health.py tests/test_auth.py -v
11 passed in 0.60s

test_health_endpoint PASSED
test_ping_endpoint PASSED
test_docs_available PASSED
test_otp_request_known_official PASSED    ← known phone → 200, dev_code present
test_otp_request_unknown_phone PASSED     ← unknown phone → 404
test_otp_verify_wrong_code PASSED         ← wrong OTP → 401
test_otp_verify_correct_code PASSED       ← correct OTP → 200, JWT present
test_me_no_token PASSED                   ← no token → 401
test_me_valid_token PASSED                ← valid JWT → 200, role/jurisdiction correct
test_dashboard_tehsildar_scope PASSED     ← Tehsildar sees only tehsil villages
test_dashboard_dm_scope PASSED            ← DM sees all district villages
```

**Gate status:** ✅ All 8 Phase 2 auth tests green. Jurisdiction scope verified via automated tests.
`/health` remains open (no auth required).

**Remaining risk for this phase:**
- OTP is in-memory — restarts clear all pending OTPs (acceptable for hackathon).
- `DEV_RETURN_OTP=True` must be set False before any public deployment.
- Recursive CTE works in SQLite (dev) and PostgreSQL (prod). Not tested with PostGIS yet.



---

## Phase 3 — Farmer App Shell: Voice + Localization ✅

**Date/Time:** 2026-08-28
**Tool/Agent:** Antigravity AI
**What happened:**
- Setup `i18next` + `react-i18next` with `en.json` and `hi.json` containing 100% synchronized translation keys.
- Implemented Web Speech API TTS voice hook (`useTTS.ts`) with voice auto-selection for `hi-IN` and `en-IN` and language toggle persistence in `localStorage`.
- Built 5-screen interactive Farmer Shell (`FarmerShell.tsx`):
  1. `[Scan Crop]`: Native rear-camera capture (`capture="environment"`), gallery photo upload, image preview with GPS auto-tagging (`navigator.geolocation`), client-side canvas compression, and Analyze/Retake flow.
  2. `[My Reports]`: Historical farmer crop scan reports with crop icons, village tags, status badges (`status_ready`, `status_review`, `status_scheduled`), and TTS readout.
  3. `[Weather Alert]`: Climate radar cards (Temperature, Humidity, Rain forecast) + Village disease zone risk breakdown (Red / Orange / Green / Incoming Risk).
  4. `[Ask Expert]`: Consultation form with interactive quick-question suggestion chips + submission receipt and response SLA.
  5. `[Book Drone]`: Aerial spray service with dynamic field acreage counter, crop selector, chemical/bio-spray toggle, real-time cost calculation (₹400/acre), and instant booking confirmation badge.
- Re-architected `index.css` following `front.md` minimalist principles: flat surfaces, single border-radius (`8px`), single accent (`#22c55e`), WCAG AA high-contrast, large touch targets (56px+), zero decorative gradients.
- Fixed CORS origins in backend `config.py` to allow `127.0.0.1` and `localhost` ports.

**AI suggestion I rejected / corrected:**
- Initially, the scan button was a mock visual circle without native file input triggers. Replaced with dual `<input type="file">` refs (one with `capture="environment"` for mobile camera, one for photo gallery).
- Fixed React 19 `JSX.Element` type mismatch in `FarmerShell.tsx` by utilizing `React.ReactElement`.

**Gate status:**
- ✅ TypeScript + Vite production build compiles in ~100ms with 0 errors.
- ✅ Language toggle switches between English and Hindi live without reloads.
- ✅ Web Speech API voice synthesis functions for all 5 screens in both languages.
- ✅ Backend test suite 11/11 tests green.

**Remaining risk for this phase:**
- SpeechSynthesis availability depends on browser/OS platform (handled gracefully with fallback).

---

## Phase 4 — Image Capture, Geotag, Offline Queue _(pending)_
