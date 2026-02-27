-- Create deiliskipulag tables
-- Run: psql $DATABASE_URL -f scripts/migrate_deiliskipulag.sql
-- Or use: docker compose exec -T planitor python scripts/migrate.py

CREATE TABLE IF NOT EXISTS deiliskipulag_plans (
    skipnr INTEGER PRIMARY KEY,
    heiti VARCHAR,
    sveitarfelag VARCHAR,
    dagsleidrett DATE,
    malsmed VARCHAR,
    numer_mals VARCHAR
);

CREATE TABLE IF NOT EXISTS deiliskipulag_documents (
    id SERIAL PRIMARY KEY,
    skipnr INTEGER REFERENCES deiliskipulag_plans(skipnr),
    doc_type VARCHAR,
    source_url VARCHAR,
    file_size_mb NUMERIC,
    page_count INTEGER,
    pages_rendered_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_deiliskipulag_documents_id ON deiliskipulag_documents(id);
CREATE INDEX IF NOT EXISTS ix_deiliskipulag_documents_skipnr ON deiliskipulag_documents(skipnr);
