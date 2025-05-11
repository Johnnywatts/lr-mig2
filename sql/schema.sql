-- Database schema for Lightroom File Management Utility

-- File metadata table
CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    filepath TEXT NOT NULL,
    filesize BIGINT NOT NULL,
    created_date TIMESTAMP,
    modified_date TIMESTAMP,
    exif_data JSONB,
    category CHAR(1),  -- 'P' for Personal, 'W' for Work
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Directory structure table
CREATE TABLE IF NOT EXISTS directories (
    id SERIAL PRIMARY KEY,
    dirpath TEXT NOT NULL,
    parent_id INTEGER REFERENCES directories(id),
    category CHAR(1),  -- 'P' for Personal, 'W' for Work
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Duplicate tracking table
CREATE TABLE IF NOT EXISTS duplicates (
    id SERIAL PRIMARY KEY,
    original_file_id INTEGER REFERENCES files(id),
    duplicate_file_id INTEGER REFERENCES files(id),
    match_type VARCHAR(50),  -- 'exact', 'partial_plus', 'partial_minus'
    match_percentage INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_files_filepath ON files(filepath);
CREATE INDEX IF NOT EXISTS idx_directories_dirpath ON directories(dirpath);
CREATE INDEX IF NOT EXISTS idx_files_category ON files(category);
CREATE INDEX IF NOT EXISTS idx_directories_category ON directories(category); 