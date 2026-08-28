# Alembic migrations for Kisan Saathi backend
# Phase 1 will add: jurisdictions, officials, farmers, crop_entries,
#   disease_reports, disease_lookup, weather_daily, zone_status,
#   subsidy_flags, retraining_data

# To initialize (run once from /backend):
#   alembic init alembic
#   alembic revision --autogenerate -m "initial schema"
#   alembic upgrade head

# env.py will be configured to use settings.DB_URL (synchronous psycopg2
# connection for migrations, async engine for app runtime)
