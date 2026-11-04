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
