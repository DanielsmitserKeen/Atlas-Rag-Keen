"""
Test script to verify database connection and OpenAI API
"""

import os
from dotenv import load_dotenv
import psycopg2
from openai import OpenAI

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

print("="*60)
print("Testing Connections...")
print("="*60)

# Test OpenAI
print("\n1. Testing OpenAI API...")
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="test",
        dimensions=1536
    )
    print("   ✓ OpenAI API works!")
    print(f"   ✓ Embedding dimensions: {len(response.data[0].embedding)}")
except Exception as e:
    print(f"   ✗ OpenAI API failed: {e}")
    exit(1)

# Test Database Connection
print("\n2. Testing Supabase Database...")
try:
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"   ✓ Database connected!")
    print(f"   ✓ PostgreSQL version: {version[0][:50]}...")
    
    # Check if pgvector extension exists
    cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    if cursor.fetchone():
        print("   ✓ pgvector extension is installed")
    else:
        print("   ⚠ pgvector extension NOT found - run setup_database.sql first!")
    
    # Check if documents table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'documents'
        );
    """)
    if cursor.fetchone()[0]:
        print("   ✓ documents table exists")
        
        # Count existing documents
        cursor.execute("SELECT COUNT(*) FROM documents;")
        count = cursor.fetchone()[0]
        print(f"   ✓ Current documents in database: {count}")
    else:
        print("   ⚠ documents table NOT found - run setup_database.sql first!")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"   ✗ Database connection failed: {e}")
    exit(1)

print("\n" + "="*60)
print("✓ All connections successful!")
print("="*60)
print("\nNext steps:")
print("1. If pgvector/table warnings above: Run setup_database.sql in Supabase")
print("2. Create a folder with TXT/PDF files to upload")
print("3. Run: python upload_documents.py <folder_path>")
print("="*60)
