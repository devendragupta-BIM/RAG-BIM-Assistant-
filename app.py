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
from reportlab.lib.enums import TA_CENTER
from generator import show_generator
from standards import show_standards_library
from dashboard import show_dashboard
from voice import show_voice, render_voice_input
from coordinator import show_coordinator
from issue_tracker import show_issue_tracker
from cost_intelligence import show_cost_intelligence
from rfi_intelligence import show_rfi_intelligence
from submittal_tracker import show_submittal_tracker
from spec_writer import show_specification_writer
from meeting_minutes import show_meeting_minutes
from carbon_estimator import show_carbon_estimator
from contract_analyzer import show_contract_analyzer
import tempfile
import os
import io
from datetime import datetime

load_dotenv()

st.set_page_config(
    page_title="NexBIM",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Design System ─────────────────────────────────────────────────────────────
# Palette: deep navy base, slate mid-tones, electric cyan accent, warm amber highlight
# Type: DM Sans (body) + Space Mono (data/code) — feels technical but human
# Signature: blueprint grid texture on sidebar, not decorative — it IS the product

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Space+Mono:wght@400;700&family=DM+Serif+Display:ital@0;1&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Base ── */
.stApp {
    background: #0B1120;
    color: #C8D8E8;
    font-family: 'DM Sans', sans-serif;
}

/* ── Sidebar — blueprint feel ── */
[data-testid="stSidebar"] {
    background: #080E1A !important;
    border-right: 1px solid #1A2840;
    background-image:
        linear-gradient(rgba(14,160,231,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(14,160,231,0.03) 1px, transparent 1px) !important;
    background-size: 24px 24px !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}

/* ── Inputs ── */
[data-testid="stChatInput"] textarea {
    background: #111827 !important;
    border: 1px solid #1E3050 !important;
    border-radius: 10px !important;
    color: #C8D8E8 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #0EA0E7 !important;
    box-shadow: 0 0 0 3px rgba(14,160,231,0.1) !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: #0F1929 !important;
    border: 1px solid #1A2840 !important;
    border-radius: 12px !important;
    margin-bottom: 10px !important;
    padding: 4px !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #0EA0E7 !important;
    color: #080E1A !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    width: 100% !important;
    padding: 10px 16px !important;
    transition: background 0.2s, transform 0.15s !important;
    letter-spacing: 0.1px !important;
}
.stButton > button:hover {
    background: #38B8F5 !important;
    transform: translateY(-1px) !important;
}

.stDownloadButton > button {
    background: #0EA0E7 !important;
    color: #080E1A !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #0F1929 !important;
    border: 1px solid #1A2840 !important;
    border-radius: 8px !important;
    color: #7AA0C0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #0F1929 !important;
    border: 1px dashed #1E3050 !important;
    border-radius: 10px !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #0F1929 !important;
    border: 1px solid #1E3050 !important;
    color: #C8D8E8 !important;
    font-family: 'DM Sans', sans-serif !important;
    border-radius: 8px !important;
}

/* ── Text input ── */
.stTextInput input {
    background: #0F1929 !important;
    border: 1px solid #1E3050 !important;
    border-radius: 8px !important;
    color: #C8D8E8 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Radio ── */
.stRadio > div { gap: 4px !important; }
.stRadio label { color: #7AA0C0 !important; font-size: 0.85rem !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0B1120 !important;
    border-bottom: 1px solid #1A2840 !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #4A6A8A !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: #0F1929 !important;
    color: #0EA0E7 !important;
    border-bottom: 2px solid #0EA0E7 !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1A2840 !important;
    border-radius: 8px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #080E1A; }
::-webkit-scrollbar-thumb { background: #1E3050; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2A4068; }

/* ── NexBIM custom components ── */

.nx-wordmark {
    padding: 28px 20px 8px 20px;
    display: flex;
    align-items: baseline;
    gap: 2px;
}
.nx-wordmark-nex {
    font-family: 'DM Serif Display', serif;
    font-size: 1.7rem;
    color: #0EA0E7;
    letter-spacing: -1px;
    line-height: 1;
}
.nx-wordmark-bim {
    font-family: 'DM Serif Display', serif;
    font-size: 1.7rem;
    color: #E8F4FF;
    letter-spacing: -1px;
    line-height: 1;
}
.nx-version {
    font-family: 'Space Mono', monospace;
    font-size: 0.55rem;
    color: #1E3050;
    letter-spacing: 2px;
    padding: 0 20px 16px 20px;
    text-transform: uppercase;
}

.nx-nav-section {
    font-family: 'Space Mono', monospace;
    font-size: 0.58rem;
    color: #1E3050;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    padding: 14px 20px 6px 20px;
}

.nx-kb-block {
    margin: 0 12px;
    background: #0D1625;
    border: 1px solid #1A2840;
    border-radius: 8px;
    padding: 12px 14px;
}
.nx-kb-row {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    color: #3A6080;
    padding: 3px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.nx-kb-row::before {
    content: '—';
    color: #1A3050;
    font-size: 0.7rem;
}
.nx-kb-stats {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #1A2840;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid #121E30;
}

.nx-disc-indicator {
    margin: 6px 12px;
    padding: 8px 12px;
    border-radius: 6px;
    border-left: 3px solid;
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

.nx-page-header {
    padding: 24px 0 20px 0;
    border-bottom: 1px solid #1A2840;
    margin-bottom: 24px;
}
.nx-page-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #E8F4FF;
    letter-spacing: -0.5px;
    line-height: 1.1;
}
.nx-page-title em {
    font-style: italic;
    color: #0EA0E7;
}
.nx-page-desc {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    color: #3A5570;
    margin-top: 6px;
    line-height: 1.5;
}

.nx-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 20px;
}
.nx-pill {
    background: #0D1625;
    border: 1px solid #1A2840;
    border-radius: 20px;
    padding: 4px 12px;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #3A6080;
    white-space: nowrap;
}
.nx-pill span {
    color: #0EA0E7;
    font-weight: 700;
}

.nx-empty {
    text-align: center;
    padding: 80px 20px;
}
.nx-empty-glyph {
    font-family: 'DM Serif Display', serif;
    font-size: 3.5rem;
    color: #0EA0E7;
    opacity: 0.08;
    margin-bottom: 16px;
    line-height: 1;
}
.nx-empty-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: #1A3050;
    margin-bottom: 10px;
}
.nx-empty-hints {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.83rem;
    color: #162030;
    line-height: 2.4;
}
.nx-empty-hints em {
    color: #1E3858;
    font-style: normal;
}

.nx-source {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #2A4060;
    padding: 3px 0;
    display: flex;
    align-items: center;
    gap: 6px;
}
.nx-source::before {
    content: '↗';
    color: #0EA0E7;
    font-size: 0.6rem;
}

.nx-warn {
    background: #1A0F0F;
    border: 1px solid #3A1818;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.84rem;
    color: #C06060;
}

.nx-footer {
    text-align: center;
    font-family: 'Space Mono', monospace;
    font-size: 0.55rem;
    letter-spacing: 1.5px;
    color: #0D1828;
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #0F1D2E;
    text-transform: uppercase;
}

.nx-doc-active {
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: #0EA0E7;
    padding: 4px 12px;
    margin: 4px 0;
    display: flex;
    align-items: center;
    gap: 6px;
}
.nx-doc-active::before {
    content: '●';
    font-size: 0.5rem;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}
</style>
""", unsafe_allow_html=True)

# ── Config ────────────────────────────────────────────────────────────────────

DISCIPLINE_CONFIG = {
    "Architecture": {
        "emoji": "🏛️",
        "color": "#E07060",
        "focus": "architectural design, floor plans, walls, curtain walls, rooms, doors, windows, stairs, roofs, and architectural Revit workflows",
        "examples": [
            "How do I model a curtain wall in Revit?",
            "What LOD applies to architectural walls at design development?",
            "How do I tag rooms and calculate areas automatically?"
        ]
    },
    "Structure": {
        "emoji": "🏗️",
        "color": "#E0B030",
        "focus": "structural engineering, columns, beams, slabs, foundations, rebar detailing, structural grids, load paths, and structural Revit workflows",
        "examples": [
            "How do I model a structural column grid in Revit?",
            "What is the correct approach for rebar detailing in BIM?",
            "How do I set up a structural analytical model?"
        ]
    },
    "MEP": {
        "emoji": "⚡",
        "color": "#30C090",
        "focus": "mechanical systems, electrical systems, plumbing, duct routing, pipe routing, MEP coordination, clash detection, and MEP Revit workflows",
        "examples": [
            "How do I route ducts in Revit MEP?",
            "What are MEP clearance zone requirements per code?",
            "How does clash detection work between MEP and structure?"
        ]
    },
    "General BIM": {
        "emoji": "📚",
        "color": "#0EA0E7",
        "focus": "BIM standards, ISO 19650, LOD specification, BIM Execution Plans, information management, and general BIM workflows",
        "examples": [
            "What does ISO 19650 say about information management?",
            "What is the difference between LOD 200 and LOD 300?",
            "How do I write a BIM Execution Plan?"
        ]
    }
}

PAGES = [
    "AI Chat",
    "BIM Generator",
    "Standards Library",
    "Dashboard",
    "Voice",
    "Coordination",
    "Issue Tracker",
    "Cost Intelligence",
    "RFI Intelligence",
    "Submittal Tracker",
    "Spec Writer",
    "Meeting Minutes",
    "Carbon Estimator",
    "Contract Analyzer"
]

PAGE_ICONS = {
    "AI Chat":          "💬",
    "BIM Generator":    "⚡",
    "Standards Library":"📖",
    "Dashboard":        "📊",
    "Voice":            "🎙️",
    "Coordination":     "🔗",
    "Issue Tracker":    "🐛",
    "Cost Intelligence":"💰",
    "RFI Intelligence": "📨",
    "Submittal Tracker":"📦",
    "Spec Writer":      "📝",
    "Meeting Minutes":  "🎙️",
    "Carbon Estimator": "🌿",
    "Contract Analyzer":"📄"
}

# Pages that don't need the discipline selector
NO_DISC_PAGES = ["Coordination", "Issue Tracker", "Cost Intelligence",
                 "BIM Generator", "Standards Library", "Dashboard", "Voice",
                 "RFI Intelligence", "Submittal Tracker", "Spec Writer",
                 "Meeting Minutes", "Carbon Estimator", "Contract Analyzer"]

# ── Cached resources ──────────────────────────────────────────────────────────

@st.cache_resource
def load_base_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    if not os.path.exists("chroma_db"):
        return None, embeddings
    vectorstore = Chroma(
        persist_directory="chroma_db",
        embedding_function=embeddings
    )
    return vectorstore, embeddings

# ── PDF helpers ───────────────────────────────────────────────────────────────

def process_uploaded_pdf(uploaded_file, embeddings):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    loader = PyPDFLoader(tmp_path)
    docs   = loader.load()
    for doc in docs:
        doc.metadata["source_file"] = uploaded_file.name
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50
    ).split_documents(docs)
    vs = Chroma.from_documents(documents=chunks, embedding=embeddings)
    os.unlink(tmp_path)
    return vs, len(docs)

def format_sources(docs):
    sources, seen = [], set()
    for doc in docs:
        src  = doc.metadata.get("source_file", "Unknown")
        page = int(doc.metadata.get("page", 0)) + 1
        key  = f"{src}_p{page}"
        if key not in seen:
            seen.add(key)
            sources.append(f"{src} — pg.{page}")
    return sources

def build_history(messages):
    history = ""
    for m in messages[-6:]:
        if m["role"] == "user":
            history += f"User: {m['content']}\n"
        elif m["role"] == "assistant":
            history += f"Assistant: {m['content']}\n"
    return history

# ── AI Chat ───────────────────────────────────────────────────────────────────

def ask_question(question, vectorstore, messages, discipline):
    docs    = vectorstore.similarity_search(question, k=8)
    context = "\n\n".join([d.page_content for d in docs])
    sources = format_sources(docs)
    history = build_history(messages)
    focus   = DISCIPLINE_CONFIG[discipline]["focus"]

    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile"
    )

    prompt = f"""You are NexBIM, a sharp and knowledgeable BIM assistant
specialising in {focus}.

RESPONSE RULES — follow every time, no exceptions:
- Maximum 3 key points. Never more.
- Start directly with the answer. No preamble, no "Great question".
- Use bullet points. Bold key terms.
- If the answer is simple, give 2-3 sentences only.
- End with one "Quick Tip:" line if it adds real value.
- Never repeat the question. Never say what you are about to do.

Discipline context: {discipline}

Conversation so far:
{history}

Relevant document context:
{context}

Question: {question}

Answer (max 3 points, no fluff):"""

    response = llm.invoke(prompt)
    return response.content, sources

# ── PDF export ────────────────────────────────────────────────────────────────

def generate_pdf_report(messages, discipline):
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=letter,
                rightMargin=0.75*inch, leftMargin=0.75*inch,
                topMargin=0.75*inch,  bottomMargin=0.75*inch)
    CYAN      = HexColor("#0EA0E7")
    SLATE     = HexColor("#7AA0C0")
    DARK      = HexColor("#3A5570")
    styles    = getSampleStyleSheet()

    title_s    = ParagraphStyle("T",  parent=styles["Normal"], fontSize=22,
                    fontName="Helvetica-Bold", textColor=CYAN, spaceAfter=4)
    sub_s      = ParagraphStyle("S",  parent=styles["Normal"], fontSize=10,
                    fontName="Helvetica", textColor=SLATE, spaceAfter=4)
    date_s     = ParagraphStyle("D",  parent=styles["Normal"], fontSize=8,
                    fontName="Helvetica", textColor=DARK,  spaceAfter=18)
    q_s        = ParagraphStyle("Q",  parent=styles["Normal"], fontSize=11,
                    fontName="Helvetica-Bold", textColor=CYAN,
                    spaceAfter=4, spaceBefore=14)
    a_s        = ParagraphStyle("A",  parent=styles["Normal"], fontSize=10,
                    fontName="Helvetica", textColor=HexColor("#2C2C2C"),
                    spaceAfter=6, leading=15)
    src_s      = ParagraphStyle("SR", parent=styles["Normal"], fontSize=8,
                    fontName="Helvetica-Oblique", textColor=DARK,
                    spaceAfter=3, leftIndent=16)
    sec_s      = ParagraphStyle("SC", parent=styles["Normal"], fontSize=9,
                    fontName="Helvetica-Bold", textColor=DARK, spaceAfter=3)
    footer_s   = ParagraphStyle("F",  parent=styles["Normal"], fontSize=7,
                    fontName="Helvetica", textColor=DARK, alignment=TA_CENTER)

    story = []
    story.append(Paragraph("NexBIM", title_s))
    story.append(Paragraph(f"Research Report — {discipline}", sub_s))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", date_s))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=CYAN, spaceAfter=16))

    qa = 0
    for m in messages:
        if m["role"] == "user":
            qa += 1
            story.append(Paragraph(f"Q{qa}: {m['content']}", q_s))
        elif m["role"] == "assistant":
            story.append(Paragraph(
                m["content"].replace("\n", "<br/>"), a_s))
            if m.get("sources"):
                story.append(Paragraph("Sources:", sec_s))
                for s in m["sources"]:
                    story.append(Paragraph(s, src_s))
            story.append(HRFlowable(width="100%", thickness=0.4,
                                     color=HexColor("#DDDDDD"), spaceAfter=8))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=CYAN, spaceAfter=6))
    story.append(Paragraph(
        "NexBIM v3.3 — Built by Devendra Gupta — BIM + AI + Automation",
        footer_s))
    doc.build(story)
    buffer.seek(0)
    return buffer

# ── Session state ─────────────────────────────────────────────────────────────

defaults = {
    "messages":           [],
    "active_vectorstore": None,
    "uploaded_doc_name":  None,
    "discipline":         "General BIM",
    "page":               "AI Chat",
    "issues":             [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

base_vectorstore, embeddings = load_base_vectorstore()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:

    # Wordmark
    st.markdown("""
    <div class='nx-wordmark'>
        <span class='nx-wordmark-nex'>Nex</span>
        <span class='nx-wordmark-bim'>BIM</span>
    </div>
    <div class='nx-version'>v4.0 &nbsp;·&nbsp; AI Platform for BIM Engineers</div>
    """, unsafe_allow_html=True)

    # Navigation
    st.markdown("<div class='nx-nav-section'>Navigate</div>",
                unsafe_allow_html=True)

    for p in PAGES:
        icon    = PAGE_ICONS[p]
        is_active = st.session_state.page == p
        label   = f"{icon} {p}"

        if is_active:
            st.markdown(f"""
            <div style='margin:0 12px 2px 12px; padding:8px 12px;
            background:#0D1E34; border:1px solid #1A3050;
            border-left:3px solid #0EA0E7; border-radius:6px;
            font-family:DM Sans,sans-serif; font-size:0.85rem;
            color:#0EA0E7; font-weight:600;'>{label}</div>
            """, unsafe_allow_html=True)
        else:
            if st.button(label, key=f"nav_{p}",
                         help=f"Go to {p}"):
                st.session_state.page = p
                st.rerun()

    # Discipline selector — only for relevant pages
    if st.session_state.page not in NO_DISC_PAGES:
        st.markdown("<div class='nx-nav-section'>Discipline</div>",
                    unsafe_allow_html=True)

        disc_options = list(DISCIPLINE_CONFIG.keys())
        selected_disc = st.selectbox(
            "Discipline", disc_options,
            index=disc_options.index(st.session_state.discipline),
            label_visibility="collapsed"
        )
        if selected_disc != st.session_state.discipline:
            st.session_state.discipline = selected_disc
            st.session_state.messages   = []
            st.rerun()

        disc_color = DISCIPLINE_CONFIG[selected_disc]["color"]
        disc_emoji = DISCIPLINE_CONFIG[selected_disc]["emoji"]
        st.markdown(f"""
        <div class='nx-disc-indicator'
        style='border-color:{disc_color};
        background:{disc_color}10; color:{disc_color};'>
            {disc_emoji} {selected_disc} mode active
        </div>
        """, unsafe_allow_html=True)

    # Knowledge base
    st.markdown("<div class='nx-nav-section'>Knowledge Base</div>",
                unsafe_allow_html=True)
    st.markdown("""
    <div class='nx-kb-block'>
        <div class='nx-kb-row'>ISO 19650 Edition 4</div>
        <div class='nx-kb-row'>LOD Specification 2025</div>
        <div class='nx-kb-row'>Revit Architecture Guide</div>
        <div class='nx-kb-row'>Navisworks User Guide</div>
        <div class='nx-kb-row'>BIM Execution Plan Template</div>
        <div class='nx-kb-stats'>2,333 pages · 9,935 chunks · ChromaDB</div>
    </div>
    """, unsafe_allow_html=True)

    # Upload document
    st.markdown("<div class='nx-nav-section'>Upload Document</div>",
                unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "PDF", type="pdf", label_visibility="collapsed"
    )

    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.uploaded_doc_name:
            with st.spinner("Processing document..."):
                custom_vs, num_pages = process_uploaded_pdf(
                    uploaded_file, embeddings)
                st.session_state.active_vectorstore = custom_vs
                st.session_state.uploaded_doc_name  = uploaded_file.name
                st.session_state.messages            = []
            st.success(f"✓ {num_pages} pages loaded")

    if st.session_state.uploaded_doc_name:
        name = st.session_state.uploaded_doc_name
        st.markdown(f"""
        <div class='nx-doc-active'>
            {name[:24]}{'...' if len(name) > 24 else ''}
        </div>
        """, unsafe_allow_html=True)
        if st.button("↩ Reset to base KB"):
            st.session_state.active_vectorstore = None
            st.session_state.uploaded_doc_name  = None
            st.session_state.messages            = []
            st.rerun()

    # Export — only on AI Chat
    if st.session_state.messages and st.session_state.page == "AI Chat":
        st.markdown("<div class='nx-nav-section'>Export</div>",
                    unsafe_allow_html=True)
        if st.button("📥 Export chat as PDF"):
            with st.spinner("Building report..."):
                pdf = generate_pdf_report(
                    st.session_state.messages,
                    st.session_state.discipline
                )
                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf,
                    file_name=f"NexBIM_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )

    # Session
    st.markdown("<div class='nx-nav-section'>Session</div>",
                unsafe_allow_html=True)
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

    # Footer
    st.markdown("""
    <div class='nx-footer'>
        Devendra Gupta &nbsp;·&nbsp; BIM + AI + Automation
    </div>
    """, unsafe_allow_html=True)

# ── Page routing ──────────────────────────────────────────────────────────────

if st.session_state.page == "BIM Generator":
    show_generator()
    st.stop()

if st.session_state.page == "Standards Library":
    show_standards_library()
    st.stop()

if st.session_state.page == "Dashboard":
    show_dashboard()
    st.stop()

if st.session_state.page == "Voice":
    show_voice()
    st.stop()

if st.session_state.page == "Coordination":
    show_coordinator()
    st.stop()

if st.session_state.page == "Issue Tracker":
    show_issue_tracker()
    st.stop()

if st.session_state.page == "Cost Intelligence":
    show_cost_intelligence()
    st.stop()

if st.session_state.page == "RFI Intelligence":
    show_rfi_intelligence()
    st.stop()

if st.session_state.page == "Submittal Tracker":
    show_submittal_tracker()
    st.stop()

if st.session_state.page == "Spec Writer":
    show_specification_writer()
    st.stop()

if st.session_state.page == "Meeting Minutes":
    show_meeting_minutes()
    st.stop()

if st.session_state.page == "Carbon Estimator":
    show_carbon_estimator()
    st.stop()

if st.session_state.page == "Contract Analyzer":
    show_contract_analyzer()
    st.stop()

# ── AI Chat page ──────────────────────────────────────────────────────────────

current_vs   = st.session_state.active_vectorstore or base_vectorstore
current_disc = st.session_state.discipline
disc_color   = DISCIPLINE_CONFIG[current_disc]["color"]
disc_emoji   = DISCIPLINE_CONFIG[current_disc]["emoji"]

# Page header
st.markdown(f"""
<div class='nx-page-header'>
    <div class='nx-page-title'>
        {disc_emoji} <em>{current_disc}</em> Chat
    </div>
    <div class='nx-page-desc'>
        Ask anything about {current_disc.lower()} —
        grounded in ISO 19650, Revit, Navisworks, and LOD documents.
        Answers in 3 points. No fluff.
    </div>
</div>
""", unsafe_allow_html=True)

# Stats pills
st.markdown("""
<div class='nx-pill-row'>
    <div class='nx-pill'><span>5</span> documents</div>
    <div class='nx-pill'><span>9,935</span> chunks</div>
    <div class='nx-pill'><span>50+</span> standards</div>
    <div class='nx-pill'>Groq <span>Llama 3.3</span></div>
    <div class='nx-pill'>Source <span>citations</span></div>
    <div class='nx-pill'>Chat <span>memory</span></div>
</div>
""", unsafe_allow_html=True)

# KB warning
if base_vectorstore is None and current_vs is None:
    st.markdown("""
    <div class='nx-warn'>
    ⚠️ Knowledge base not loaded. Upload a BIM PDF in the sidebar to begin.
    </div>
    """, unsafe_allow_html=True)

# Chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for src in message["sources"]:
                    st.markdown(
                        f"<div class='nx-source'>{src}</div>",
                        unsafe_allow_html=True)

# Voice input — single call, unique key
render_voice_input(
    current_disc,
    current_vs
)

# Empty state
if not st.session_state.messages:
    examples = DISCIPLINE_CONFIG[current_disc]["examples"]
    st.markdown(f"""
    <div class='nx-empty'>
        <div class='nx-empty-glyph'>◈</div>
        <div class='nx-empty-title'>{current_disc} — ready</div>
        <div class='nx-empty-hints'>
            <em>"{examples[0]}"</em><br>
            <em>"{examples[1]}"</em><br>
            <em>"{examples[2]}"</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input(
        f"Ask about {current_disc.lower()}..."):
    if current_vs is None:
        st.error("Upload a PDF document in the sidebar first.")
    else:
        st.session_state.messages.append(
            {"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(""):
                answer, sources = ask_question(
                    prompt, current_vs,
                    st.session_state.messages,
                    current_disc
                )
            st.markdown(answer)
            if sources:
                with st.expander("Sources"):
                    for src in sources:
                        st.markdown(
                            f"<div class='nx-source'>{src}</div>",
                            unsafe_allow_html=True)

        st.session_state.messages.append({
            "role":    "assistant",
            "content": answer,
            "sources": sources
        })

# Footer
st.markdown("""
<div class='nx-footer'>
    NexBIM v4.0 &nbsp;·&nbsp; Devendra Gupta &nbsp;·&nbsp;
    LangChain · ChromaDB · Groq · Streamlit
</div>
""", unsafe_allow_html=True)
