-- Create logging table for scan operations
CREATE TABLE IF NOT EXISTS scan_logs (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    log_level VARCHAR(10) NOT NULL,
    component VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    file_path TEXT,
    error_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_scan_logs_session ON scan_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_scan_logs_level ON scan_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_scan_logs_created ON scan_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_scan_logs_component ON scan_logs(component);

-- Create scan session summary table
CREATE TABLE IF NOT EXISTS scan_sessions (
    id UUID PRIMARY KEY,
    scan_type VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    files_processed INTEGER DEFAULT 0,
    files_successful INTEGER DEFAULT 0,
    files_failed INTEGER DEFAULT 0,
    directories_processed INTEGER DEFAULT 0,
    total_data_mb DECIMAL,
    performance_metrics JSONB,
    config_used TEXT,
    status VARCHAR(20) DEFAULT 'running'
); 