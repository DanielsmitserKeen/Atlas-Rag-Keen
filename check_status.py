"""Quick status check - run anytime to see progress"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
cursor = conn.cursor()

# Get stats
cursor.execute("SELECT COUNT(*) FROM documents")
total_chunks = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT filename) FROM documents")
unique_files = cursor.fetchone()[0]

cursor.execute("""
    SELECT filename, COUNT(*) as chunks 
    FROM documents 
    GROUP BY filename 
    ORDER BY MAX(created_at) DESC 
    LIMIT 5
""")
recent_files = cursor.fetchall()

print("=" * 60)
print("📊 UPLOAD STATUS")
print("=" * 60)
print(f"\n✅ Files uploaded:     {unique_files}/387 ({unique_files/387*100:.1f}%)")
print(f"✅ Total chunks:       {total_chunks:,}")
print(f"📦 Avg chunks/file:    {total_chunks//unique_files if unique_files > 0 else 0}")

print(f"\n📄 Last 5 uploaded files:")
for filename, chunks in recent_files:
    print(f"   • {filename[:50]}... ({chunks} chunks)")

remaining = 387 - unique_files
if remaining > 0:
    est_chunks = remaining * (total_chunks // unique_files if unique_files > 0 else 80)
    print(f"\n⏳ Estimated remaining: ~{est_chunks:,} chunks ({remaining} files)")

print("=" * 60)

cursor.close()
conn.close()
