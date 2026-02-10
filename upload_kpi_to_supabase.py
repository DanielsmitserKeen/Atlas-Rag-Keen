"""
Upload KPI documents to Supabase database
"""

import json
import psycopg2
from psycopg2.extras import execute_values
import openai
from openai import OpenAI
import os
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(os.getenv('SUPABASE_DB_URL'))

def get_embedding(text):
    """Generate embedding for text using OpenAI"""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def upload_kpi_documents(json_file='kpi_documents.json'):
    """Upload KPI documents to Supabase"""
    
    # Load documents
    print(f"Loading documents from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    print(f"✓ Loaded {len(documents)} documents")
    
    # Connect to database
    print("Connecting to Supabase...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if documents already exist
    print("Checking for existing KPI documents...")
    cursor.execute("""
        SELECT COUNT(*) FROM documents 
        WHERE filename LIKE 'KPI_Dashboard_%' 
           OR filename LIKE 'Company_%KPI%'
           OR filename LIKE 'Top_Performers_%'
           OR filename LIKE 'ARR_Bucket_Analysis_%'
    """)
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        print(f"\n⚠ Found {existing_count} existing KPI documents in database")
        response = input("Delete existing KPI documents and re-upload? (y/n): ")
        
        if response.lower() == 'y':
            print("Deleting existing KPI documents...")
            cursor.execute("""
                DELETE FROM documents 
                WHERE filename LIKE 'KPI_Dashboard_%' 
                   OR filename LIKE 'Company_%'
                   OR filename LIKE 'Top_Performers_%'
                   OR filename LIKE 'ARR_Bucket_Analysis_%'
            """)
            conn.commit()
            print(f"✓ Deleted {existing_count} existing documents")
        else:
            print("Skipping upload. Exiting...")
            cursor.close()
            conn.close()
            return
    
    # Upload documents
    print(f"\nUploading {len(documents)} documents to Supabase...")
    
    uploaded = 0
    failed = 0
    
    for doc in tqdm(documents, desc="Uploading"):
        try:
            # Generate embedding
            embedding = get_embedding(doc['content'])
            
            # Prepare metadata
            metadata = json.dumps(doc['metadata'])
            
            # Insert into database
            cursor.execute("""
                INSERT INTO documents (filename, content, embedding, chunk_index, total_chunks, file_type, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                doc['filename'],
                doc['content'],
                embedding,
                0,  # Single chunk per document
                1,  # Total chunks = 1
                'KPI_DASHBOARD',
                metadata
            ))
            
            uploaded += 1
            
        except Exception as e:
            print(f"\n✗ Failed to upload {doc['filename']}: {e}")
            failed += 1
            continue
    
    # Commit all changes
    conn.commit()
    
    # Print statistics
    print(f"\n{'='*50}")
    print(f"Upload Complete!")
    print(f"{'='*50}")
    print(f"✓ Successfully uploaded: {uploaded}")
    if failed > 0:
        print(f"✗ Failed: {failed}")
    
    # Get final count
    cursor.execute("""
        SELECT COUNT(*) FROM documents 
        WHERE file_type = 'KPI_DASHBOARD'
    """)
    total_kpi = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_all = cursor.fetchone()[0]
    
    print(f"\nDatabase Statistics:")
    print(f"- Total KPI documents: {total_kpi}")
    print(f"- Total all documents: {total_all}")
    
    # Close connection
    cursor.close()
    conn.close()
    
    print("\n✓ Upload complete! KPI data is now searchable in the RAG system.")

if __name__ == '__main__':
    try:
        upload_kpi_documents()
    except FileNotFoundError:
        print("✗ Error: kpi_documents.json not found")
        print("Run 'python extract_kpi_data.py' first to generate the documents")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
