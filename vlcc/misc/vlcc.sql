BEGIN TRANSACTION;

-- Fancy tables

CREATE TABLE IF NOT EXISTS build (
    version TEXT PRIMARY KEY,
    state TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS comparison (
    id INTEGER PRIMARY KEY,
    movie TEXT,
    description TEXT,
    width INTEGER,
    height INTEGER,
    length INTEGER,
    fps INTEGER,
    published TEXT
);

CREATE TABLE IF NOT EXISTS sample (
    comparison_build_id INTEGER,
    interval INTEGER,
    ram INTEGER,
    threads INTEGER,
    cpu_percent INTEGER,
    ram_percent INTEGER,

    FOREIGN KEY (comparison_build_id) REFERENCES comparison_build(id)
);

CREATE TABLE IF NOT EXISTS comparison_build (
    id INTEGER PRIMARY KEY,
    comparison_id INTEGER,
    build_version TEXT,

    FOREIGN KEY (comparison_id) REFERENCES comparison(id),
    FOREIGN KEY (build_version) REFERENCES build(version),

    UNIQUE (comparison_id, build_version) ON CONFLICT REPLACE
);

-- Awesome indexes

CREATE INDEX IF NOT EXISTS comparison_published_index ON comparison (published);

CREATE INDEX IF NOT EXISTS sample_comparison_build_id_index ON sample (comparison_build_id);

COMMIT;
