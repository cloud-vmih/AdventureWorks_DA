CREATE TABLE IF NOT EXISTS audit.etl_log (
    log_id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'STARTED', 'COMPLETED', 'FAILED'
    records_affected INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);
