-- D1 schema for the first-party page-view counter.
--
-- Apply once after creating the database:
--   npx wrangler d1 create views
--   npx wrangler d1 execute views --remote --file=./migrations/0001_init.sql
-- (drop --remote to seed a local dev copy instead.)

-- One row per path: the running total shown in the footer.
CREATE TABLE IF NOT EXISTS page_views (
  path  TEXT PRIMARY KEY,
  count INTEGER NOT NULL DEFAULT 0
);

-- Short-lived dedup table: one row per (IP, path, UTC day). `k` is a salted
-- SHA-256 hash of IP + path + day (no raw IP/UA is ever stored);
-- `d` is the UTC epoch-day, used by the daily cron to purge past days. There is
-- deliberately no index on `d`: the table only ever holds ~one day of rows, so
-- the cron's scan is cheap, and skipping the index saves an index write on every
-- counted view.
CREATE TABLE IF NOT EXISTS view_dedup (
  k TEXT PRIMARY KEY,
  d INTEGER NOT NULL
);
