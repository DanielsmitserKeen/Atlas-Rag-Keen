"""
Real-time monitor for document upload progress
"""
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_stats(cursor):
    """Get current upload statistics"""
    # Total chunks
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_chunks = cursor.fetchone()[0]
    
    # Unique files
    cursor.execute("SELECT COUNT(DISTINCT filename) FROM documents")
    unique_files = cursor.fetchone()[0]
    
    # Latest uploaded file
    cursor.execute("""
        SELECT filename, MAX(created_at) as last_upload
        FROM documents 
        GROUP BY filename 
        ORDER BY last_upload DESC 
        LIMIT 1
    """)
    latest = cursor.fetchone()
    
    # File types breakdown
    cursor.execute("""
        SELECT file_type, COUNT(DISTINCT filename) as file_count, COUNT(*) as chunk_count
        FROM documents 
        GROUP BY file_type
    """)
    file_types = cursor.fetchall()
    
    return {
        'total_chunks': total_chunks,
        'unique_files': unique_files,
        'latest_file': latest[0] if latest else None,
        'latest_time': latest[1] if latest else None,
        'file_types': file_types
    }

def main():
    conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
    
    # Get initial stats
    cursor = conn.cursor()
    start_stats = get_stats(cursor)
    start_time = datetime.now()
    start_chunks = start_stats['total_chunks']
    
    print("Starting monitor... Press Ctrl+C to stop\n")
    time.sleep(2)
    
    try:
        while True:
            clear_screen()
            cursor = conn.cursor()
            stats = get_stats(cursor)
            cursor.close()
            
            elapsed = datetime.now() - start_time
            chunks_added = stats['total_chunks'] - start_chunks
            
            # Calculate rate
            if elapsed.total_seconds() > 0:
                chunks_per_sec = chunks_added / elapsed.total_seconds()
                chunks_per_min = chunks_per_sec * 60
            else:
                chunks_per_min = 0
            
            # Estimate time remaining (assuming ~80 chunks per file, 387 files total)
            target_files = 387
            remaining_files = target_files - stats['unique_files']
            if chunks_per_min > 0:
                est_chunks_remaining = remaining_files * 80  # avg chunks per file
                est_minutes_remaining = est_chunks_remaining / chunks_per_min
                eta = datetime.now() + timedelta(minutes=est_minutes_remaining)
            else:
                est_minutes_remaining = None
                eta = None
            
            # Display
            print("=" * 70)
            print(f"📊 DOCUMENT UPLOAD MONITOR - {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 70)
            
            print(f"\n📁 FILES UPLOADED")
            print(f"   Total files:        {stats['unique_files']}/{target_files} ({stats['unique_files']/target_files*100:.1f}%)")
            print(f"   Remaining:          {remaining_files} files")
            
            print(f"\n📦 CHUNKS UPLOADED")
            print(f"   Total chunks:       {stats['total_chunks']:,}")
            print(f"   Added this session: {chunks_added:,}")
            
            print(f"\n⚡ UPLOAD SPEED")
            print(f"   Current rate:       {chunks_per_min:.1f} chunks/min")
            print(f"   Elapsed time:       {str(elapsed).split('.')[0]}")
            
            if est_minutes_remaining and est_minutes_remaining > 0:
                hours = int(est_minutes_remaining // 60)
                mins = int(est_minutes_remaining % 60)
                print(f"   Est. remaining:     {hours}h {mins}m")
                print(f"   ETA:                {eta.strftime('%H:%M:%S')}")
            
            if stats['latest_file']:
                print(f"\n📄 LATEST FILE")
                print(f"   {stats['latest_file'][:60]}...")
                if stats['latest_time']:
                    time_ago = datetime.now(stats['latest_time'].tzinfo) - stats['latest_time']
                    print(f"   Uploaded {int(time_ago.total_seconds())}s ago")
            
            print(f"\n📊 FILE TYPES")
            for ft in stats['file_types']:
                print(f"   {ft[0].upper()}: {ft[1]} files, {ft[2]:,} chunks")
            
            print("\n" + "=" * 70)
            print("Refreshing every 5 seconds... (Ctrl+C to stop)")
            print("=" * 70)
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n✓ Monitor stopped")
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
