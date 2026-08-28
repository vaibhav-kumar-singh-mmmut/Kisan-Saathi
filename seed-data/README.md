# Seed Data

This directory will contain:
- `disease_lookup.json` — already at repo root (35 entries, source of truth for zone scoring)
- `villages.sql` — 6–10 mock villages spanning Red / Orange / Green / Incoming Risk zones
- `officials.sql` — mock officials across Revenue and Development wings
- `farmers.sql` — mock farmer records with crop_entries
- `disease_reports.sql` — pre-seeded reports matching Phase 1's hand-verification scenarios
- `weather_daily.sql` — mock daily weather records to trigger weather_triggers

Seed scripts will be applied via Alembic data migrations in Phase 1.
