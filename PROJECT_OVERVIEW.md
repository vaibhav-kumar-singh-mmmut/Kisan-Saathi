# Project Overview — Fasal Rakshak: Crop Health & Pest Advisory System (SIH26131)

## Problem Statement
Farmers often recognise crop diseases or pest infestations only after visible damage has
spread. Extension staff cover large areas, and laboratory diagnosis or expert advice is often
not immediately available. Weather, crop stage, variety, soil condition, and local pest history
all influence risk — but these inputs are rarely combined into actionable farm-level alerts.
Incorrect diagnosis leads to delayed treatment, excessive or inappropriate pesticide use,
increased cultivation cost, pesticide residue concerns, and yield loss. Natural calamities like
floods compound this — farmers need advance warning and support beyond disease alone.

**The challenge:** provide timely, reliable, and locally relevant detection, forecasting, and
management support — and connect it to the government infrastructure that already exists.

## Core Positioning
India already runs substantial digital agriculture infrastructure: AgriStack (farmer/land/crop
identity), SVAMITVA (village geodata), Bhuvan and the National Pest Surveillance System (pest
detection), FASAL and Krishi-DSS (satellite forecasting), PMFBY (insurance), e-NAM (market
access), WDRA/e-NWR (storage credit), Namo Drone Didi (spraying), and CWC/IMD (weather &
flood forecasting). This project's role is NOT to rebuild these — it is the **jurisdiction-aware,
hyper-local orchestration layer** that routes their signals to the correct village/officer,
automates workflows (subsidy claims, drone bookings, camp scheduling), and closes the last
mile with voice-first, multilingual accessibility.

## User Roles

### Farmer-facing
| Role | Description |
|---|---|
| Farmer | Primary end user — scans crops, receives advisories |
| Pradhan (elected village head) | Bulk image capture for village, village-level status view |
| Lekhpal / Patwari (revenue official) | Statutory village-cluster crop-record keeper; verification source for crop catalogue |
| Kanungo | Supervises a group of Lekhpals; escalation point for data discrepancies |

### Revenue wing (District Magistrate line)
District Magistrate, Adl. Commissioner, Adl. DM (F/R, E, City), Chief Revenue Officer,
Sub Divisional Magistrate, Tehsildar, Naib Tehsildar — jurisdiction narrows from district →
sub-division → tehsil.

### Development wing (Panchayati Raj line)
Chief Development Officer, District Development Officer, Project Director (DRDA),
DC (MGNREGA), DC (NRLM), Block Development Officer — jurisdiction narrows from district → block.

### Cross-cutting / service roles
Agriculture Officer, Horticulture Officer, KVK/Lab Expert (validator), RPTO-certified Drone
Pilot, Drone Assistant, Custom Hiring Centre Manager, FPO representative.

## Core Features

### Farmer-facing
- Voice-assisted, icon-based, low-literacy-friendly UI with regional language support (Hindi +
  expandable)
- Scan/upload crop image → AI diagnosis with confidence score; low-confidence results route to
  human expert validation, never guessed
- Pathogen-aware advisory: IPM-first treatment steps for fungal/bacterial disease; NO false
  "cure" advisory for viral disease (isolate + resistant variety next season instead)
- Weather-based predictive risk alerts before symptoms appear
- Offline-first capture with auto-sync
- "Book Drone Spray" — connects to nearest Namo Drone Didi SHG / Custom Hiring Centre
- Post-harvest "store, don't distress-sell" suggestion via WDRA/e-NWR pledge financing
- Follow-up confirmation loop feeding model retraining
- WhatsApp/SMS/IVR fallback for low-smartphone-penetration areas

### Officer/Official-facing (jurisdiction-scoped, single dashboard)
- Live hotspot map: Red/Orange/Green zones, computed by a scheduled scoring service, not
  live-computed per page load
- "Incoming Risk" ring for downstream villages predicted from wind/water-linked spread modeling
- Crop catalogue layer ("what's planted where") synced from AgriStack's Crop Sown Registry
- Camp scheduling with auto-notification to affected farmers
- Subsidy flagging with minimum-report threshold + full audit trail → auto-generates PMFBY
  claim packet
- Drone booking + dual-purpose aerial imagery capture during spray missions
- Flood risk overlay from CWC forecasts, reusing the same alert/subsidy pipeline as disease
- Preventive supply-chain and crop-rotation planning before sowing season

### System-wide
- Geo-time-tagged, fraud-resistant submissions
- Rule-based (not black-box) risk scoring — explainable to officers
- Continuous model retraining from expert-confirmed field data

## Tech Stack Summary (full detail in PRODUCTION_TABLE.md)
React Native (mobile) + React (web dashboard) + FastAPI/Node backend + PostgreSQL/PostGIS +
PyTorch/TensorFlow inference service + Leaflet/Mapbox + Google Cloud/Bhashini TTS-STT +
i18next localization + WhatsApp Business API + IMD/Open-Meteo weather + AgriStack UFSI sync.

## Full Integration Map
| System | Provides | Our role |
|---|---|---|
| AgriStack (Farmer/Land/Crop Sown Registries + UFSI) | Verified farmer identity, land, crops sown | Sync via UFSI instead of building our own farmer/crop DB |
| SVAMITVA | Verified village boundary/property geodata | Base map layer for jurisdiction tree |
| Bhuvan Pest/Disease Surveillance Portal | Crowdsourced pest/disease geotagging | Cross-reference/contribute reports |
| National Pest Surveillance System | AI/ML detection, 66 crops, 432 pests | Avoid duplicating; add jurisdiction routing on top |
| FASAL / Krishi-DSS (ISRO) | Satellite yield & disease forecasting (incl. wheat rust) | Layer into predictive risk engine |
| IMD (api.imd.gov.in, Agromet/KALP/SANKALP) | District weather, agromet advisory | Primary weather trigger source for risk engine |
| CWC (aff.india-water.gov.in) / NDMA Sachet | Flood forecasts, 90%+ accuracy, CAP alerts | Second trigger source into same alert/subsidy pipeline as disease |
| PMFBY / National Crop Insurance Portal | Loss compensation, no subsidy cap | Auto-generate claim packets from subsidy-flag workflow; 72-hr window reminder |
| e-NAM | 1,650+ mandis, price discovery | Surplus/deficit routing suggestions |
| WDRA / e-NWR | Warehouse storage + ~4% pledge financing | "Don't distress-sell" suggestion for green-zone harvests |
| 10,000 FPO Scheme | Farmer aggregation, collective bargaining | Route drone booking/subsidy claims/market access through FPO when available |
| Namo Drone Didi / Kisan Drone CHCs | Subsidized spraying + onboard camera | "Book Drone Spray" action + supplementary aerial imagery feed |
| Kisan e-Mitra / KISAN SARATHI / BharatVistaar | Precedent for voice/chat advisory at scale | Validates our LLM-chatbot direction |

## Data Sources for Training/Seed Data
PlantVillage, PlantDoc, IP102, LeafNet (public image datasets) → fine-tuned over time with
crowdsourced, expert-validated field images. Full disease coverage (35 entries across cereals,
pulses, vegetables, fruits, bulbs, berries) seeded in `disease_lookup.json`.

## Known Limitations (state these honestly in the pitch)
- Public training datasets are lab-condition images, not Indian field conditions — accuracy
  improves as the crowdsourced feedback loop matures
- IMD/AgriStack production API access may need formal partnership — prototype on Open-Meteo,
  document the swap-in path
- Subsidy-linked reporting creates a fraud incentive — mitigated by minimum-report thresholds
  and full audit trails
- Machine-translated technical/dosage content carries real-world risk — requires human review
  pass before shipping, not fully automated

## Headline Stat
India loses an estimated 30% of crops, worth ₹90,000 crore annually, to pests and diseases —
plant diseases alone account for nearly one-third of total production losses.

## Repository
`sih-crop--disease--detection-` — https://github.com/vaibhav-kumar-singh-mmmut/sih-crop--disease--detection-
