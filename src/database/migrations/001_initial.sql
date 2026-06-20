CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    confidence REAL NOT NULL,
    frequency REAL,
    snr REAL,
    source TEXT NOT NULL DEFAULT 'SDR',
    inference_time_ms INTEGER NOT NULL DEFAULT 0,
    model_version TEXT NOT NULL DEFAULT 'unknown',
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    location TEXT NOT NULL DEFAULT 'Unknown',
    timestamp TEXT NOT NULL,
    FOREIGN KEY(signal_id) REFERENCES signals(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    details TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
