-- New serverless demo database only; no SQLite/legacy data import.
CREATE TABLE IF NOT EXISTS fluo_schema(singleton boolean PRIMARY KEY CHECK(singleton), version integer NOT NULL);
INSERT INTO fluo_schema VALUES(TRUE,1) ON CONFLICT DO NOTHING;
DO $$ BEGIN IF (SELECT version FROM fluo_schema WHERE singleton) <> 1 THEN
  RAISE EXCEPTION 'Unsupported Fluo schema version'; END IF; END $$;
CREATE TABLE IF NOT EXISTS fluo_guests(
  digest text PRIMARY KEY CHECK(length(digest)=64), csrf text NOT NULL,
  expires double precision NOT NULL, revoked boolean NOT NULL DEFAULT FALSE,
  mutations integer NOT NULL DEFAULT 0 CHECK(mutations>=0)
);
CREATE INDEX IF NOT EXISTS fluo_guests_expiry ON fluo_guests(expires);
CREATE TABLE IF NOT EXISTS fluo_sessions(
  id text PRIMARY KEY, digest text NOT NULL REFERENCES fluo_guests(digest) ON DELETE CASCADE,
  payload jsonb NOT NULL CHECK(octet_length(payload::text)<=8192)
);
CREATE INDEX IF NOT EXISTS fluo_sessions_owner ON fluo_sessions(digest);
CREATE TABLE IF NOT EXISTS fluo_reviews(
  session_id text REFERENCES fluo_sessions(id) ON DELETE CASCADE,
  event_id text, payload jsonb NOT NULL CHECK(octet_length(payload::text)<=1048576),
  PRIMARY KEY(session_id,event_id)
);
CREATE TABLE IF NOT EXISTS fluo_preferences(
  session_id text PRIMARY KEY REFERENCES fluo_sessions(id) ON DELETE CASCADE,
  payload jsonb NOT NULL CHECK(octet_length(payload::text)<=1024)
);
CREATE TABLE IF NOT EXISTS fluo_budgets(
  name text, period bigint, hits integer NOT NULL CHECK(hits>0), expires bigint NOT NULL,
  PRIMARY KEY(name,period)
);
