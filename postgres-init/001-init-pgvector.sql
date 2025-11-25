-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Optional: Create a sample vectors table for testing
CREATE TABLE IF NOT EXISTS test_vectors (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(384)
);
