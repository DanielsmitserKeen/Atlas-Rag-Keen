"""
Update source_url for a specific document in Supabase
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

def update_document_url(filename: str, new_url: str):
    """Update the source_url for all chunks of a specific document"""
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cursor = conn.cursor()
    
    try:
        # Update source_url in metadata for all chunks of this document
        cursor.execute("""
            UPDATE documents 
            SET metadata = jsonb_set(metadata, '{source_url}', %s::jsonb)
            WHERE filename = %s
        """, (f'"{new_url}"', filename))
        
        updated_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Updated {updated_count} chunks for '{filename}'")
        print(f"   New URL: {new_url}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Update the specific document
    filename = "Boosting the use of artificial intelligence in EU micro, small and medium-sized Enterprises.pdf"
    new_url = "https://www.eesc.europa.eu/sites/default/files/files/qe-02-21-953-en-n.pdf"
    
    update_document_url(filename, new_url)
