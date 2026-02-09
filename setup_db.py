"""Setup the database schema automatically"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

print("=" * 60)
print("SETTING UP DATABASE SCHEMA")
print("=" * 60)

conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
conn.autocommit = True
cursor = conn.cursor()

print("\n1. Enabling pgvector extension...", flush=True)
cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
print("   ✓ pgvector enabled")

print("\n2. Creating documents table...", flush=True)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        content TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        total_chunks INTEGER NOT NULL,
        embedding vector(1536),
        metadata JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
""")
print("   ✓ documents table created")

print("\n3. Creating indexes...", flush=True)
# Note: HNSW index is better for high dimensions but needs more memory
# For now we skip the vector index and rely on sequential scan (fine for smaller datasets)
# Or use: USING hnsw (embedding vector_cosine_ops) if available in your Supabase version
try:
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS documents_embedding_idx 
        ON documents 
        USING hnsw (embedding vector_cosine_ops);
    """)
    print("   ✓ Vector similarity index (HNSW) created")
except Exception as e:
    print(f"   ⚠ Vector index skipped (will use sequential scan): {e}")
    # Sequential scan works fine for up to ~100k vectors

cursor.execute("CREATE INDEX IF NOT EXISTS documents_filename_idx ON documents(filename);")
cursor.execute("CREATE INDEX IF NOT EXISTS documents_file_type_idx ON documents(file_type);")
print("   ✓ Filename and file_type indexes created")

print("\n4. Creating search function...", flush=True)
cursor.execute("""
    CREATE OR REPLACE FUNCTION match_documents(
        query_embedding vector(1536),
        match_threshold FLOAT DEFAULT 0.5,
        match_count INT DEFAULT 10
    )
    RETURNS TABLE(
        id UUID,
        filename TEXT,
        file_type TEXT,
        content TEXT,
        chunk_index INTEGER,
        similarity FLOAT
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY
        SELECT
            documents.id,
            documents.filename,
            documents.file_type,
            documents.content,
            documents.chunk_index,
            1 - (documents.embedding <=> query_embedding) AS similarity
        FROM documents
        WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
        ORDER BY documents.embedding <=> query_embedding
        LIMIT match_count;
    END;
    $$;
""")
print("   ✓ match_documents() function created")

cursor.close()
conn.close()

print("\n" + "=" * 60)
print("✅ DATABASE SETUP COMPLETE!")
print("=" * 60)
