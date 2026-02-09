"""
Robust uploader that skips already uploaded files
"""
import os
import sys
from pathlib import Path
from typing import List, Set
import psycopg2
from psycopg2.extras import Json
from openai import OpenAI
from dotenv import load_dotenv
import PyPDF2
import hashlib
import time
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


class RobustUploader:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.db_conn = psycopg2.connect(SUPABASE_DB_URL)
        self.uploaded_files = self._get_uploaded_files()
        print(f"✓ Connected - Found {len(self.uploaded_files)} already uploaded files")

    def _get_uploaded_files(self) -> Set[str]:
        """Get set of filenames already in database"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT DISTINCT filename FROM documents")
        files = {row[0] for row in cursor.fetchall()}
        cursor.close()
        return files

    def read_txt_file(self, file_path: Path) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    def read_pdf_file(self, file_path: Path) -> str:
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def chunk_text(self, text: str) -> List[str]:
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + CHUNK_SIZE
            chunk = text[start:end]
            
            if end < text_length:
                last_period = chunk.rfind('. ')
                last_newline = chunk.rfind('\n')
                last_break = max(last_period, last_newline)
                
                if last_break > CHUNK_SIZE * 0.5:
                    chunk = chunk[:last_break + 1]
                    end = start + last_break + 1

            chunks.append(chunk.strip())
            start = end - CHUNK_OVERLAP

        return [c for c in chunks if c]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=10))
    def create_embedding(self, text: str) -> List[float]:
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            dimensions=EMBEDDING_DIMENSIONS
        )
        time.sleep(0.1)
        return response.data[0].embedding

    def upload_document(self, file_path: Path) -> int:
        # Skip if already uploaded
        if file_path.name in self.uploaded_files:
            print(f"⏭️  SKIP: {file_path.name} (already uploaded)", flush=True)
            return 0

        print(f"\n📄 {file_path.name}", flush=True)

        # Read file
        file_extension = file_path.suffix.lower()
        try:
            if file_extension == '.txt':
                content = self.read_txt_file(file_path)
            elif file_extension == '.pdf':
                content = self.read_pdf_file(file_path)
            else:
                print(f"   ✗ Unsupported: {file_extension}", flush=True)
                return 0
        except Exception as e:
            print(f"   ✗ Read error: {e}", flush=True)
            return 0

        if not content.strip():
            print(f"   ✗ Empty file", flush=True)
            return 0

        # Chunk
        chunks = self.chunk_text(content)
        print(f"   📦 {len(chunks)} chunks", flush=True)

        # Upload chunks
        uploaded = 0
        cursor = self.db_conn.cursor()

        for idx, chunk in enumerate(chunks):
            try:
                if (idx + 1) % 10 == 0 or idx == 0:
                    print(f"   [{idx+1}/{len(chunks)}]", end=' ', flush=True)
                
                embedding = self.create_embedding(chunk)
                
                metadata = {
                    "file_size": file_path.stat().st_size,
                    "chunk_size": len(chunk)
                }

                cursor.execute(
                    """
                    INSERT INTO documents 
                    (filename, file_type, content, chunk_index, total_chunks, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        file_path.name,
                        file_extension[1:],
                        chunk,
                        idx,
                        len(chunks),
                        embedding,
                        Json(metadata)
                    )
                )
                uploaded += 1

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"\n   ✗ Chunk {idx} error: {str(e)[:50]}", flush=True)
                continue

        self.db_conn.commit()
        cursor.close()
        print(f" ✅ {uploaded}/{len(chunks)}", flush=True)
        
        # Mark as uploaded
        self.uploaded_files.add(file_path.name)
        return uploaded

    def upload_directory(self, directory_path: str):
        dir_path = Path(directory_path)
        files = list(dir_path.glob("*.txt")) + list(dir_path.glob("*.pdf"))
        
        print(f"\n{'='*60}")
        print(f"📁 {len(files)} files | {len(self.uploaded_files)} already done")
        print(f"{'='*60}\n")

        total_chunks = 0
        successful = 0

        for file_path in files:
            try:
                chunks = self.upload_document(file_path)
                if chunks > 0:
                    total_chunks += chunks
                    successful += 1
            except KeyboardInterrupt:
                print(f"\n\n⚠️  Interrupted by user")
                break
            except Exception as e:
                print(f"✗ Error: {file_path.name}: {e}", flush=True)
                continue

        print(f"\n{'='*60}")
        print(f"✅ Done: {successful} files, {total_chunks} chunks")
        print(f"{'='*60}\n")

    def close(self):
        if self.db_conn:
            self.db_conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_robust.py <directory_path>")
        sys.exit(1)

    uploader = RobustUploader()
    try:
        uploader.upload_directory(sys.argv[1])
    finally:
        uploader.close()
