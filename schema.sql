-- superinstance-api schema v1 — one database, five seams
-- (tiles/rooms from plato-cf; bookings from i2i-ledger; intents from pincher;
--  gamma/eta field columns from exoj/quilt-dba; growth via stage-tagged cells)

-- ── Authority: rooms & tiles (plato-cf, Lamport-versioned, tiered) ──
CREATE TABLE IF NOT EXISTS rooms (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT NOT NULL UNIQUE,
  stage      INTEGER NOT NULL DEFAULT 1,      -- quilt-dba growth seam: cells load in stages
  created_ts INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS tiles (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  room_id    INTEGER NOT NULL REFERENCES rooms(id),
  key        TEXT NOT NULL,
  lamport    INTEGER NOT NULL DEFAULT 1,
  content    TEXT NOT NULL,
  tier       TEXT NOT NULL DEFAULT 'full' CHECK (tier IN ('full','gist','hint')),
  vector_id  TEXT,                            -- Vectorize id (meaning seam)
  created_ts INTEGER NOT NULL,
  updated_ts INTEGER NOT NULL,
  UNIQUE (room_id, key)
);

CREATE TABLE IF NOT EXISTS tile_versions (
  tile_id  INTEGER NOT NULL REFERENCES tiles(id),
  lamport  INTEGER NOT NULL,
  content  TEXT NOT NULL,
  tier     TEXT NOT NULL,
  ts       INTEGER NOT NULL,
  PRIMARY KEY (tile_id, lamport)
);

CREATE TABLE IF NOT EXISTS demotion_receipts (
  tile_id       INTEGER NOT NULL REFERENCES tiles(id),
  from_tier     TEXT NOT NULL,
  to_tier       TEXT NOT NULL,
  fact_survival REAL,                         -- tile-memory metric
  lattice_snap  REAL,                         -- tile-memory metric
  method        TEXT NOT NULL,
  ts            INTEGER NOT NULL
);

-- ── Meaning + honesty: bookings (i2i-ledger, with field columns) ──
CREATE TABLE IF NOT EXISTS bookings (
  id          TEXT PRIMARY KEY,               -- UUID string (vector id parity, i2i pattern)
  agent       TEXT NOT NULL,
  gist        TEXT NOT NULL,
  body        TEXT NOT NULL DEFAULT '',
  receipt_url TEXT,
  books_to    TEXT,
  vector_id   TEXT,
  gamma       INTEGER NOT NULL DEFAULT 0,     -- exoj seam: compute cost (ms + tokens/10)
  eta         INTEGER NOT NULL DEFAULT 0,     -- exoj seam: surprise (1000*(1-near_max))
  ts          INTEGER NOT NULL,
  embedded    INTEGER NOT NULL DEFAULT 0      -- honest vector-lag reporting
);

CREATE INDEX IF NOT EXISTS idx_bookings_ts       ON bookings(ts);
CREATE INDEX IF NOT EXISTS idx_bookings_books_to ON bookings(books_to);

-- ── Reflex: intents (pincher seam — the shell that learns) ──
CREATE TABLE IF NOT EXISTS intents (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  intent      TEXT NOT NULL,                  -- canonical phrasing
  context     TEXT NOT NULL DEFAULT '',       -- binding context (room/agent/scope)
  reflex      TEXT NOT NULL,                  -- the compiled answer/action
  confidence  REAL NOT NULL,                  -- compile-time self-consistency
  vector_id   TEXT,                           -- semantic match key
  uses        INTEGER NOT NULL DEFAULT 0,
  created_ts  INTEGER NOT NULL,
  updated_ts  INTEGER NOT NULL,
  UNIQUE (intent, context)
);

-- pinch thresholds: known ≥ 0.92 fires; 0.75–0.92 CONFIRM; else ESCALATE.
-- Escalated resolutions compile back as new intents (cortex teaches shell).

-- ── Growth: canon cells (quilt-dba seam — adding a cell IS advancing a stage; ──
-- E-D1: R1 GROWTH confirmed at eval 299). Design receipt is silent on table
-- specifics, so this is the minimal doctrine-true shape:
--   one canon cell added = room.stage + 1, always receipted; never regressed.
CREATE TABLE IF NOT EXISTS canon_cells (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  room_id    INTEGER NOT NULL REFERENCES rooms(id),
  title      TEXT NOT NULL,                  -- canonical cell name (unique per room)
  body       TEXT NOT NULL DEFAULT '',       -- canonical content
  stage      INTEGER NOT NULL,               -- stage this cell advanced the room TO
  agent      TEXT NOT NULL DEFAULT '',       -- who grew it (token identity wins)
  vector_id  TEXT,                           -- meaning seam (best-effort embed)
  created_ts INTEGER NOT NULL,
  UNIQUE (room_id, title)                    -- no phantom double-advance on retry
);

CREATE TABLE IF NOT EXISTS stage_receipts (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  room_id    INTEGER NOT NULL REFERENCES rooms(id),
  cell_id    INTEGER NOT NULL REFERENCES canon_cells(id),
  from_stage INTEGER NOT NULL,
  to_stage   INTEGER NOT NULL,
  agent      TEXT NOT NULL DEFAULT '',
  ts         INTEGER NOT NULL
);

-- ── Field: conservation view (γ+η ≤ 1585 per agent per day) ──
CREATE VIEW IF NOT EXISTS field_budget AS
SELECT agent, date(ts, 'unixepoch') AS day,
       SUM(gamma) AS gamma_sum, SUM(eta) AS eta_sum,
       SUM(gamma) + SUM(eta) AS total,
       1585 - (SUM(gamma) + SUM(eta)) AS remaining
FROM bookings GROUP BY agent, day;

CREATE INDEX IF NOT EXISTS idx_tiles_room ON tiles(room_id);
CREATE INDEX IF NOT EXISTS idx_tiles_key  ON tiles(key);
CREATE INDEX IF NOT EXISTS idx_cells_room          ON canon_cells(room_id);
CREATE INDEX IF NOT EXISTS idx_stage_receipts_room ON stage_receipts(room_id);
