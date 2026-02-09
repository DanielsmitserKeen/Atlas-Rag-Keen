# 🚀 Quick Deployment Guide

## For Streamlit Cloud (share via link)

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Add RAG chat application"
git branch -M main
git remote add origin https://github.com/yourusername/yourrepo.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set main file: `rag_chat.py`
6. Click "Deploy"

### Step 3: Add Secrets

In Streamlit Cloud app settings, go to "Secrets" and add:

```toml
OPENAI_API_KEY = "your-openai-api-key-here"
SUPABASE_DB_URL = "postgresql://postgres:your-password@db.yourproject.supabase.co:5432/postgres"
```

### Step 4: Share Your Link!

Your app will be available at: `https://yourappname.streamlit.app`

---

## Important Notes

✅ Make sure database is set up first (`setup_database.sql`)
✅ Upload documents before deploying (`upload_documents.py`)
✅ Never commit `.env` or `secrets.toml` to GitHub
✅ Use Supabase connection pooling for production:
   - In Supabase: Settings → Database → Connection Pooling
   - Use the pooler URL for Streamlit Cloud

## Troubleshooting

**Connection timeout?**
Use Supabase connection pooling URL instead of direct connection.

**App crashes on startup?**
Check that secrets are correctly formatted in Streamlit Cloud (no extra spaces).

**No documents found?**
Make sure you've uploaded documents to the database first using `upload_documents.py`.

## Local Testing

Before deploying, test locally:

```bash
streamlit run rag_chat.py
```

Open your browser at `http://localhost:8501`
