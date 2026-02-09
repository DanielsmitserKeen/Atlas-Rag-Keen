import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import openai
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables (for local development)
load_dotenv()

# Page config (must be first Streamlit command)
st.set_page_config(
    page_title="KEEN - SME Insights Chat",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "KEEN SME Insights Chat"
    }
)

# Helper function to get secrets (works both locally and on Streamlit Cloud)
def get_secret(key):
    """Get secret from Streamlit secrets or environment variable"""
    # Try Streamlit secrets first (for cloud deployment)
    try:
        if key in st.secrets:
            return st.secrets[key]
    except:
        pass
    # Fall back to environment variable (for local development)
    return os.getenv(key)

# Initialize OpenAI client
client = OpenAI(api_key=get_secret('OPENAI_API_KEY'))

# Set theme to light
st.markdown("""
<script>
    const root = window.parent.document.querySelector('.stApp');
    if (root) {
        root.style.backgroundColor = '#ffffff';
    }
</script>
""", unsafe_allow_html=True)

# Custom CSS - Keen Brand Styling (White Theme)
st.markdown("""
<style>
    /* Force white background everywhere */
    .stApp {
        background-color: #ffffff !important;
    }
    
    /* Main app background */
    .main {
        background-color: #ffffff !important;
    }
    
    .block-container {
        background-color: #ffffff !important;
    }
    
    /* All text black */
    body, p, div, span, h1, h2, h3, h4, h5, h6, label {
        color: #000000 !important;
    }
    
    /* Logo container at center top */
    .logo-container {
        text-align: center;
        padding: 2rem 0 1rem 0;
        margin-bottom: 1rem;
        background: #ffffff !important;
    }
    
    .logo-container img {
        height: 120px;
        width: auto;
        max-width: 400px;
    }
    
    /* Header styling */
    .main-header {
        background: #ffffff !important;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        color: #000000 !important;
        text-align: center;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .main-header h1 {
        color: #000000 !important;
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: #000000 !important;
        font-size: 1rem;
    }
    
    /* Chat messages */
    .stChatMessage {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        background: #ffffff !important;
        border: 1px solid #e2e8f0;
    }
    
    .stChatMessage * {
        color: #000000 !important;
    }
    
    [data-testid="stChatMessageContent"] {
        padding: 0.5rem;
    }
    
    /* Source boxes with Keen styling */
    .source-box {
        background: #ffffff !important;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 3px solid #000000;
        border: 1px solid #e2e8f0;
    }
    
    .source-box * {
        color: #000000 !important;
    }
    
    .source-title {
        font-weight: 700;
        color: #000000 !important;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
    
    .similarity-badge {
        background: #000000 !important;
        color: #ffffff !important;
        padding: 0.35rem 0.8rem;
        border-radius: 0.3rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] * {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #000000 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #000000 !important;
        color: #ffffff !important;
        border: none;
        border-radius: 0.3rem;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        background: #333333 !important;
    }
    
    /* Sliders - Make them visible */
    .stSlider {
        padding: 1rem 0;
    }
    
    .stSlider > div > div > div {
        background-color: #000000 !important;
    }
    
    .stSlider > div > div > div > div {
        background-color: #000000 !important;
    }
    
    /* Slider track */
    [data-baseweb="slider"] {
        background-color: transparent !important;
    }
    
    [data-baseweb="slider"] > div {
        background-color: #e0e0e0 !important;
    }
    
    /* Slider thumb */
    [data-baseweb="slider"] [role="slider"] {
        background-color: #000000 !important;
        border: 2px solid #000000 !important;
        width: 20px !important;
        height: 20px !important;
    }
    
    /* Slider filled track */
    [data-baseweb="slider"] > div > div:first-child {
        background-color: #000000 !important;
    }
    
    /* Slider labels */
    .stSlider label {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    
    .stSlider [data-testid="stTickBarMin"],
    .stSlider [data-testid="stTickBarMax"] {
        color: #000000 !important;
    }
    
    /* Input field */
    .stChatInput {
        border-radius: 0.5rem;
        border: 1px solid #000000;
        background: #ffffff !important;
    }
    
    .stChatInput input {
        background: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #000000 !important;
        font-size: 2rem;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #000000 !important;
    }
    
    /* Dividers */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: #e2e8f0;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #ffffff !important;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #000000 !important;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #333333 !important;
    }
    
    /* Text areas and inputs */
    textarea, input {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Source URL Links */
    .source-link {
        display: inline-block;
        margin-top: 0.5rem;
        padding: 0.5rem 1rem;
        background: linear-gradient(135deg, #000000 0%, #333333 100%);
        color: #ffffff !important;
        text-decoration: none;
        border-radius: 0.3rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        border: none;
    }
    
    .source-link:hover {
        background: linear-gradient(135deg, #333333 0%, #555555 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .source-link:active {
        transform: translateY(0);
    }
</style>
""", unsafe_allow_html=True)

# Add logo at center top
import base64
from pathlib import Path

logo_path = Path("Keen-logo-color-RGB@2x.png")
if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <div class="logo-container">
        <img src="data:image/png;base64,{logo_data}" alt="Keen Logo">
    </div>
    """, unsafe_allow_html=True)
else:
    # Placeholder if logo not found
    st.markdown("""
    <div class="logo-container">
        <span style="color: #000000; font-weight: 700; font-size: 2rem;">KEEN</span>
    </div>
    """, unsafe_allow_html=True)

# Database connection
def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(
            get_secret('SUPABASE_DB_URL'),
            cursor_factory=RealDictCursor
        )
        conn.autocommit = True  # Important for read-only queries
        return conn
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

def get_embedding(text):
    """Generate embedding for text using OpenAI"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def search_documents(query, match_count=5, match_threshold=0.7):
    """Search for relevant document chunks"""
    conn = None
    cursor = None
    try:
        # Generate query embedding
        query_embedding = get_embedding(query)
        
        # Convert embedding list to PostgreSQL vector format
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        # Call the match_documents function with proper type casting
        cursor.execute(
            "SELECT * FROM match_documents(%s::vector, %s, %s)",
            (embedding_str, match_threshold, match_count)
        )
        
        results = cursor.fetchall()
        
        return results
    except Exception as e:
        st.error(f"Error searching documents: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def generate_answer(query, context_chunks):
    """Generate answer using OpenAI with context"""
    if not context_chunks:
        return "I could not find relevant information in the documents. / Ik kon geen relevante informatie vinden in de documenten.", []
    
    # Improved language detection
    query_lower = query.lower()
    
    # Dutch indicators
    dutch_words = ['wat', 'hoe', 'welke', 'waarom', 'waar', 'wanneer', 'wie', 'kunnen', 'moet', 'hebben', 
                   'zijn', 'wordt', 'voor', 'met', 'van', 'een', 'het', 'de', 'bij', 'naar', 'over']
    # Spanish indicators  
    spanish_words = ['qué', 'cómo', 'cuál', 'por qué', 'dónde', 'cuándo', 'quién', 'puede', 'debe', 
                     'tiene', 'son', 'está', 'para', 'con', 'del', 'los', 'las', 'una', 'sobre']
    # English indicators
    english_words = ['what', 'how', 'which', 'why', 'where', 'when', 'who', 'can', 'should', 'have', 
                     'is', 'are', 'for', 'with', 'from', 'about', 'the', 'and', 'to', 'of']
    
    dutch_count = sum(1 for word in dutch_words if word in query_lower)
    spanish_count = sum(1 for word in spanish_words if word in query_lower)
    english_count = sum(1 for word in english_words if word in query_lower)
    
    # Determine language based on highest count
    if dutch_count > spanish_count and dutch_count > english_count:
        language = "DUTCH"
        language_full = "Dutch/Nederlands"
    elif spanish_count > dutch_count and spanish_count > english_count:
        language = "SPANISH"
        language_full = "Spanish/Español"
    else:
        language = "ENGLISH"
        language_full = "English"
    
    # Prepare context with numbered sources
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        context_text += f"\n\n[Source {i}] {chunk['filename']}\n{chunk['content']}\n---"
    
    # Create prompt with VERY explicit language instruction
    prompt = f"""CRITICAL INSTRUCTION: You MUST answer in {language} ONLY. The user's question is in {language}.

The source documents below may be in Spanish, Dutch, or English, but you MUST translate/answer in {language} regardless of source language.

Sources (ignore their language, answer in {language}):
{context_text}

User Question (in {language}): {query}

ANSWER REQUIREMENTS (in {language} ONLY):
1. Write your ENTIRE answer in {language} - DO NOT use Spanish, Dutch, or any other language
2. Translate information from sources into {language}
3. Add [Source X] citations after each statement
4. Include relevant details, examples, and data
5. If sources are in a different language, TRANSLATE the content to {language}

Begin your answer in {language} now:"""

    # Generate answer
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an expert assistant. CRITICAL RULE: You MUST answer ONLY in {language_full}. Even if source documents are in other languages, translate everything to {language_full}. Always cite sources as [Source X]."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        
        answer = response.choices[0].message.content
        
        # Prepare sources with more detail
        sources = []
        for i, chunk in enumerate(context_chunks, 1):
            # Extract keywords from content for preview
            preview = chunk["content"][:400] + "..." if len(chunk["content"]) > 400 else chunk["content"]
            
            sources.append({
                "number": i,
                "filename": chunk["filename"],
                "content": chunk["content"],
                "preview": preview,
                "similarity": chunk["similarity"],
                "chunk_index": chunk["chunk_index"],
                "file_type": chunk.get("file_type", "unknown"),
                "source_url": chunk.get("source_url")
            })
        
        return answer, sources
        
    except Exception as e:
        st.error(f"Error generating answer: {str(e)}")
        return "Er is een fout opgetreden bij het genereren van het antwoord.", []

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Header with clean styling
st.markdown("""
<div class="main-header">
    <h1>SME Insights Chat</h1>
    <p>Search across 20,214+ document chunks about AI adoption, investors, and technology trends</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with settings
with st.sidebar:
    st.markdown("<h2 style='color: #000000;'>⚙️ Settings</h2>", unsafe_allow_html=True)
    
    match_count = st.slider(
        "Number of search results",
        min_value=3,
        max_value=10,
        value=10,
        help="How many relevant chunks to use for context"
    )
    
    match_threshold = st.slider(
        "Similarity threshold",
        min_value=0.5,
        max_value=0.9,
        value=0.5,
        step=0.05,
        help="Minimum similarity score (higher = stricter match)"
    )
    
    st.divider()
    
    # Stats
    st.markdown("<h2 style='color: #000000;'>📊 Database Stats</h2>", unsafe_allow_html=True)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT filename) as files, COUNT(*) as chunks FROM documents")
            stats = cursor.fetchone()
            
            st.metric("Total Files", f"{stats['files']:,}")
            st.metric("Total Chunks", f"{stats['chunks']:,}")
        else:
            st.error("No database connection")
    except Exception as e:
        st.error(f"Could not load stats: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available - DIRECTLY visible, not in expander
        if "sources" in message and message["sources"]:
            st.markdown("---")
            st.markdown(f"### 📚 Sources ({len(message['sources'])})")
            
            for source in message["sources"]:
                st.markdown(f"""
                <div class="source-box">
                    <div class="source-title">
                        [Source {source['number']}] {source['filename']} 
                        <span class="similarity-badge">{source['similarity']:.2%} relevance</span>
                    </div>
                    <div style="font-size: 0.9rem; color: #000000; margin-top: 0.3rem;">
                        📄 {source.get('file_type', 'unknown').upper()} • Chunk {source['chunk_index']}
                    </div>
                    <div style="margin-top: 0.8rem; padding: 0.8rem; background-color: white; border-radius: 0.3rem; font-size: 0.95rem; line-height: 1.6; color: #000000;">
                        <strong>Quote:</strong><br>
                        <em>"{source['preview']}"</em>
                    </div>
                    {f'<a href="{source["source_url"]}" target="_blank" class="source-link">🔗 View Original Source</a>' if source.get('source_url') else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Add a "show full content" expander for each source
                with st.expander(f"🔍 Show full text of Source {source['number']}"):
                    st.text_area(
                        "Full chunk content",
                        source['content'],
                        height=200,
                        key=f"source_{message.get('timestamp', 0)}_{source['number']}",
                        disabled=True
                    )

# Chat input
if prompt := st.chat_input("Ask a question about AI adoption, investors, or technology..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching documents..."):
            # Search for relevant chunks
            relevant_chunks = search_documents(prompt, match_count, match_threshold)
            
            if not relevant_chunks:
                response = "I could not find relevant information. Try rephrasing your question or lowering the similarity threshold."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                # Generate answer
                with st.spinner("Generating answer..."):
                    answer, sources = generate_answer(prompt, relevant_chunks)
                
                st.markdown(answer)
                
                # Show sources directly (not in expander)
                if sources:
                    st.markdown("---")
                    st.markdown(f"### 📚 Sources ({len(sources)})")
                    
                    for source in sources:
                        st.markdown(f"""
                        <div class="source-box">
                            <div class="source-title">
                                [Source {source['number']}] {source['filename']} 
                                <span class="similarity-badge">{source['similarity']:.2%} relevance</span>
                            </div>
                            <div style="font-size: 0.9rem; color: #000000; margin-top: 0.3rem;">
                                📄 {source.get('file_type', 'unknown').upper()} • Chunk {source['chunk_index']}
                            </div>
                            <div style="margin-top: 0.8rem; padding: 0.8rem; background-color: white; border-radius: 0.3rem; font-size: 0.95rem; line-height: 1.6; color: #000000;">
                                <strong>Quote:</strong><br>
                                <em>"{source['preview']}"</em>
                            </div>
                            {f'<a href="{source["source_url"]}" target="_blank" class="source-link">🔗 View Original Source</a>' if source.get('source_url') else ''}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add a "show full content" expander for each source
                        with st.expander(f"🔍 Show full text of Source {source['number']}"):
                            st.text_area(
                                "Full chunk content",
                                source['content'],
                                height=200,
                                key=f"new_source_{source['number']}",
                                disabled=True
                            )
                
                # Save to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "timestamp": datetime.now().timestamp()
                })

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #000000; font-size: 0.9rem; padding: 1rem; background: #ffffff;">
    <strong style="color: #000000;">💡 Tip:</strong> Each answer contains <span style="color: #000000; font-weight: 600;">[Source X]</span> references.<br>
    Ask specific questions for best results.
</div>
""", unsafe_allow_html=True)
