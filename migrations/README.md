# Database migrations (prep only)

This directory is a lightweight home for SQL schema migrations.

## Current status

- `0001_initial_schema.sql` contains the initial SQLite schema for:
  - `trades`
  - `reports`
- Migration execution is **not wired into app startup** yet.
- The app continues to rely on `services.storage.init_db()` for automatic schema creation.

## Manual usage (optional)

If you want to apply the schema manually to a SQLite DB file:

```bash
sqlite3 achenium.db < migrations/0001_initial_schema.sql
```

If your DB path differs, replace `achenium.db` with your configured `DB_PATH`.

## Suggested next step

When ready, add a migration runner (e.g., a tiny script/CLI command) that:

1. Tracks applied migration files.
2. Applies pending SQL files in order.
3. Keeps app startup behavior explicit (opt-in) rather than automatic until finalized.
