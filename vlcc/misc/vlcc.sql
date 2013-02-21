BEGIN TRANSACTION;

-- Fancy tables

CREATE TABLE IF NOT EXISTS build (
    version VARCHAR(8) PRIMARY KEY,
    state VARCHAR(16)
);

CREATE TABLE IF NOT EXISTS comparison (
    id INTEGER PRIMARY KEY,
    movie VARCHAR(255),
    description TEXT,
    width SMALLINT,
    height SMALLINT,
    length INTEGER,
    fps SMALLINT,
    ready BOOLEAN DEFAULT 0,
    performed DATE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sample (
    comparison_build_id INTEGER,
    interval INTEGER,
    cpu SMALLINT,
    ram SMALLINT,
    threads SMALLINT,
    ram_bytes BIGINT,

    FOREIGN KEY (comparison_build_id) REFERENCES comparison_build(id)
);

CREATE TABLE IF NOT EXISTS comparison_build (
    id INTEGER PRIMARY KEY,
    comparison_id INTEGER,
    build_version VARCHAR(8),

    FOREIGN KEY (comparison_id) REFERENCES comparison(id),
    FOREIGN KEY (build_version) REFERENCES build(version),

    UNIQUE (comparison_id, build_version) ON CONFLICT REPLACE
);

-- Awesome indexes

CREATE INDEX IF NOT EXISTS comparison_performed_index ON comparison (performed);

CREATE INDEX IF NOT EXISTS sample_comparison_build_id_index ON sample (comparison_build_id);

COMMIT;
