# /docs

## Architecture References

| Document | Purpose |
|----------|---------|
| [`PRODUCTION_WORKFLOW.md`](../PRODUCTION_WORKFLOW.md) | **MVP Module Map (M1–M5)** + all 11 detailed workflow flows |
| [`AI_AGENT_BUILD_PROMPT.md`](../AI_AGENT_BUILD_PROMPT.md) | Phase-by-phase implementation checklist (Phase 0–13) |

### MVP Module Map (quick reference)

| Module | Name | Build Phases |
|--------|------|-------------|
| **M1** | AI Crop Doctor | Phase 3 (capture) + Phase 4 (geotag/offline) + Phase 5 (ML) |
| **M2** | Crop Risk Radar | Phase 8 (zone scoring) + Phase 9 (map) + Phase 10 (weather/flood) |
| **M3** | Smart Advisory | Phase 5–6 (pathogen-branched advisory) |
| **M4** | Geo Disease Hotspot Maps | Phase 8–9 (zone scoring + officer map) |
| **M5** | Expert Validation Loop | Phase 7 (expert queue + retraining) |

---

## Document Index


| File | Purpose |
|------|---------|
| `architecture.md` | System architecture diagram and component map |
| `api-reference.md` | Endpoint reference (auto-generated from FastAPI OpenAPI JSON) |
| `zone-scoring-spec.md` | Formal specification of the zone-scoring algorithm (Phase 8) |
| `advisory-logic.md` | Pathogen-branched advisory rules (Phase 6) |
| `deployment.md` | Render/Railway deployment runbook |
| `data-dictionary.md` | DB schema data dictionary |

These will be created phase by phase.
