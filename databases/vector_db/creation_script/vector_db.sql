-- Enable the pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a table for vector embeddings with chunk size 256
CREATE TABLE vector_embeddings_256 (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER NOT NULL,
    embedding vector(256),
    text TEXT,
    database TEXT
);

-- Create a table for vector embeddings with chunk size 512
CREATE TABLE vector_embeddings_512 (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER NOT NULL,
    embedding vector(512),
    text TEXT,
    database TEXT
);

-- Create a table for vector embeddings with chunk size 512
CREATE TABLE vector_embeddings_1536 (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER NOT NULL,
    embedding vector(1536),
    text TEXT,
    database TEXT
);
