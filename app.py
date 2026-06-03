import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import tempfile
import os
import io
from datetime import datetime

load_dotenv()

st.set_page_config(
    page_title="BIMpilot — AI Assistant for BIM Engineers",
    page_icon="🏗️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0A1628;
        color: #FFFFFF;
    }
    [data-testid="stSidebar"] {
        background-color: #0D2137;
        border-right: 1px solid #1E3A5F;
    }
    [data-testid="stChatInput"] {
        background-color: #0D2137;
        border: 1px solid #00D4FF;
        border-radius: 12px;
    }
    [data-testid="stChatMessage"] {
        background-color: #0D2137;
        border-radius: 12px;
        border: 1px solid #1E3A5F;
        margin-bottom: 8px;
        padding: 8px;
    }
    .stButton > button {
        background-color: #00D4FF;
        color: #0A1628;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #00F5CC;
        color: #0A1628;
    }
    .streamlit-expanderHeader {
        background-color: #1E3A5F;
        border-radius: 8px;
        color: #00D4FF;
    }
    [data-testid="stFileUploader"] {
        background-color: #1E3A5F;
        border-radius: 8px;
        border: 1px dashed #00D4FF;
    }
    .bimpilot-header {
        background: linear-gradient(135deg, #0D2137 0%, #1E3A5F 100%);
        padding: 20px 30px;
        border-radius: 16px;
        border: 1px solid #00D4FF;
        margin-bottom: 20px;
    }
    .bimpilot-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #00D4FF;
        margin: 0;
        letter-spacing: 2px;
    }
    .bimpilot-subtitle {
        font-size: 1rem;
        color: #A0B4C8;
        margin: 4px 0 0 0;
    }
    .bimpilot-badge {
        background-color: #00D4FF;
        color: #0A1628;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 10px;
    }
    .stats-bar {
        background-color: #0D2137;
        border: 1px solid #1E3A5F;
        border-radius: 10px;
        padding: 10px 20px;
        margin-bottom: 16px;
    }
    .stat-item {
        color: #00D4FF;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .bimpilot-footer {
        text-align: center;
        color: #4A6A8A;
        font-size: 0.75rem;
        margin-top: 20px;
        padding-top: 10px;
        border-top: 1px solid #1E3A5F;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_base_vectorstore():
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    vectorstore = Chroma(
        persist_directory="chroma_db",
        embedding_function=embeddings
    )
    return vectorstore, embeddings

def process_uploaded_pdf(uploaded_file, embeddings):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    loader = PyPDFLoader(tmp_path)
    docs = loader.load()

    for doc in docs:
        doc.metadata["source_file"] = uploaded_file.name

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(docs)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    os.unlink(tmp_path)
    return vectorstore, len(docs)

def format_sources(docs):
    sources = []
    seen = set()
    for doc in docs:
        source_file = doc.metadata.get("source_file", "Unknown Document")
        page = doc.metadata.get("page", 0)
        page_display = int(page) + 1
        key = f"{source_file}_p{page_display}"
        if key not in seen:
            seen.add(key)
            sources.append(f"• {source_file} — Page {page_display}")
    return sources

def build_conversation_history(messages):
    history = ""
    for message in messages[-6:]:
        if message["role"] == "user":
            history += f"User: {message['content']}\n"
        elif message["role"] == "assistant":
            history += f"Assistant: {message['content']}\n"
    return history

def ask_question(question, vectorstore, messages):
    docs = vectorstore.similarity_search(question, k=10)
    context = "\n\n".join([doc.page_content for doc in docs])
    sources = format_sources(docs)
    conversation_history = build_conversation_history(messages)

    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile"
    )

    prompt = f"""You are BIMpilot, an expert AI assistant for BIM engineers
with deep knowledge of Building Information Modeling, Revit, Navisworks,
ISO 19650, LOD Specification, and BIM Execution Plans.

Use the conversation history and document context to give accurate,
helpful, and contextually aware answers. For follow up questions refer
back to the conversation history.

Use the document context as your primary source. Only say you cannot
find the answer if the context has absolutely no relevant information.

Conversation History:
{conversation_history}

Context from BIM documents:
{context}

Current Question: {question}

Give a detailed, practical, and helpful answer.
Answer:"""

    response = llm.invoke(prompt)
    return response.content, sources

def generate_pdf_report(messages):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    DARK_BLUE = HexColor("#0A1628")
    MID_BLUE = HexColor("#0D2137")
    ACCENT_BLUE = HexColor("#00D4FF")
    WHITE = HexColor("#FFFFFF")
    LIGHT_GRAY = HexColor("#A0B4C8")
    DARK_GRAY = HexColor("#4A6A8A")

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=24,
        fontName="Helvetica-Bold",
        textColor=ACCENT_BLUE,
        spaceAfter=6,
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica",
        textColor=LIGHT_GRAY,
        spaceAfter=4,
        alignment=TA_LEFT
    )

    date_style = ParagraphStyle(
        "Date",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica",
        textColor=DARK_GRAY,
        spaceAfter=20,
        alignment=TA_LEFT
    )

    question_style = ParagraphStyle(
        "Question",
        parent=styles["Normal"],
        fontSize=12,
        fontName="Helvetica-Bold",
        textColor=ACCENT_BLUE,
        spaceAfter=6,
        spaceBefore=16,
        leftIndent=0
    )

    answer_style = ParagraphStyle(
        "Answer",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica",
        textColor=HexColor("#2C2C2C"),
        spaceAfter=8,
        leading=16
    )

    source_style = ParagraphStyle(
        "Source",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Oblique",
        textColor=DARK_GRAY,
        spaceAfter=4,
        leftIndent=20
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=DARK_GRAY,
        spaceAfter=4
    )

    story = []

    story.append(Paragraph("🏗️ BIMpilot", title_style))
    story.append(Paragraph(
        "AI-Powered BIM Research Report",
        subtitle_style
    ))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        date_style
    ))
    story.append(HRFlowable(
        width="100%",
        thickness=2,
        color=ACCENT_BLUE,
        spaceAfter=20
    ))

    qa_count = 0
    for message in messages:
        if message["role"] == "user":
            qa_count += 1
            story.append(Paragraph(
                f"Q{qa_count}: {message['content']}",
                question_style
            ))
        elif message["role"] == "assistant":
            clean_answer = message["content"].replace("\n", "<br/>")
            story.append(Paragraph(clean_answer, answer_style))

            if message.get("sources"):
                story.append(Paragraph("Sources:", section_style))
                for source in message["sources"]:
                    story.append(Paragraph(source, source_style))

            story.append(HRFlowable(
                width="100%",
                thickness=0.5,
                color=HexColor("#CCCCCC"),
                spaceAfter=10
            ))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(
        width="100%",
        thickness=1,
        color=ACCENT_BLUE,
        spaceAfter=8
    ))
    story.append(Paragraph(
        "Generated by BIMpilot v2.0 | Built by Devendra Gupta | BIM + AI + Automation",
        ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            fontName="Helvetica",
            textColor=DARK_GRAY,
            alignment=TA_CENTER
        )
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_vectorstore" not in st.session_state:
    st.session_state.active_vectorstore = None

if "uploaded_doc_name" not in st.session_state:
    st.session_state.uploaded_doc_name = None

base_vectorstore, embeddings = load_base_vectorstore()

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 20px 0;'>
        <span style='font-size:2rem; font-weight:900; color:#00D4FF;
        letter-spacing:3px;'>BIM</span>
        <span style='font-size:2rem; font-weight:900; color:#FFFFFF;
        letter-spacing:3px;'>pilot</span>
        <br>
        <span style='font-size:0.7rem; color:#4A6A8A;
        letter-spacing:2px;'>AI ASSISTANT FOR BIM ENGINEERS</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**📚 Knowledge Base**")
    st.markdown("""
    <div style='background:#1E3A5F; border-radius:8px;
    padding:10px; margin-bottom:10px;'>
        <div style='color:#00D4FF; font-size:0.8rem;'>✅ ISO 19650 Edition 4</div>
        <div style='color:#00D4FF; font-size:0.8rem;'>✅ LOD Specification 2025</div>
        <div style='color:#00D4FF; font-size:0.8rem;'>✅ Revit Architecture Guide</div>
        <div style='color:#00D4FF; font-size:0.8rem;'>✅ Navisworks Guide</div>
        <div style='color:#00D4FF; font-size:0.8rem;'>✅ BIM Execution Plan</div>
        <div style='color:#A0B4C8; font-size:0.75rem; margin-top:6px;'>
        2,333 pages · 9,935 chunks</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**📄 Upload Your Document**")
    uploaded_file = st.file_uploader(
        "Upload private BIM PDF",
        type="pdf",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.uploaded_doc_name:
            with st.spinner("Processing document..."):
                custom_vectorstore, num_pages = process_uploaded_pdf(
                    uploaded_file, embeddings
                )
                st.session_state.active_vectorstore = custom_vectorstore
                st.session_state.uploaded_doc_name = uploaded_file.name
                st.session_state.messages = []
            st.success(f"✅ Loaded {num_pages} pages")

    if st.session_state.uploaded_doc_name:
        st.info(f"📄 Active: {st.session_state.uploaded_doc_name}")
        if st.button("↩ Use Base Knowledge"):
            st.session_state.active_vectorstore = None
            st.session_state.uploaded_doc_name = None
            st.session_state.messages = []
            st.rerun()

    st.markdown("---")

    if st.session_state.messages:
        st.markdown("**📊 Export Report**")
        if st.button("📥 Download PDF Report"):
            with st.spinner("Generating report..."):
                pdf_buffer = generate_pdf_report(st.session_state.messages)
                st.download_button(
                    label="⬇️ Click to Download",
                    data=pdf_buffer,
                    file_name=f"BIMpilot_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )

    st.markdown("---")
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("""
    <div style='margin-top:20px; text-align:center;
    color:#4A6A8A; font-size:0.7rem;'>
        Built by Devendra Gupta<br>
        BIM + AI + Automation
    </div>
    """, unsafe_allow_html=True)

current_vectorstore = st.session_state.active_vectorstore or base_vectorstore

st.markdown("""
<div class='bimpilot-header'>
    <div style='display:flex; align-items:center;'>
        <span class='bimpilot-title'>🏗️ BIMpilot</span>
        <span class='bimpilot-badge'>v2.0</span>
    </div>
    <div class='bimpilot-subtitle'>
        AI-Powered Document Intelligence for BIM Engineers
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='stats-bar'>
    <span class='stat-item'>📚 5 BIM Documents &nbsp;|&nbsp;
    🧠 9,935 Knowledge Chunks &nbsp;|&nbsp;
    ⚡ Powered by Groq + Llama 3.3 &nbsp;|&nbsp;
    🔒 Private & Secure</span>
</div>
""", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📚 Sources"):
                for source in message["sources"]:
                    st.markdown(source)

if not st.session_state.messages:
    st.markdown("""
    <div style='text-align:center; padding:40px 20px; color:#4A6A8A;'>
        <div style='font-size:3rem;'>🏗️</div>
        <div style='font-size:1.1rem; color:#A0B4C8; margin-top:10px;'>
            Ask me anything about BIM, Revit, Navisworks,
            ISO 19650, or LOD
        </div>
        <div style='font-size:0.85rem; margin-top:20px; color:#4A6A8A;'>
            Try: "What is information management in ISO 19650?"<br>
            Or: "How do I set up a BIM Execution Plan?"<br>
            Or: "What is the difference between LOD 200 and LOD 300?"
        </div>
    </div>
    """, unsafe_allow_html=True)

if prompt := st.chat_input("Ask BIMpilot a BIM question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("BIMpilot is searching documents..."):
            answer, sources = ask_question(
                prompt,
                current_vectorstore,
                st.session_state.messages
            )
        st.markdown(answer)
        if sources:
            with st.expander("📚 Sources"):
                for source in sources:
                    st.markdown(source)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })

st.markdown("""
<div class='bimpilot-footer'>
    BIMpilot v2.0 · Built by Devendra Gupta ·
    BIM + AI + Automation ·
    Powered by LangChain · ChromaDB · Groq AI
</div>
""", unsafe_allow_html=True)