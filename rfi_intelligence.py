import streamlit as st
import pandas as pd
import os
from datetime import datetime
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return ChatGroq(api_key=os.getenv("GROQ_API_KEY"),
                    model_name="llama-3.3-70b-versatile")

def parse_rfi_csv(file):
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return None

def df_preview(df, n=60):
    return df.head(n).to_csv(index=False)

def analyze_rfi(df):
    llm  = get_llm()
    data = df_preview(df)
    prompt = f"""You are a senior BIM/construction project manager analyzing an RFI log.

RFI Log Data:
{data}

Produce a structured RFI INTELLIGENCE REPORT with these exact sections:

## RFI INTELLIGENCE REPORT

### ROOT CAUSE ANALYSIS
Group all RFIs by root cause (design gap, coordination clash, specification ambiguity,
site condition, client change). For each group: count, examples, which discipline is responsible.

### DELAY RISK — OVERDUE RFIs
List RFIs open more than 14 days. For each: RFI number/title, days open, responsible party,
consequence if still unanswered, recommended escalation action.

### CONSULTANT PERFORMANCE
Rank consultants/disciplines by RFI response rate and average response time.
Flag the worst performer and explain the downstream impact.

### PREDICTED NON-RESPONSES
Based on age and pattern, identify which open RFIs are at risk of going unanswered.
Explain the pattern you detected.

### TOP 3 ACTIONS FOR TODAY
Exactly 3 specific actions the project manager must take today to reduce RFI risk.

Be specific. Use actual RFI numbers and data from the CSV."""
    return llm.invoke(prompt).content

def draft_rfi_response(rfi_title, rfi_description, discipline):
    llm = get_llm()
    prompt = f"""You are a senior {discipline} consultant drafting a professional RFI response.

RFI Title: {rfi_title}
RFI Description: {rfi_description}
Responding Discipline: {discipline}

Write a professional, concise RFI response letter following Indian construction industry standards.

Format:
**RFI RESPONSE**
Date: {datetime.now().strftime('%B %d, %Y')}
Re: {rfi_title}

[Response body — clear, direct, technically accurate, 3-5 sentences]

**Action Required:** [what the contractor must do next]
**Drawing/Document Reference:** [reference relevant drawings or specs]
**Response by:** {discipline} Consultant"""
    return llm.invoke(prompt).content

RFI_CSS = """
<style>
.rfi-header { background:linear-gradient(135deg,#070F1E,#0D1B2E); border:1px solid rgba(255,120,80,0.15); border-radius:18px; padding:26px 30px; margin-bottom:20px; }
.rfi-title  { font-family:'DM Serif Display',serif; font-size:1.9rem; color:#FFF; margin:0 0 4px 0; }
.rfi-title span { color:#FF7850; }
.rfi-sub    { font-family:'DM Sans',sans-serif; font-size:0.87rem; color:#2A4A6A; }
.rfi-badge  { display:inline-block; background:rgba(255,120,80,0.08); border:1px solid rgba(255,120,80,0.2); color:#FF7850; font-family:'Space Mono',monospace; font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:4px; margin-right:8px; }
.rfi-stat-row { display:flex; gap:10px; flex-wrap:wrap; margin:16px 0; }
.rfi-stat  { background:rgba(255,255,255,0.02); border:1px solid rgba(255,120,80,0.1); border-radius:12px; padding:14px 20px; flex:1; min-width:120px; }
.rfi-stat-v { font-family:'DM Serif Display',serif; font-size:1.8rem; color:#FF7850; line-height:1; }
.rfi-stat-l { font-family:'Space Mono',monospace; font-size:0.6rem; color:#1E3A5F; letter-spacing:1.5px; text-transform:uppercase; margin-top:4px; }
.rfi-divider { border:none; border-top:1px solid rgba(255,255,255,0.04); margin:20px 0; }
</style>
"""

def show_rfi_intelligence():
    st.markdown(RFI_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class='rfi-header'>
        <div style='margin-bottom:10px;'>
            <span class='rfi-badge'>NEW</span><span class='rfi-badge'>v1.0</span>
        </div>
        <div class='rfi-title'>RFI <span>Intelligence</span> Engine</div>
        <div class='rfi-sub'>Upload your RFI log. Get root cause analysis, delay risks, consultant performance ranking, and auto-drafted response letters.</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊 Analyze RFI Log", "✍️ Draft RFI Response"])

    with tab1:
        rfi_file = st.file_uploader("Upload RFI Log CSV", type=["csv"], key="rfi_upload")
        if rfi_file:
            df = parse_rfi_csv(rfi_file)
            if df is not None:
                st.markdown(f"""
                <div class='rfi-stat-row'>
                    <div class='rfi-stat'><div class='rfi-stat-v'>{len(df)}</div><div class='rfi-stat-l'>Total RFIs</div></div>
                    <div class='rfi-stat'><div class='rfi-stat-v'>{len(df.columns)}</div><div class='rfi-stat-l'>Data Columns</div></div>
                </div>
                """, unsafe_allow_html=True)
                with st.expander("Preview data"):
                    st.dataframe(df.head(8), use_container_width=True)
                if st.button("⚡ Run RFI Intelligence Analysis"):
                    with st.spinner("Analyzing RFI log..."):
                        result = analyze_rfi(df)
                        st.session_state["rfi_result"] = result
            if "rfi_result" in st.session_state:
                st.markdown(st.session_state["rfi_result"])
                st.download_button("⬇️ Download Report",
                    data=st.session_state["rfi_result"],
                    file_name=f"NexBIM_RFI_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain", key="dl_rfi")

    with tab2:
        st.markdown("##### Draft a response for a specific RFI")
        c1, c2 = st.columns(2)
        with c1:
            rfi_title = st.text_input("RFI Title", placeholder="e.g. Beam depth conflict at Grid C/3")
            discipline = st.selectbox("Responding Discipline",
                ["Architecture", "Structure", "MEP", "Civil", "Facade", "General"])
        with c2:
            rfi_desc = st.text_area("RFI Description",
                placeholder="Describe the issue raised...", height=100)
        if st.button("✍️ Draft Response Letter"):
            if rfi_title.strip() and rfi_desc.strip():
                with st.spinner("Drafting response..."):
                    response = draft_rfi_response(rfi_title, rfi_desc, discipline)
                    st.session_state["rfi_draft"] = response
            else:
                st.warning("Enter RFI title and description.")
        if "rfi_draft" in st.session_state:
            st.markdown(st.session_state["rfi_draft"])
            st.download_button("⬇️ Download Response",
                data=st.session_state["rfi_draft"],
                file_name=f"NexBIM_RFIResponse_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", key="dl_rfi_draft")

    st.markdown("<div class='rfi-divider'></div>", unsafe_allow_html=True)
    st.markdown("""<div style='text-align:center;font-family:Space Mono,monospace;font-size:0.6rem;color:#0E1E30;'>
    NEXBIM RFI INTELLIGENCE v1.0 · DEVENDRA GUPTA</div>""", unsafe_allow_html=True)
