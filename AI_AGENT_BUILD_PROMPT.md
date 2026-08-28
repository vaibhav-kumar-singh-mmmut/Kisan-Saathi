# BUILD_PLAN.md — Fasal Rakshak (SIH26131), Build Order, Gates, Verification, Worklog

Target: adapt to your actual hackathon time budget (fill in below), but **deploy early**
(after Phase 3), not at the end — judges interact with a hosted demo, and deploy problems
found on the last day are fatal. Feed one phase at a time to your AI agent; do not queue
phases — each gate must pass before the next phase starts.

Total budget: ____ hrs build + 45 min demo/submission assets.

---

## Phase 0 — Scaffold (20 min)
- `React Native` (mobile) + `React` (web) + `FastAPI` (backend) + `PostgreSQL+PostGIS` (db)
- Folders: /mobile-app, /web-dashboard, /backend, /ml-model, /docs, /seed-data
- `.env.example`: DB_URL, WEATHER_API_KEY, MAPS_API_KEY, JWT_SECRET, ML_MODEL_ENDPOINT,
  AGRISTACK_UFSI_KEY — never commit real secrets
- **Gate:** backend starts (`uvicorn main:app`), web/mobile shells render, zero errors.

## Phase 1 — Schema + Seed Data (45 min)
- Create tables: `jurisdictions` (self-referencing tree), `officials`, `farmers`,
  `crop_entries`, `disease_reports`, `disease_lookup` (seed from disease_lookup.json — 35
  entries), `weather_daily`, `zone_status`, `subsidy_flags`, `retraining_data`
- Seed 6-10 mock villages spanning at least one Red, one Orange, one Green, one "Incoming
  Risk" scenario, plus mock officials across the Revenue and Development wings
- **Gate (human review, not just a passing script):** open the seeded villages/reports
  manually and confirm the zone each SHOULD score matches disease_lookup.json's severity
  and weather_triggers logic — do this before writing any scoring code, so you know what
  "correct" looks like. → **Worklog entry: "how I verified the seed data matches the rules."**

## Phase 2 — Auth + Jurisdiction-Aware Access + Health (40 min)
- Phone+OTP, JWT, roles tagged jurisdiction_type (revenue/development/panchayat/service)
  and jurisdiction_id: Farmer, Pradhan, Lekhpal/Patwari, Kanungo, DM, Adl. Commissioner,
  Adl. DM (F/R/E/City), Chief Revenue Officer, SDM, Tehsildar, Naib Tehsildar, CDO, DDO,
  PD (DRDA), DC (MGNREGA), DC (NRLM), BDO, Agriculture/Horticulture Officer, KVK Expert,
  Drone Pilot, Drone Assistant, CHC Manager, FPO Representative
- ONE dashboard route; query results filtered server-side by jurisdiction path — do not
  build per-role dashboards
- `/health` endpoint, open, no auth
- **Deploy now** (Render/Railway). Confirm `/health` from your phone.
- **Gate (all required):** login works hosted, from a phone browser; a Tehsildar sees only
  their tehsil's villages; a DM sees the whole district; wrong OTP → rejected.

## Phase 3 — Farmer App Shell: Voice + Localization (35 min)
- i18next, locale JSON (en, hi at minimum), no hardcoded UI strings
- Icon nav: [Scan Crop] [My Reports] [Weather Alert] [Ask Expert] [Book Drone]
- TTS narration per screen (Google Cloud TTS or Bhashini), matches selected locale
- **Redeploy. Gate:** hosted app opens on a phone, language toggle works, voice plays in
  both languages, screen reader/TTS doesn't crash on missing translation keys.

## Phase 4 — Image Capture, Geotag, Offline Queue (35 min)
- Camera/gallery upload, GPS+EXIF auto-attach, client-side compression
- Offline queue with visible "pending sync" state, auto-upload on reconnect
- Flag (don't hard-block) submissions with missing/mismatched GPS-timestamp
- **Gate:** turn on airplane mode, scan a crop, confirm it queues; reconnect, confirm it syncs.

## Phase 5 — ML Inference Service (50 min)
- Fine-tune MobileNet/EfficientNet on PlantVillage+IP102, further fine-tune on PlantDoc
- Endpoint: POST image → `{disease_id, confidence, crop, pathogen_type}`
- confidence < 70% → `needs_expert_review`, no final diagnosis returned
- Log every inference for retraining
- **Gate:** run 10 sample images from each dataset through the hosted endpoint; confirm
  response shape and confidence flagging both behave as specified — not just "it returns
  something."

## Phase 6 — Pathogen-Branched Advisory (30 min)
Write `tests/advisory.test.ts` (or .py) FIRST, watch it fail, then implement:
- [ ] fungal/bacterial match → returns ipm_steps[], dosage, pre-harvest interval
- [ ] viral match → NEVER returns a treatment/cure step; returns isolate + resistant-variety
  advisory only (this is the one judges are most likely to probe — a wrong viral "cure"
  suggestion is a real correctness bug, not a style choice)
- [ ] nematode match → soil treatment + rotation advisory
- [ ] confidence < 70% → routes to expert queue, no advisory generated yet
- **Gate:** all cases green; manually confirm the viral case in the running app, not just
  in the test file — a passing unit test with a UI that still shows a "spray now" button
  for a viral result is still a bug.

## Phase 7 — Expert Validation Queue (25 min)
- Queue sorted by urgency/location; expert confirms/corrects → writes `retraining_data`
- **Gate:** submit a deliberately ambiguous image, confirm it lands in the queue, confirm
  expert correction updates the record without touching the original farmer submission.

## Phase 8 — Zone Scoring Service (55 min) — the load-bearing feature
Write `tests/zone_scoring.test.ts` FIRST:
- [ ] report_count + severity + growth_rate + affected_area% + weather_trigger → correct
  score → correct color, using Phase 1's hand-verified seed scenarios as fixtures
- [ ] a village whose color DIDN'T change between two scoring runs produces NO new alert
  (alert-fatigue prevention — this is a real design requirement, not an edge case)
- [ ] a village that flips green→red DOES fire the auto-dispatch notification
- [ ] "Incoming Risk" only fires for villages within `spread_radius_km`, matching wind
  direction/shared water source, and growing a crop the source disease can affect
Then implement the scheduled job (cron/serverless, runs every 3-6 hrs + on new confirmed report).
- **Gate:** all tests green; manually trigger one run against seed data and confirm the
  colors match what you hand-verified in Phase 1.

## Phase 9 — Officer Dashboard: Hotspot Map (40 min)
- PostGIS + Leaflet/Mapbox, zone-colored markers, "Incoming Risk" ring style, crop
  catalogue toggle layer, filters (crop/disease/date/jurisdiction), drill-down + trend chart
- Scoped server-side to logged-in officer's jurisdiction (reuse Phase 2's filtering)
- **Redeploy. Gate:** log in as a BDO and a DM in two browser tabs — confirm each sees a
  different-scoped map, not the same data with a different label.

## Phase 10 — Weather + Flood Risk (40 min)
- IMD (api.imd.gov.in) or Open-Meteo fallback; apply disease_lookup.json's weather_triggers
  per disease per village
- CWC flood advisory (aff.india-water.gov.in) cross-referenced against village geodata
- Flood risk REUSES Phase 8's alert pipeline — do not build a second notification system
- **Gate:** feed a mock high-humidity, high-rainfall weather record for a village growing
  wheat at flowering stage; confirm a blight risk banner appears on both farmer and officer
  views without a farmer submission having occurred yet (this proves prediction, not just
  detection, actually works).

## Phase 11 — Subsidy/PMFBY + Camp + Drone Booking (50 min)
Write `tests/subsidy.test.ts` FIRST:
- [ ] flag rejected when independent-report count is below the configured minimum
- [ ] flag allowed once threshold met; 72-hr PMFBY window reminder timestamp is correct
- [ ] claim packet includes geotagged images, disease history, acreage, farmer ID
- [ ] audit trail records flagged-by, evidence, approver, timestamp — immutable once approved
- [ ] "Book Drone Spray" creates a booking record routed to the correct CHC/SHG by proximity
- **Gate:** all tests green; manually walk one flagged submission through officer→BDO
  approval and confirm the audit trail is complete and correct.

## Phase 12 — AgriStack Sync + Post-Harvest Storage Suggestion (30 min)
- Sync `crop_entries` from AgriStack's Crop Sown Registry via UFSI (or a mocked stub if API
  access isn't granted in time — document this honestly, don't fake live integration)
- Lekhpal/Kanungo roles can flag discrepancies between synced data and their own record
- Green Zone + pulses/oilseeds harvest → WDRA storage suggestion surfaced
- **Gate:** confirm the crop catalogue layer on the officer map is populated FROM this sync
  path, not from manually seeded data left over from Phase 1.

## Phase 13 — Polish, Fallback Channels, Full Test Pass (35 min)
- Human-review pass on Hindi translations of disease_lookup.json's ipm_steps — do not ship
  unreviewed machine translation of dosage/technical content
- SMS fallback stub; WhatsApp Business API webhook stub
- Full regression: `npm test` / `pytest` green in a fresh clone
- Redeploy, smoke-test hosted end to end

---

## Verification Checklist

### Tier 1 — Logic/unit tests (write before implementing, per phase above)
Advisory branching (Phase 6), zone scoring (Phase 8), subsidy workflow (Phase 11) — see
each phase's inline checklist. Do not skip writing these first; the whole point is catching
the viral-cure bug and the alert-fatigue bug before a judge does.

### Tier 2 — Integration tests
- [ ] no auth token → 401 on all protected routes; `/health` stays open
- [ ] full round trip over HTTP: scan → inference → advisory → zone update, using one
  seeded village end to end
- [ ] jurisdiction filtering: at least 2 different roles querying the same endpoint get
  provably different, correctly-scoped results

### Tier 3 — Agent/demo-in-the-loop (manual, documented in worklog)
- [ ] cold session: a new user asks "what's wrong with my wheat" → app guides them to Scan
  Crop without confusion
- [ ] viral-disease scan → advisory does NOT suggest a cure (re-verify live, not just in tests)
- [ ] low-confidence scan → routes to expert queue, farmer sees "needs expert check", not a
  fabricated diagnosis
- [ ] simulate 5 reports in one village within a short window → zone flips to Red, alert
  fires once, not five times
- [ ] simulate a 6th report after the flip → no duplicate alert
- [ ] officer books a drone spray → CHC Manager role sees the booking request

---

## Demo Script (for judges / submission video, 4–5 min)

1. **The core loop.** Farmer scans a visibly diseased leaf → confidence high → pathogen-
   aware advisory appears in Hindi with voice narration → "Book Drone Spray" shown.
2. **The judgment case.** Scan a viral-pattern image → show the advisory correctly refuses
   to suggest a cure, offers resistant-variety-next-season instead. (This is your strongest
   "we actually thought about correctness" moment — don't skip it.)
3. **The prediction case, not just detection.** Show the weather-triggered risk banner
   appearing for a village with zero farmer submissions yet — prove this is forecasting,
   not just reactive.
4. **The officer view.** Log in as BDO vs. DM in two tabs, show the jurisdiction-scoped map
   differs correctly. Click a Red zone, show Incoming Risk ring on a neighboring village,
   schedule a camp, flag a subsidy, show the auto-generated PMFBY packet.
5. **The restraint case.** Show a repeat submission in an already-Red, already-alerted
   village does NOT re-fire a duplicate notification — alert fatigue, handled.

---

## Worklog (fill DURING the build, in WORKLOG.md at repo root)
Capture as they happen, not reconstructed after:
- Which phase, what tool/agent did the work, and why
- At least one rejected/corrected AI-agent suggestion with your reasoning (watch for the
  agent over-engineering the scoring formula, or getting pathogen-type branching wrong —
  record the first real one you catch)
- Verification evidence: seed hand-review notes (Phase 1), test-first commit for Phases 6/8/11
- Remaining risks / what you'd do next (this feeds your README limitations section too —
  reuse the "Known Limitations" list from PROJECT_OVERVIEW.md)

## Submission Checklist
- [ ] Hosted URL working, tested from a phone on mobile data (not just your dev wifi)
- [ ] Repo clean, README complete, links to PROJECT_OVERVIEW.md / PRODUCTION_TABLE.md /
      PRODUCTION_WORKFLOW.md / disease_lookup.json
- [ ] All tests green in a fresh clone
- [ ] Demo video recorded following the script above (4-5 min)
- [ ] WORKLOG.md complete
- [ ] Known limitations stated honestly (dataset domain gap, IMD/AgriStack API access,
      machine-translation review requirement, subsidy fraud mitigations) — judges trust
      teams more when they name the gaps themselves
