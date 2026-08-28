# Kisan-Saathi 🌾

**AI-powered crop health & pest advisory system — SIH26131**

Kisan-Saathi helps farmers detect crop diseases and pests early, get localized
treatment advisories in their own language, and connects that data to a
jurisdiction-aware dashboard for agriculture officials — from village Pradhan
up to District Magistrate.

## The Problem

Farmers often recognise crop diseases or pest infestations only after visible
damage has spread. Extension staff cover large areas, and expert advice is
often not immediately available. Weather, crop stage, soil condition, and
local pest history all influence risk — but these inputs are rarely combined
into actionable, farm-level alerts. This leads to delayed treatment, excessive
or inappropriate pesticide use, higher costs, residue concerns, and yield loss.

## What This System Does

- 📸 **Farmers scan a crop photo** → get an AI-assisted diagnosis with a
  confidence score, voice-narrated in their regional language
- 🩺 **Pathogen-aware advisories** — treatment steps for fungal/bacterial
  disease; honest "no cure, prevent spread" guidance for viral disease
- 🗺️ **Officials get a live hotspot map**, scoped to their exact jurisdiction
  (village / tehsil / block / district), with Red/Orange/Green zone scoring
  and predictive "Incoming Risk" alerts for downstream villages
- ⛅ **Weather & flood-risk forecasting** flags danger before symptoms even
  appear, using IMD and CWC data
- 🚁 **Drone spray booking** via the Namo Drone Didi network
- 💰 **Automated subsidy workflows** — PMFBY claim packets generated from
  confirmed reports, with audit trails
- 🏬 **Post-harvest guidance** — storage/pledge-financing suggestions via
  WDRA instead of distress selling

## Documentation

| File | What it covers |
|---|---|
| [`PROJECT_OVERVIEW.md`](./PROJECT_OVERVIEW.md) | Full problem statement, solution, roles, features, integration map |
| [`AI_AGENT_BUILD_PROMPT.md`](./AI_AGENT_BUILD_PROMPT.md) | Phased build plan with gates and verification checklists |
| [`PRODUCTION_TABLE.md`](./PRODUCTION_TABLE.md) | Tech stack, role/jurisdiction table, disease coverage summary |
| [`PRODUCTION_WORKFLOW.md`](./PRODUCTION_WORKFLOW.md) | End-to-end system workflows |
| [`disease_lookup.json`](./disease_lookup.json) | Seed data — 35 diseases/pests across major North India crops |

## Tech Stack

React Native (mobile) · React (web dashboard) · FastAPI (backend) ·
PostgreSQL + PostGIS · PyTorch/TensorFlow (ML inference) · Leaflet (maps) ·
Google Cloud/Bhashini (voice) · i18next (localization)

## Team

Vaibhav Kumar Singh and team — SIH 2026, Problem Statement 26131

## Status

🚧 Under active development for Smart India Hackathon.
