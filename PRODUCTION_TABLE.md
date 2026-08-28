# Production Table — Fasal Rakshak

## Tech Stack by Layer
| Layer | Technology | Purpose |
|---|---|---|
| Farmer/Pradhan Mobile App | React Native | Cross-platform, offline-capable |
| Officer/Official Web Dashboard | React.js | Jurisdiction-scoped map dashboards, single codebase for all roles |
| Backend API | FastAPI (Python) | REST layer; Python integrates naturally with ML inference |
| Database | PostgreSQL + PostGIS | Relational + geospatial queries for hotspot/jurisdiction logic |
| Zone Scoring Service | Scheduled backend job (cron/serverless) | Computes zone colors every 3-6 hrs; NOT computed per page load |
| ML Model Serving | FastAPI/Flask microservice + PyTorch/TensorFlow | Disease/pest classification inference |
| File/Image Storage | S3-compatible / Firebase Storage | Uploaded crop + drone imagery |
| Maps | Leaflet.js / Mapbox | Zone rendering, spread-path overlays |
| Localization | i18next (web) / i18next-RN (mobile) | Static UI strings by locale JSON; disease_lookup content human-reviewed after translation |
| Voice (TTS/STT) | Google Cloud TTS/STT or Bhashini | Regional-language voice guidance and input |
| SMS/WhatsApp/IVR | Twilio / MSG91 / WhatsApp Business API | Zero/low-smartphone reach |
| Weather | api.imd.gov.in (production) / Open-Meteo (prototype) | Risk-engine weather triggers |
| Flood Data | CWC (aff.india-water.gov.in), NDMA Sachet CAP alerts | Second alert-trigger source |
| Auth | JWT + OTP (phone-based) | Role-based access across all user types |
| Hosting | Render/Railway (hackathon) → cloud provider at scale | Deployment |

## Full Role & Jurisdiction Table
| Role | Wing | Scope | Core Actions |
|---|---|---|---|
| Farmer | — | Own submissions | Scan, view diagnosis, book drone, receive alerts |
| Pradhan | Panchayati Raj (elected) | Own village | Bulk capture, village status |
| Lekhpal/Patwari | Revenue (appointed) | Cluster of villages | Statutory crop-record source; verification cross-check |
| Kanungo | Revenue | Group of villages | Supervises Lekhpals; discrepancy escalation |
| District Magistrate | Revenue | District | Full aggregate + drill-down |
| Adl. Commissioner / Adl. DM (F/R, E, City) / Chief Revenue Officer | Revenue | District/Division | District-level aggregate |
| Sub Divisional Magistrate | Revenue | Sub-Division | Tehsils/villages within sub-division |
| Tehsildar / Naib Tehsildar | Revenue | Tehsil | Villages within tehsil |
| Chief/District Development Officer | Development | District | Scheme-focused district aggregate |
| Project Director (DRDA) / DC (MGNREGA) / DC (NRLM) | Development | District | Scheme-specific overlays (labour, livelihood) |
| Block Development Officer | Development | Block | Villages within block; subsidy approval |
| Agriculture/Horticulture Officer | Cross-cutting | Block/Tehsil charge | Zone map, camp scheduling, validation |
| KVK/Lab Expert | Cross-cutting | Assigned queue | Confirms/corrects low-confidence AI diagnoses |
| RPTO Drone Pilot / Drone Assistant | Service provider | Linked to SHG/CHC | Executes spray + imagery capture bookings |
| CHC Manager | Service provider | CHC location | Confirms drone availability/bookings |
| FPO Representative | Aggregation entity | Member farmers | Pooled bookings, claims, market access |

## Disease/Pest Coverage (full detail in disease_lookup.json)
| Category | Crops covered |
|---|---|
| Cereals | Wheat (3 rusts + pest complex), Rice (bakanae, false smut, blast, tungro) |
| Cash/Fiber | Sugarcane (red rot), Cotton (whitefly, pink bollworm) |
| Oilseed | Mustard (aphid/Alternaria/white rust) |
| Bulb | Onion (purple blotch, Stemphylium blight, thrips, Fusarium basal rot) |
| Vegetables | Tomato/Potato/Brinjal/Chilli (early/late blight, bacterial wilt, pink rot, powdery scab, fruit borer), nursery damping-off |
| Orchard Fruits | Mango, Litchi, Pomegranate, Guava, Grapes (anthracnose cross-crop family, powdery mildew, canker, sudden death, bacterial blight, nematode wilt) |
| Pulses | Chickpea, Lentil, Pea, Pigeon Pea, Moong (wilt, rust, powdery mildew, blights) |
| Berries | Strawberry (powdery mildew, anthracnose) |

35 total entries with severity, spread medium (incl. `cropping_calendar_bridge`), weather
triggers by pathogen-type pattern, compound-risk pairs, and irreversibility flags.

## Weather Risk Pattern Reference
| Pathogen/type | Trigger pattern |
|---|---|
| Rust | Cool (10-27C) + wind-dispersed, near-calendar-predictable |
| Oomycete late blight | Cool + very wet (10-21C, 90%+ humidity) |
| Alternaria early blight | Warm + humid (24-29C, 70%+ humidity) — opposite band from late blight |
| Powdery mildew | Dry daytime + humid night — inverts the "less rain = less risk" rule |
| Bacterial | Rain-splash + insect/physical wound as entry point |
| Soil-borne wilt | Cumulative rainfall + poor drainage, not single-day trigger |

## External Data/API Sources
| Source | Data | Access |
|---|---|---|
| AgriStack UFSI | Farmer/Land/Crop Sown Registries | Open API gateway, consent-managed |
| data.gov.in | Crop stats, schemes, open datasets | Open API/downloads |
| Soil Health Card | Soil nutrient data | State-wise open data on data.gov.in |
| api.imd.gov.in | District weather, agromet advisory | Registered API access |
| CWC (aff.india-water.gov.in) | 5-day flood advisory, 20 river basins | Public portal |
| Bhuvan (ISRO) | Satellite imagery, pest/disease portal | Open geoportal |
| e-NAM | Mandi prices, trade | 1,650+ mandis integrated |
| WDRA/e-NWR | Warehouse receipts | WDRA-accredited warehouse network |

## Timeline Snapshot (hackathon)
| Phase | Focus | Day |
|---|---|---|
| 0-2 | Scaffolding, jurisdiction-aware auth, farmer UI shell | 1 |
| 3-5 | Image capture, ML inference, pathogen-aware advisory | 1-2 |
| 6-7 | Expert queue, officer hotspot dashboard, zone scoring service | 2 |
| 8-9 | Weather + flood risk layer, subsidy/PMFBY/camp workflow | 2-3 |
| 10-11 | Drone booking, AgriStack sync, WDRA storage suggestion | 3 |
| 12 | Hindi localization, polish, seed data, demo prep | 3 |
