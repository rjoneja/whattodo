-- One row per event. No IP addresses, no cookies: "dev" is a random id the phone made up for itself.
CREATE TABLE IF NOT EXISTS ev (
  day TEXT NOT NULL,      -- YYYY-MM-DD (London)
  ts  INTEGER NOT NULL,   -- ms since epoch, server clock
  dev TEXT NOT NULL,      -- random per-phone id
  t   TEXT NOT NULL,      -- event type: visit, share, share_open, swipe, setup_done, trip_open, ...
  a   TEXT,               -- main detail (e.g. swipe kind, who's going, where a visit came from)
  b   TEXT,               -- second detail (e.g. travel choices)
  id  TEXT                -- the idea it was about, if any
);
CREATE INDEX IF NOT EXISTS ev_day_t ON ev(day, t);
CREATE INDEX IF NOT EXISTS ev_dev ON ev(dev, day);

-- Events organisers submit. Raj approves each one by email before it goes live.
CREATE TABLE IF NOT EXISTS sub (
  id      TEXT PRIMARY KEY,
  ts      INTEGER NOT NULL,
  status  TEXT NOT NULL,      -- new → review (emailed) → approved / rejected → published
  url     TEXT, name TEXT, dates TEXT, venue TEXT, details TEXT,
  contact TEXT,               -- optional email from the organiser, only for Raj to reply
  event   TEXT,               -- the event as written up by the pipeline (JSON)
  verdict TEXT                -- the pipeline's view: looks fine / why not
);
CREATE INDEX IF NOT EXISTS sub_status ON sub(status, ts);
