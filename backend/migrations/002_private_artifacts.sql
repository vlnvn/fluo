-- Populated only by the private provisioning operation with reviewed checksums.
CREATE TABLE IF NOT EXISTS fluo_artifacts(
  name text PRIMARY KEY CHECK(name IN ('fluo_sensor_stream.csv.gz','fluo_episode_labels.csv')),
  sha256 text NOT NULL CHECK(length(sha256)=64),
  body bytea NOT NULL CHECK(octet_length(body)<=4194304)
);
