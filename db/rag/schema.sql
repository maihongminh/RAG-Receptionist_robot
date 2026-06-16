-- RAG operational schema.
-- Qdrant remains the vector store. This schema tracks what was indexed so a
-- later incremental sync can compare source content_hash/updated_at safely.

CREATE SCHEMA IF NOT EXISTS robo_rag;

CREATE TABLE IF NOT EXISTS robo_rag.index_manifest (
  id text PRIMARY KEY,
  qdrant_collection text NOT NULL,
  source text NOT NULL,
  source_table text,
  source_view text,
  source_id text NOT NULL,
  chunk_index integer NOT NULL,
  point_id text NOT NULL,
  content_hash text NOT NULL,
  domain text,
  clinic_id text,
  access_level text,
  visibility text,
  language text,
  document_type text,
  source_updated_at text,
  indexed_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (qdrant_collection, source, source_id, chunk_index)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_rag_index_manifest_point_id
ON robo_rag.index_manifest (qdrant_collection, point_id);

CREATE INDEX IF NOT EXISTS idx_rag_index_manifest_source
ON robo_rag.index_manifest (source, source_id);

CREATE INDEX IF NOT EXISTS idx_rag_index_manifest_hash
ON robo_rag.index_manifest (content_hash);
