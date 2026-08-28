# Production Workflow — Fasal Rakshak

## 1. Farmer Reporting Flow
```
Farmer opens app (voice guides in regional language, i18next locale)
        v
[Scan Crop] -> capture/upload photo -> auto GPS+timestamp
        v
   Online? --No--> queue locally -> auto-sync when connected
        v
Uploaded -> ML inference service
        v
   Confidence >= threshold? --No--> Expert Validation Queue
        v
Pathogen-type check: fungal/bacterial -> IPM treatment steps
                      viral -> NO cure advisory; resistant variety +
                               isolate to prevent spread instead
        v
Advisory shown (voice + regional language) + nearest dealer +
[Book Drone Spray] option (routes to nearest SHG/CHC)
        v
Submission logged -> zone scoring service picks it up on next run
        v
5-7 days later: follow-up "did this help?" -> feeds retraining dataset
```

## 2. Pradhan Bulk Reporting Flow
```
Pradhan opens [Bulk Upload] mode -> captures multiple farm images per visit
        v
Each image auto-tagged to nearest registered plot (GPS match against
AgriStack-synced crop_entries)
        v
Same ML inference + advisory pipeline as individual flow
        v
Village-level summary visible to Pradhan; Lekhpal/Kanungo can
cross-verify against official crop record
```

## 3. Expert Validation Flow
```
Low-confidence/flagged submission enters queue
        v
KVK/Lab Expert reviews image + AI guess + location
        v
Confirms or corrects -> stored in retraining_data table
        v
Final advisory sent to farmer (pathogen-type branch applies here too)
```

## 4. Zone Scoring Service (scheduled backend job, every 3-6 hrs)
```
For each village:
  1. Pull disease_reports (last 7-14 days)
  2. Count reports, compute week-over-week growth rate
  3. Look up severity per disease_lookup.json
  4. Pull weather_daily; check against disease weather_triggers
  5. Pull crop_entries (synced from AgriStack) for % acreage affected
  6. score = f(report_count, severity, growth_rate, affected_area%, weather_trigger)
  7. Map score -> zone color (red/orange/green)
  8. Compare to PREVIOUS zone color:
       changed   -> write zone_status row + fire auto-dispatch notification
       unchanged -> update silently, no alert (avoids alert fatigue)
  9. If newly Red: run "Incoming Risk" check on neighboring villages
     (wind direction + adjacency + shared water source + same-crop presence)
```

## 5. Officer Zone Monitoring Flow
```
Officer logs in (jurisdiction-scoped: village/tehsil/block/district
per Revenue or Development wing)
        v
Map shows zone-scored villages + Incoming Risk rings + flood overlay
(from CWC) + crop catalogue layer (from AgriStack sync)
        v
Drill into a zone -> reports, trend chart, weather context
        v
Officer action:
  |-- Schedule Camp -> notify affected farmers (push+SMS)
  |-- Book Drone Spray -> dispatch to CHC/SHG, dual-purpose imagery capture
  |-- Flag for Subsidy -> min. report threshold check -> BDO review
  '-- Escalate to District Official
```

## 6. Outbreak Spread Prediction Flow
```
Village confirmed outbreak + rising report pattern
        v
Spread-Direction Engine checks: wind direction, water-source adjacency,
geographic adjacency, same-crop presence nearby, disease-specific
spread_radius_km (from disease_lookup.json)
        v
Downstream villages flagged "Incoming Risk" (distinct marker)
        v
Auto-dispatch: officers, Pradhan/farmers in downstream zone,
"Dedicated Distribution Drive" suggested SCOPED to buffer zone only
        v
Zones outside predicted path stay "Protected/Unaffected" -
explicitly excluded from pesticide drive (residue/cost reduction goal)
        v
Real reports confirm/refute prediction -> recalibrates future
spread-radius assumptions for that disease
```

## 7. Subsidy / PMFBY Flow
```
Officer flags submission(s) as subsidy-eligible
        v
Check: minimum independent confirmed reports in area? --No--> blocked
        v Yes
72-hour PMFBY reporting window reminder (fires from first confirmed report)
        v
Routed to BDO -> auto-generated PMFBY claim packet (geotagged images,
disease confirmation history, affected acreage, farmer ID from AgriStack)
        v
BDO approves/rejects -> audit trail (flagged-by, evidence, decision, timestamp)
        v
Approved -> submitted to National Crop Insurance Portal / PMFBY process
```

## 8. Flood Risk Flow (reuses disease alert/subsidy pipeline)
```
CWC issues 5-day flood advisory for a river basin/gauge station
        v
Cross-reference gauge location against village geodata (catchment mapping)
        v
Flagged villages get "Flood Risk - Incoming" marker (same visual
pattern as disease Incoming Risk)
        v
Auto-dispatch to Pradhan/farmers/officers (same pipeline as disease alerts)
        v
Post-flood: confirmed-flooded farmers -> same PMFBY subsidy workflow,
different trigger source
```

## 9. Post-Harvest Storage & Market Flow
```
Green Zone farmer harvests healthy crop (esp. pulses/oilseeds with
known 15-25% post-harvest price dip)
        v
System suggests: store via WDRA-registered warehouse instead of
distress sale -> obtain e-NWR -> pledge for ~30% market value loan
at ~4% effective rate
        v
Sell later on e-NAM once price recovers, OR fulfill surplus->deficit
routing suggestion (Red Zone shortfall areas identified from zone map)
```

## 10. Preventive Supply Chain & Crop Rotation Flow (pre-sowing)
```
District Official reviews historical hotspot + Soil Health Card data
        v
Identifies at-risk areas before sowing season
        v
Crop rotation rule engine suggests next crop:
  - depleting crop (wheat/rice) -> suggest nitrogen-fixing legume
  - repeated same-family disease incidence -> suggest different family
    (flags reduced benefit if rotating WITHIN pulse family, since
    several pulse diseases share pathogens across that family)
  - Soil Health Card deficiency -> suggest tolerant crop
        v
Preventive input supply (resistant varieties) + soil sample drive
scheduled for flagged areas
```

## 11. Model Improvement Loop (continuous, background)
```
New submissions + expert corrections + follow-up confirmations +
drone-captured aerial imagery
        v
Accumulate in retraining dataset
        v
Periodic (scheduled batch) model retraining
        v
Updated model deployed to inference service
        v
Accuracy improves on real Indian field conditions over lab-trained baseline
```
# MVP Module Map (M1-M5)

Simplified module view for demos/pitches — maps directly onto the phases in
AI_AGENT_BUILD_PROMPT.md and the detailed flows above.

```
FARMER
  v
Register Crop & Field  (crop_entries, synced/entered per Phase 1/12)
  v
Upload Image           (Phase 3/4)
  v
AI Disease Detection   (Phase 4/5)
  v
        +------------------+------------------+
        v                                     v
  Confidence Score              Weather + Crop Stage + GPS
        \___________  ___________/
                    v v
              RISK ENGINE          <- M2: Crop Risk Radar (Phase 8-9)
                    |
        +-----------+-----------+
        v                       v
  Low/Med Risk              High Risk
        v                       v
    Monitor              Action Plan          <- M3: Smart Advisory (Phase 6)
                              v
                      Save Field Report
                              v
                    Geo Hotspot Engine         <- M4: Geo Disease Hotspot Maps (Phase 8)
                              v
                    Officer Dashboard          (Phase 9)
                              v
                    Expert Validation          <- M5: Expert Validation Loop (Phase 7)
                              v
                    Confirmed Field Data       (feeds retraining_data, Phase 7)
```

## Module -> Build Prompt Phase Mapping
| Module | Name | Corresponding Phase(s) |
|---|---|---|
| M1 | AI Crop Doctor | Phase 3 (capture/geotag) + Phase 4 (ML inference) + Phase 5 (advisory) |
| M2 | Crop Risk Radar | Phase 8 (zone scoring) + Phase 9 (officer map) + Phase 10 (weather/flood) |
| M3 | Smart Advisory | Phase 5-6 (pathogen-branched advisory + expert queue entry point) |
| M4 | Geo Disease Hotspot Maps | Phase 8-9 (zone scoring service + hotspot map) |
| M5 | Expert Validation Loop | Phase 7 (expert queue, confirm/correct, feeds retraining_data) |

This M1-M5 grouping is a good level to present at in a demo — five clear
modules instead of 14 build phases — while the underlying phases remain the
actual implementation checklist for your AI agent.
