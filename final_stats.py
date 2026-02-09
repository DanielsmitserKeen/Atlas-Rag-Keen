import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('SUPABASE_DB_URL'))
cursor = conn.cursor()

print('\n' + '='*60)
print('📊 FINAL UPLOAD STATISTICS')
print('='*60)

cursor.execute('SELECT file_type, COUNT(DISTINCT filename) as files, COUNT(*) as chunks FROM documents GROUP BY file_type ORDER BY files DESC')
print('\nPer bestandstype:')
for row in cursor.fetchall():
    print(f'   {row[0].upper()}: {row[1]} files, {row[2]:,} chunks')

cursor.execute('SELECT COUNT(DISTINCT filename), COUNT(*) FROM documents')
total = cursor.fetchone()
print(f'\n📦 TOTAAL:')
print(f'   Files:  {total[0]}/387 ({total[0]/387*100:.1f}%)')
print(f'   Chunks: {total[1]:,}')

print('\n✅ Upload succesvol voltooid!')
print('='*60)

cursor.close()
conn.close()
