# 📄 Document Uploader naar Supabase met Vector Embeddings

Upload TXT en PDF bestanden naar Supabase met OpenAI embeddings voor RAG (Retrieval Augmented Generation) toepassingen.

## 🚀 Features

- ✅ Ondersteunt TXT en PDF bestanden
- ✅ Automatische text chunking met overlap voor betere context
- ✅ OpenAI embeddings (text-embedding-3-small, 1536 dimensies)
- ✅ Opslag in Supabase met pgvector
- ✅ Metadata tracking (bestandsnaam, type, chunk info, hash)
- ✅ Progress bars en duidelijke feedback
- ✅ Klaar voor RAG chatbot implementatie

## 📋 Vereisten

- Python 3.8 of hoger
- Supabase account met database toegang
- OpenAI API key

## 🛠️ Installatie

### 1. Clone/Download dit project

```bash
cd "c:\Users\mdani\Desktop\Upload Files To Supabase"
```

### 2. Installeer Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configureer environment variables

Open het `.env` bestand en update:

```env
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.sbttvzflkoziqolkzgfq.supabase.co:5432/postgres
```

⚠️ **Belangrijk**: Vervang `[YOUR-PASSWORD]` met je echte Supabase database wachtwoord!

### 4. Setup Supabase database

Voer het SQL script uit in je Supabase SQL Editor:

1. Ga naar je Supabase dashboard
2. Klik op "SQL Editor"
3. Maak een nieuwe query
4. Kopieer de inhoud van `setup_database.sql` en voer uit

Dit creëert:
- `pgvector` extension
- `documents` tabel met vector kolom
- Indexes voor snelle searches
- `match_documents()` functie voor semantic search

## 📝 Gebruik

### Bestanden uploaden

```bash
python upload_documents.py "pad/naar/je/bestanden"
```

**Voorbeelden:**

```bash
# Upload alle TXT en PDF bestanden uit de documents map
python upload_documents.py ./documents

# Upload vanaf een absolute pad
python upload_documents.py "C:\Users\mdani\Documents\Artikelen"
```

### Output

Het script laat zien:
- Hoeveel bestanden gevonden zijn
- Progress per bestand
- Aantal chunks per bestand
- Totaal aantal geüploade chunks
- Eventuele errors

```
============================================================
Found 3 files to upload
============================================================

Processing: artikel1.txt
  Split into 5 chunks
  Uploading chunks: 100%|████████████| 5/5
✓ Successfully uploaded 5/5 chunks

Processing: rapport.pdf
  Split into 12 chunks
  Uploading chunks: 100%|████████████| 12/12
✓ Successfully uploaded 12/12 chunks

============================================================
Upload Complete!
  Successfully uploaded: 2/3 files
  Total chunks created: 17
============================================================
```

## 🔧 Configuratie

Je kunt de chunking instellingen aanpassen in `upload_documents.py`:

```python
CHUNK_SIZE = 1000      # Aantal karakters per chunk
CHUNK_OVERLAP = 200    # Overlap tussen chunks voor context
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI model
```

### Embedding Model Opties:

- `text-embedding-3-small` (1536 dim) - **Aanbevolen**: goedkoop en effectief
- `text-embedding-3-large` (3072 dim) - Betere kwaliteit, duurder

## 📊 Database Schema

De `documents` tabel bevat:

| Kolom | Type | Beschrijving |
|-------|------|--------------|
| `id` | UUID | Unieke identifier |
| `filename` | TEXT | Originele bestandsnaam |
| `file_type` | TEXT | txt of pdf |
| `content` | TEXT | Tekst content van de chunk |
| `chunk_index` | INTEGER | Index van deze chunk (0-based) |
| `total_chunks` | INTEGER | Totaal aantal chunks voor dit bestand |
| `embedding` | VECTOR(1536) | OpenAI embedding vector |
| `metadata` | JSONB | Extra info (file_size, hash, etc) |
| `created_at` | TIMESTAMP | Aanmaak timestamp |

## 🔍 Volgende Stappen: RAG Chat

Nu je documenten in de database staan, kun je:

1. **Semantic Search** gebruiken met de `match_documents()` functie:

```sql
SELECT * FROM match_documents(
    query_embedding := '[your_query_embedding]',
    match_threshold := 0.7,
    match_count := 5
);
```

2. **RAG Chatbot bouwen** die:
   - User query omzet naar embedding
   - Relevante chunks ophaalt met `match_documents()`
   - Context + query naar LLM stuurt
   - Bronnen en quotes teruggeeft

## 🚀 Deployment naar Streamlit Cloud

### Lokaal Testen (eerst doen!)

```bash
cd "c:\Users\mdani\Desktop\Upload Files To Supabase"
streamlit run rag_chat.py
```

Zorg dat je eerst documenten hebt geüpload met `upload_documents.py`.

### Deployen naar Streamlit Cloud (deel via link!)

1. **Push je code naar GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/yourrepo.git
   git push -u origin main
   ```

2. **Ga naar [share.streamlit.io](https://share.streamlit.io)**
   - Log in met je GitHub account
   - Klik op "New app"
   - Selecteer je repository
   - Main file: `rag_chat.py`
   - Klik op "Deploy"

3. **Voeg Secrets toe**
   - Klik in Streamlit Cloud op je app
   - Ga naar "Settings" → "Secrets"
   - Kopieer de inhoud van `.streamlit/secrets.toml.example`
   - Vul je echte API keys in:
   
   ```toml
   OPENAI_API_KEY = "sk-proj-..."
   SUPABASE_DB_URL = "postgresql://postgres:password@db.yourproject.supabase.co:5432/postgres"
   ```

4. **Deel je link!**
   - Je app is nu beschikbaar op: `https://yourapp.streamlit.app`
   - Deel deze link met anderen
   - Updates pushen naar GitHub updates automatisch de app

### Deployment Checklist

✅ Database is opgezet met `setup_database.sql`
✅ Documenten zijn geüpload met `upload_documents.py`
✅ `.env` en `.streamlit/secrets.toml` staan in `.gitignore`
✅ Code is gepusht naar GitHub (zonder secrets!)
✅ Secrets zijn toegevoegd in Streamlit Cloud
✅ App is getest en werkt

### Troubleshooting Deployment

**App crasht bij opstarten:**
- Check of secrets correct zijn ingevoerd in Streamlit Cloud
- Controleer database connectie string (geen spaties, juist format)

**Database connection timeout:**
- In Supabase Settings → Database → Connection pooling
- Gebruik Connection pooling URL voor Streamlit Cloud
- Format: `postgresql://postgres.project:password@aws-0-region.pooler.supabase.com:5432/postgres`

**"No documents found" error:**
- Upload eerst documenten met `upload_documents.py` lokaal
- Database moet chunks bevatten voordat RAG chat werkt

## ❗ Troubleshooting

### Database connectie fout
- Check of je wachtwoord correct is in `.env`
- Controleer of je Supabase project actief is
- Zorg dat je IP adres toegang heeft (Supabase settings)

### Encoding errors bij TXT bestanden
- Het script probeert eerst UTF-8, dan Latin-1
- Voor andere encodings, pas `read_txt_file()` aan

### PDF extractie problemen
- Sommige PDFs (scans, images) hebben geen tekst
- Gebruik OCR tools voor gescande documenten

### OpenAI API errors
- Check of je API key geldig is
- Controleer je OpenAI credit balance
- Rate limits: het script verwerkt chunks sequentieel

## 💰 Kosten Indicatie

**OpenAI Embeddings** (text-embedding-3-small):
- ~$0.02 per 1 miljoen tokens
- 1000 karakters ≈ 250 tokens
- 100 chunks van 1000 karakters ≈ $0.0005

**Supabase**:
- Gratis tier: 500MB database
- Vector storage: ongeveer even groot als je tekstbestanden

## 📄 Licentie

MIT License - Vrij te gebruiken voor commerciële en persoonlijke projecten.

## 🤝 Vragen?

Als je tegen problemen aanloopt of vragen hebt over de implementatie, laat het weten!
