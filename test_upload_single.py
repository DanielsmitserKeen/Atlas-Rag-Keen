"""Quick test script to upload a single file"""
import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json

load_dotenv()

print("=" * 60)
print("SINGLE FILE UPLOAD TEST")
print("=" * 60)

# Get first TXT file from folder
folder = Path("Scrape Investors - Partners batch cleaned")
txt_files = list(folder.glob("*.txt"))

if not txt_files:
    print("No TXT files found!")
    sys.exit(1)

test_file = txt_files[0]
print(f"\n📄 Testing with: {test_file.name}")
print(f"   File size: {test_file.stat().st_size} bytes")

# Read content
print(f"\n1. Reading file...", flush=True)
content = test_file.read_text(encoding='utf-8')
print(f"   ✓ Read {len(content)} characters")

# Take first 500 chars as test chunk
test_chunk = content[:500]
print(f"\n2. Creating embedding for first 500 chars...", flush=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=test_chunk,
    dimensions=1536
)
embedding = response.data[0].embedding
print(f"   ✓ Embedding created: {len(embedding)} dimensions")

# Insert into database
print(f"\n3. Inserting into Supabase...", flush=True)
conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO documents 
    (filename, file_type, content, chunk_index, total_chunks, embedding, metadata)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id
    """,
    (
        test_file.name,
        "txt",
        test_chunk,
        0,
        1,
        embedding,
        Json({"test": True, "file_size": test_file.stat().st_size})
    )
)

doc_id = cursor.fetchone()[0]
conn.commit()
print(f"   ✓ Inserted! Document ID: {doc_id}")

# Verify
cursor.execute("SELECT COUNT(*) FROM documents")
count = cursor.fetchone()[0]
print(f"\n4. Verification:")
print(f"   ✓ Total documents in database: {count}")

cursor.close()
conn.close()

print("\n" + "=" * 60)
print("✅ TEST SUCCESSFUL!")
print("=" * 60)
