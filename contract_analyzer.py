import streamlit as st
import os
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tempfile
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return ChatGroq(api_key=os.getenv("GROQ_API_KEY"),
                    model_name="llama-3.3-70b-versatile")

def extract_text_from_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    loader = PyPDFLoader(tmp_path)
    docs   = loader.load()
    os.unlink(tmp_path)
    return "\n\n".join([d.page_content for d in docs])

def analyze_contract(text, contract_type, project_type):
    llm = get_llm()
    # Truncate to fit context
    text_chunk = text[:12000]
    prompt = f"""You are a senior BIM consultant and construction contracts specialist
with deep knowledge of ISO 19650, Indian BIM standards, and construction law.

Contract Type: {contract_type}
Project Type: {project_type}

Contract / Document Text:
{text_chunk}

Analyze this document and produce a BIM CONTRACT ANALYSIS REPORT:

## BIM CONTRACT ANALYSIS REPORT
**Contract Type:** {contract_type}
**Project Type:** {project_type}
**Analyzed:** {datetime.now().strftime('%B %d, %Y')}

---

## DELIVERABLES REGISTER
List every BIM deliverable the contractor/consultant is required to produce.
Format as table:
| Deliverable | Format | Due Date/Stage | Responsible Party |

## ISO 19650 COMPLIANCE CHECK
For each ISO 19650 requirement, check if the contract addresses it:
- Exchange Information Requirements (EIR) ✓/✗/Partial
- BIM Execution Plan (BEP) ✓/✗/Partial
- Master Information Delivery Plan (MIDP) ✓/✗/Partial
- Task Information Delivery Plan (TIDP) ✓/✗/Partial
- Common Data Environment (CDE) ✓/✗/Partial
- Level of Information Need ✓/✗/Partial
- Information Management roles ✓/✗/Partial

## UNREALISTIC REQUIREMENTS
Flag any BIM requirements that are technically unrealistic, ambiguous, or
contradictory. For each: the clause, why it's a problem, recommended revision.

## MISSING CLAUSES
Identify BIM requirements that should be in this contract but are absent.
For each: what's missing, why it matters, suggested clause language.

## COMPLIANCE CHECKLIST
Generate a practical checklist your team can use to track compliance:
| # | Requirement | Due | Owner | Status |

## KEY RISKS
Top 3 contractual risks related to BIM deliverables. For each: risk, likelihood, mitigation.

## RECOMMENDED ACTIONS
5 specific actions your team must take before signing or executing this contract.

Be specific to Indian construction practice and ISO 19650:2018 requirements."""

    return llm.invoke(prompt).content

def analyze_eir(text):
    llm = get_llm()
    text_chunk = text[:10000]
    prompt = f"""You are a BIM Information Manager reviewing an Employer's Information Requirements (EIR).

EIR Text:
{text_chunk}

Extract and summarize:

## EIR SUMMARY

### INFORMATION REQUIREMENTS
List all information deliverables required at each project stage.

### LOD REQUIREMENTS
What Level of Development is required for each discipline at each stage?

### SOFTWARE AND FORMAT REQUIREMENTS
What BIM software, file formats, and naming conventions are specified?

### CDE REQUIREMENTS
What Common Data Environment platform and workflow is specified?

### KEY DATES AND MILESTONES
All BIM-related dates and submission milestones.

### GAPS AND AMBIGUITIES
What is unclear or missing that your team needs clarification on before responding?

### RESPONSE STRATEGY
3 recommendations for how to respond to this EIR."""

    return llm.invoke(prompt).content

CONTRACT_CSS = """
<style>
.con-header { background:linear-gradient(135deg,#070F1E,#0D1B2E); border:1px solid rgba(100,150,255,0.15); border-radius:18px; padding:26px 30px; margin-bottom:20px; }
.con-title  { font-family:'DM Serif Display',serif; font-size:1.9rem; color:#FFF; }
.con-title span { color:#6496FF; }
.con-sub    { font-family:'DM Sans',sans-serif; font-size:0.87rem; color:#2A4A6A; }
.con-badge  { display:inline-block; background:rgba(100,150,255,0.08); border:1px solid rgba(100,150,255,0.2); color:#6496FF; font-family:'Space Mono',monospace; font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:4px; margin-right:8px; margin-bottom:10px; }
.con-divider{ border:none; border-top:1px solid rgba(255,255,255,0.04); margin:20px 0; }
</style>
"""

def show_contract_analyzer():
    st.markdown(CONTRACT_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class='con-header'>
        <div><span class='con-badge'>NEW</span><span class='con-badge'>v1.0</span><span class='con-badge'>ISO 19650</span></div>
        <div class='con-title'>BIM <span>Contract</span> Analyzer</div>
        <div class='con-sub'>Upload any EIR, BIM Protocol, or contract BIM appendix. Get a full deliverables register, ISO 19650 compliance check, unrealistic requirements flagged, and a compliance checklist your team can act on.</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📄 Analyze Contract / BIM Protocol",
                           "📋 Analyze EIR"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            contract_type = st.selectbox("Document Type", [
                "BIM Protocol", "EIR (Employer's Information Requirements)",
                "Contract BIM Appendix", "BIM Execution Plan (to review)",
                "Scope of Services — BIM", "NEC4 BIM Secondary Option X10",
                "FIDIC BIM Supplement", "Other BIM Contract Document"
            ])
        with c2:
            project_type = st.selectbox("Project Type", [
                "Residential", "Commercial Office", "Retail / Mall",
                "Hotel", "Industrial", "Institutional", "Infrastructure", "Mixed Use"
            ])

        upload_method = st.radio("Input method",
            ["Upload PDF", "Paste text"], horizontal=True)

        contract_text = ""
        if upload_method == "Upload PDF":
            pdf_file = st.file_uploader("Upload Contract PDF",
                type=["pdf"], key="contract_pdf", label_visibility="collapsed")
            if pdf_file:
                with st.spinner("Extracting text from PDF..."):
                    contract_text = extract_text_from_pdf(pdf_file)
                st.success(f"✓ Extracted {len(contract_text.split())} words from PDF")
        else:
            contract_text = st.text_area(
                "Paste contract text",
                placeholder="Paste relevant BIM clauses or the full contract text here...",
                height=200
            )

        if st.button("⚡ Analyze Contract"):
            if contract_text.strip():
                with st.spinner("Analyzing against ISO 19650..."):
                    result = analyze_contract(
                        contract_text, contract_type, project_type)
                    st.session_state["contract_result"] = result
            else:
                st.warning("Upload a PDF or paste contract text first.")

        if "contract_result" in st.session_state:
            st.markdown("<div class='con-divider'></div>", unsafe_allow_html=True)
            st.markdown(st.session_state["contract_result"])
            st.download_button("⬇️ Download Analysis",
                data=st.session_state["contract_result"],
                file_name=f"NexBIM_ContractAnalysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", key="dl_contract")

    with tab2:
        eir_method = st.radio("EIR input method",
            ["Upload PDF", "Paste text"], horizontal=True, key="eir_radio")

        eir_text = ""
        if eir_method == "Upload PDF":
            eir_file = st.file_uploader("Upload EIR PDF",
                type=["pdf"], key="eir_pdf", label_visibility="collapsed")
            if eir_file:
                with st.spinner("Extracting text..."):
                    eir_text = extract_text_from_pdf(eir_file)
                st.success(f"✓ {len(eir_text.split())} words extracted")
        else:
            eir_text = st.text_area(
                "Paste EIR text", height=200,
                placeholder="Paste EIR content here...",
                key="eir_text_input"
            )

        if st.button("📋 Analyze EIR", key="btn_eir"):
            if eir_text.strip():
                with st.spinner("Analyzing EIR..."):
                    result = analyze_eir(eir_text)
                    st.session_state["eir_result"] = result
            else:
                st.warning("Upload or paste EIR content first.")

        if "eir_result" in st.session_state:
            st.markdown("<div class='con-divider'></div>", unsafe_allow_html=True)
            st.markdown(st.session_state["eir_result"])
            st.download_button("⬇️ Download EIR Summary",
                data=st.session_state["eir_result"],
                file_name=f"NexBIM_EIR_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", key="dl_eir")

    st.markdown("""<div style='text-align:center;font-family:Space Mono,monospace;font-size:0.6rem;
    color:#0E1E30;margin-top:24px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.03);'>
    NEXBIM CONTRACT ANALYZER v1.0 · DEVENDRA GUPTA · ISO 19650 · BIM PROTOCOL</div>""",
    unsafe_allow_html=True)
