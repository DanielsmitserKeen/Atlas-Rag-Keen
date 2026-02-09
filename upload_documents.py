"""
Document Uploader to Supabase with Vector Embeddings
Uploads TXT and PDF files, creates embeddings using OpenAI, and stores them in Supabase
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import execute_values
from openai import OpenAI
from dotenv import load_dotenv
import PyPDF2
import hashlib
import time
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

# OpenAI settings
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions, cost-effective
EMBEDDING_DIMENSIONS = 1536
CHUNK_SIZE = 1000  # characters per chunk
CHUNK_OVERLAP = 200  # overlap between chunks for context


class DocumentUploader:
    """Handles uploading documents to Supabase with vector embeddings"""

    def __init__(self):
        """Initialize the uploader with OpenAI and Supabase connections"""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        if not SUPABASE_DB_URL:
            raise ValueError("SUPABASE_DB_URL not found in environment variables")

        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.db_conn = None
        self._connect_to_database()

    def _connect_to_database(self):
        """Establish connection to Supabase database"""
        try:
            self.db_conn = psycopg2.connect(SUPABASE_DB_URL)
            print("✓ Connected to Supabase database")
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            raise

    def read_txt_file(self, file_path: Path) -> str:
        """Read content from a TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    def read_pdf_file(self, file_path: Path) -> str:
        """Read content from a PDF file"""
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, 
                   overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence or word boundary if not at end
            if end < text_length:
                # Look for sentence end
                last_period = chunk.rfind('. ')
                last_newline = chunk.rfind('\n')
                last_break = max(last_period, last_newline)
                
                if last_break > chunk_size * 0.5:  # Only break if we're past halfway
                    chunk = chunk[:last_break + 1]
                    end = start + last_break + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return [c for c in chunks if c]  # Remove empty chunks

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text using OpenAI with retry logic"""
        try:
            response = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                dimensions=EMBEDDING_DIMENSIONS
            )
            time.sleep(0.1)  # Small delay to avoid rate limiting
            return response.data[0].embedding
        except Exception as e:
            print(f"✗ Failed to create embedding (retrying...): {e}", flush=True)
            raise

    def upload_document(self, file_path: Path) -> int:
        """Upload a single document to Supabase"""
        print(f"\n{'='*60}", flush=True)
        print(f"📄 Processing: {file_path.name}", flush=True)
        print(f"{'='*60}", flush=True)

        # Read file content
        file_extension = file_path.suffix.lower()
        try:
            print(f"   Reading {file_extension} file...", flush=True)
            if file_extension == '.txt':
                content = self.read_txt_file(file_path)
            elif file_extension == '.pdf':
                content = self.read_pdf_file(file_path)
            else:
                print(f"✗ Unsupported file type: {file_extension}", flush=True)
                return 0
            print(f"   ✓ Read {len(content)} characters", flush=True)
        except Exception as e:
            print(f"✗ Failed to read file: {e}", flush=True)
            return 0

        if not content.strip():
            print(f"✗ File is empty or could not extract content", flush=True)
            return 0

        # Chunk the content
        print(f"   Chunking text...", flush=True)
        chunks = self.chunk_text(content)
        print(f"   ✓ Split into {len(chunks)} chunks", flush=True)

        # Process each chunk
        uploaded_count = 0
        cursor = self.db_conn.cursor()

        print(f"\n   Uploading chunks to Supabase:", flush=True)
        for idx, chunk in enumerate(chunks):
            try:
                # Progress indicator
                print(f"   [{idx+1}/{len(chunks)}] Creating embedding...", end=' ', flush=True)
                embedding = self.create_embedding(chunk)
                print(f"✓ Uploading...", end=' ', flush=True)

                # Prepare metadata
                metadata = {
                    "original_filename": file_path.name,
                    "file_size": file_path.stat().st_size,
                    "chunk_size": len(chunk),
                    "file_hash": hashlib.md5(content.encode()).hexdigest()
                }

                # Insert into database
                cursor.execute(
                    """
                    INSERT INTO documents 
                    (filename, file_type, content, chunk_index, total_chunks, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        file_path.name,
                        file_extension[1:],  # Remove the dot
                        chunk,
                        idx,
                        len(chunks),
                        embedding,
                        psycopg2.extras.Json(metadata)
                    )
                )
                uploaded_count += 1
                print(f"✓", flush=True)

            except Exception as e:
                print(f"\n   ✗ Failed to upload chunk {idx}: {e}", flush=True)
                continue

        self.db_conn.commit()
        cursor.close()
        print(f"\n   ✅ Successfully uploaded {uploaded_count}/{len(chunks)} chunks!", flush=True)
        return uploaded_count

    def upload_directory(self, directory_path: str) -> Dict[str, int]:
        """Upload all TXT and PDF files from a directory"""
        dir_path = Path(directory_path)
        
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")

        # Find all TXT and PDF files
        files = list(dir_path.glob("*.txt")) + list(dir_path.glob("*.pdf"))
        
        if not files:
            print(f"✗ No TXT or PDF files found in {directory_path}")
            return {"total_files": 0, "total_chunks": 0}

        print(f"\n{'='*60}")
        print(f"Found {len(files)} files to upload")
        print(f"{'='*60}")

        total_chunks = 0
        successful_files = 0

        for file_path in files:
            try:
                chunks_uploaded = self.upload_document(file_path)
                if chunks_uploaded > 0:
                    total_chunks += chunks_uploaded
                    successful_files += 1
            except Exception as e:
                print(f"✗ Error processing {file_path.name}: {e}")
                continue

        print(f"\n{'='*60}")
        print(f"Upload Complete!")
        print(f"  Successfully uploaded: {successful_files}/{len(files)} files")
        print(f"  Total chunks created: {total_chunks}")
        print(f"{'='*60}\n")

        return {
            "total_files": len(files),
            "successful_files": successful_files,
            "total_chunks": total_chunks
        }

    def close(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
            print("✓ Database connection closed")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python upload_documents.py <directory_path>")
        print("\nExample: python upload_documents.py ./documents")
        sys.exit(1)

    directory_path = sys.argv[1]

    try:
        uploader = DocumentUploader()
        results = uploader.upload_directory(directory_path)
        uploader.close()
        
        if results["successful_files"] == 0:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
