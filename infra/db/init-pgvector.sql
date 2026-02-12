-- Enable pgvector extension on the ailine database.
-- Mounted into /docker-entrypoint-initdb.d/ by docker-compose.
CREATE EXTENSION IF NOT EXISTS vector;
