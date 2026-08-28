# AI Coding Rules — Kisan-Saathi (Crop Health Advisory Platform)

Mandatory process rules for all AI coding agents (Antigravity, Claude, etc.) working on
this project. AI_AGENT_BUILD_PROMPT.md defines WHAT to build and in what order. This file
defines HOW to build it responsibly. Both apply at all times.

---

## 1. Source of Truth
Before implementation changes, read:
- `PROJECT_OVERVIEW.md` — product scope, roles, integration map
- `PRODUCTION_TABLE.md` — tech stack, role/jurisdiction table, disease coverage
- `PRODUCTION_WORKFLOW.md` — system workflows + MVP module map (M1-M5)
- `AI_AGENT_BUILD_PROMPT.md` — phased build plan, gates, verification checklist
- `disease_lookup.json` — disease/pest seed data (38 entries)

If code conflicts with these documents, do NOT silently redesign. Explain the conflict and
ask for a decision.

## 2. Work Incrementally
One phase (per AI_AGENT_BUILD_PROMPT.md) → implementation → test → review → git checkpoint
→ next phase. Never build multiple phases in one uninterrupted pass. Large features within
a phase must be broken into independently testable tasks.

## 3. Planning Before Large Changes
Before a task touching multiple files: inspect existing code, explain the approach, list
files expected to change, identify risks, state acceptance criteria (= that phase's Gate).
Do not start without a plan the human can review — this is how the Phase 1 pre-seed review
worked, and it should be the norm for every phase, not a one-off.

## 4. Preserve Existing Functionality
Never modify working functionality unnecessarily. Understand current behavior and
dependencies before changing code. Prefer localized changes over broad rewrites.

## 5. Smallest Change Principle
Fix bugs with the smallest change that addresses the root cause. Do not rewrite a whole
file for a small bug. Do not refactor unrelated code during a bug fix unless asked.

## 6. Architecture Boundaries (as actually built)
```
web-dashboard/  -> React + Vite. UI, role-based routing after login. Talks to backend
                    via API only.
backend/        -> FastAPI. Auth, authorization, business logic, jurisdiction filtering,
                    zone scoring service, database operations, orchestration.
ml-model/       -> Independent inference service. Image preprocessing, model inference,
                    prediction, confidence, pathogen_type. Nothing else.
PostgreSQL+PostGIS -> Persistent data (10 tables per Phase 1).
```
Frontend must NOT: connect directly to the database, hold API keys, call ml-model
directly (route through backend), or make authoritative authorization decisions.
Backend must NEVER trust client-supplied user IDs, roles, or ownership claims.

## 7. AI/ML Service Rules
The ml-model service must NOT: manage users/auth, make database authorization decisions,
directly modify application data, invent uncertain diagnoses, or claim expert validation
it hasn't received. Confidence < 70% → `needs_expert_review`, never a fabricated diagnosis
(per AI_AGENT_BUILD_PROMPT.md Phase 4).

## 8. Risk Engine Rules
Do not confuse AI confidence (how sure the model is about ONE image) with zone risk score
(how concerning the situation is given ALL evidence — reports, weather, severity, spread).
These are separate calculations. Risk/zone scoring logic lives ONLY in the backend's zone
scoring service (Phase 8) — never duplicated in the frontend or ml-model service.

## 9. Advisory / Recommendation Rules
Recommendations are controlled agricultural guidance, not open-ended AI prescriptions.
MANDATORY pathogen-type branching (per AI_AGENT_BUILD_PROMPT.md Phase 6):
- fungal/bacterial/insect -> IPM steps, dosage, pre-harvest interval from disease_lookup.json
- viral -> NEVER a treatment/cure step. Isolate + resistant-variety-next-season ONLY.
- nematode -> soil treatment + rotation guidance
Never invent a pesticide product, dosage, or safety instruction not present in
disease_lookup.json's ipm_steps[].

## 10. Expert Validation Rules
Never overwrite an AI prediction with an expert correction. Store BOTH: original AI result
+ expert decision + corrected diagnosis (if any) + expert comments, in `retraining_data`
(per Phase 1's schema). This preserves traceability for model evaluation.

## 11. Security Rules
Never hardcode API keys, passwords, or secrets. Never commit real .env values (only
.env.example with empty keys). Never trust client-side authorization. Never return
password hashes. Never log credentials.

## 12. Dependencies
Do not add a new dependency automatically. Before adding one: check if an existing
dependency already solves it, explain why it's needed, check for unnecessary complexity.

## 13. Testing Rules — "Done" requires proof, not a claim
A feature is NOT complete because it compiles, the dev server starts, or the agent says
"done." Per AI_AGENT_BUILD_PROMPT.md's Gate/Verification system: test happy path, failure
path, boundary cases, authorization, and existing functionality before calling a phase
complete. NEVER report "test passed" unless the test was actually executed — show the
output, don't summarize a claim.

## 14. Do Not Guess
When information is unavailable, say so. Do not invent API responses, database records,
AI predictions, weather values, expert confirmations, test results, or file contents.

## 15. Bug-Fixing Protocol
Reproduce -> inspect (error/logs/stack trace) -> identify root cause -> explain it ->
smallest fix -> run relevant tests -> verify nothing else broke -> report:
`Root cause / Fix / Files changed / Tests run / Result / Remaining issues`.

## 16. Git Rules
Do not commit automatically unless instructed. Normal flow: review changes -> test ->
commit -> push. Every completed phase (per AI_AGENT_BUILD_PROMPT.md) = one checkpoint.
Commit message format: reference the phase, e.g. "Phase 1 complete: schema + seed data
(38 diseases, 9 villages)".

## 17. Task Completion Report
After every substantial task, report: Task / Files created / Files modified / Dependencies
added / Tests run / Verification / Known issues / Next suggested step. This is the same
discipline as AI_AGENT_BUILD_PROMPT.md's WORKLOG.md requirement — feed reports into it.

## 18. Product Scope Rules
Respect the phases in AI_AGENT_BUILD_PROMPT.md. Do not build ahead into a later phase's
scope "because it's technically interesting" — e.g., do not build drone booking (Phase 11)
while working on Phase 3. Flag good ideas for later phases instead of building them early.

## 19. Beginner-Friendly Code
This project may be reviewed/extended by developers still learning. Prefer clear names,
small functions, simple control flow, explicit error handling, minimal duplication, and
comments where logic isn't obvious (especially pathogen-type branching and zone scoring —
these are the parts a future reader most needs explained).

## 20. Stop Conditions
Stop and report instead of continuing when: a required dependency is missing, architecture
is unclear, documentation conflicts, a destructive change seems necessary, a required
external service (weather API, AgriStack, database) is unavailable, a test fails and the
root cause is unclear, or credentials are required but unavailable. Do not invent a
workaround just to keep moving.

## 21. Core Principle
The AI coding agent is an implementation assistant, not the final authority on product
scope, architecture, security, agricultural advice, or deployment decisions. The human
developer approves important decisions — this is why every phase has a human-reviewed Gate.

## 22. Project Philosophy
```
PLAN -> IMPLEMENT -> TEST -> REVIEW -> COMMIT -> DOCUMENT -> NEXT PHASE
```
Never: PLAN -> BUILD EVERYTHING -> HOPE.
