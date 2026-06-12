import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return ChatGroq(api_key=os.getenv("GROQ_API_KEY"),
                    model_name="llama-3.3-70b-versatile")

SUBMITTAL_TYPES   = ["Shop Drawing", "Product Data", "Sample", "Test Report",
                     "Operation Manual", "Warranty", "As-Built Drawing", "Certificate", "Other"]
SUBMITTAL_STATUS  = ["Pending Submission", "Submitted", "Under Review",
                     "Approved", "Approved with Comments", "Rejected", "Resubmit Required"]
DISCIPLINES       = ["Architecture", "Structure", "MEP — Mechanical",
                     "MEP — Electrical", "MEP — Plumbing", "Civil", "Facade", "General"]
STATUS_COLORS     = {
    "Pending Submission":   "#4A6A8A",
    "Submitted":            "#00D4FF",
    "Under Review":         "#FFB200",
    "Approved":             "#00FF64",
    "Approved with Comments":"#00FFB2",
    "Rejected":             "#FF4444",
    "Resubmit Required":    "#FF7850",
}

def init_state():
    if "submittals" not in st.session_state:
        st.session_state.submittals = []

def create_submittal(title, stype, discipline, spec_section,
                     required_by, submitted_by, priority):
    return {
        "id":           str(uuid.uuid4())[:8].upper(),
        "title":        title,
        "type":         stype,
        "discipline":   discipline,
        "spec_section": spec_section,
        "required_by":  required_by,
        "submitted_by": submitted_by,
        "priority":     priority,
        "status":       "Pending Submission",
        "created_at":   datetime.now().strftime("%d %b %Y"),
        "updated_at":   datetime.now().strftime("%d %b %Y"),
        "comments":     []
    }

def import_from_boq(df):
    count = 0
    for _, row in df.iterrows():
        item = str(row.iloc[0]).strip()
        if not item or item.lower() in ["nan", "item", "description"]:
            continue
        item_lower = item.lower()
        stype = "Shop Drawing"
        if any(x in item_lower for x in ["tile", "paint", "fabric", "sample"]):
            stype = "Sample"
        elif any(x in item_lower for x in ["pump", "ahu", "chiller", "lift", "dg"]):
            stype = "Product Data"
        disc = "General"
        if any(x in item_lower for x in ["concrete", "rebar", "steel", "column", "beam"]):
            disc = "Structure"
        elif any(x in item_lower for x in ["duct", "pipe", "cable", "conduit", "pump"]):
            disc = "MEP — Mechanical"
        elif any(x in item_lower for x in ["tile", "paint", "door", "window", "wall"]):
            disc = "Architecture"
        s = create_submittal(item[:60], stype, disc, "—", "—", "—", "Medium")
        st.session_state.submittals.append(s)
        count += 1
    return count

def analyze_submittals():
    if not st.session_state.submittals:
        return "No submittals to analyze."
    llm  = get_llm()
    data = pd.DataFrame(st.session_state.submittals)[
        ["id","title","type","discipline","status","priority","required_by"]
    ].to_csv(index=False)
    prompt = f"""You are a senior BIM project manager analyzing a submittal register.

Submittal Register:
{data}

Produce a SUBMITTAL INTELLIGENCE REPORT:

## SUBMITTAL STATUS SUMMARY
Overall health: approved vs pending vs overdue. Flag any critical gaps.

## CRITICAL PATH SUBMITTALS
Which submittals, if delayed, will stop procurement or construction?
For each: title, why it's critical, recommended action date.

## LONG LEAD ITEMS
Identify equipment/materials likely to have 8+ week lead times
(chillers, lifts, transformers, structural steel, curtain wall).
Flag if procurement has not started.

## BULK PROCUREMENT OPPORTUNITIES
Which submittals can be batched for better pricing?

## TOP 3 ACTIONS THIS WEEK
Exactly 3 specific actions to keep submittals on track."""
    return llm.invoke(prompt).content

SUB_CSS = """
<style>
.sub-header { background:linear-gradient(135deg,#070F1E,#0D1B2E); border:1px solid rgba(0,212,150,0.15); border-radius:18px; padding:26px 30px; margin-bottom:20px; }
.sub-title  { font-family:'DM Serif Display',serif; font-size:1.9rem; color:#FFF; }
.sub-title span { color:#00D496; }
.sub-sub    { font-family:'DM Sans',sans-serif; font-size:0.87rem; color:#2A4A6A; }
.sub-badge  { display:inline-block; background:rgba(0,212,150,0.08); border:1px solid rgba(0,212,150,0.2); color:#00D496; font-family:'Space Mono',monospace; font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:4px; margin-right:8px; margin-bottom:10px; }
.sub-card   { background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); border-radius:10px; padding:12px 16px; margin-bottom:8px; }
.sub-id     { font-family:'Space Mono',monospace; font-size:0.62rem; color:#00D496; }
.sub-title-text { font-family:'DM Sans',sans-serif; font-size:0.92rem; font-weight:600; color:#E0F0FF; margin:4px 0 2px 0; }
.sub-meta   { font-family:'DM Sans',sans-serif; font-size:0.75rem; color:#2A4A6A; }
.sub-divider{ border:none; border-top:1px solid rgba(255,255,255,0.04); margin:20px 0; }
</style>
"""

def show_submittal_tracker():
    init_state()
    st.markdown(SUB_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class='sub-header'>
        <div><span class='sub-badge'>NEW</span><span class='sub-badge'>v1.0</span></div>
        <div class='sub-title'>BIM <span>Submittal</span> Tracker</div>
        <div class='sub-sub'>Track every shop drawing, product data, and sample submittal. Import from BOQ. Get AI analysis of critical path and long-lead items.</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    total    = len(st.session_state.submittals)
    approved = sum(1 for s in st.session_state.submittals if "Approved" in s["status"])
    pending  = sum(1 for s in st.session_state.submittals if s["status"] == "Pending Submission")
    st.markdown(f"""
    <div style='display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;'>
        <div style='background:rgba(255,255,255,0.02);border:1px solid rgba(0,212,150,0.1);border-radius:12px;padding:14px 20px;flex:1;min-width:100px;'>
            <div style='font-family:DM Serif Display,serif;font-size:1.8rem;color:#00D496;'>{total}</div>
            <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#1E3A5F;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>Total</div>
        </div>
        <div style='background:rgba(255,255,255,0.02);border:1px solid rgba(0,212,150,0.1);border-radius:12px;padding:14px 20px;flex:1;min-width:100px;'>
            <div style='font-family:DM Serif Display,serif;font-size:1.8rem;color:#00FF64;'>{approved}</div>
            <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#1E3A5F;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>Approved</div>
        </div>
        <div style='background:rgba(255,255,255,0.02);border:1px solid rgba(0,212,150,0.1);border-radius:12px;padding:14px 20px;flex:1;min-width:100px;'>
            <div style='font-family:DM Serif Display,serif;font-size:1.8rem;color:#FF7850;'>{pending}</div>
            <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#1E3A5F;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>Pending</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Submittal Register",
        "➕ Add Submittal",
        "📥 Import from BOQ CSV",
        "🤖 AI Analysis"
    ])

    with tab1:
        if not st.session_state.submittals:
            st.markdown("""<div style='text-align:center;padding:40px;font-family:DM Sans,sans-serif;font-size:0.85rem;color:#1E3A5F;'>
            No submittals yet. Add manually or import from BOQ CSV.</div>""", unsafe_allow_html=True)
        else:
            for s in st.session_state.submittals:
                color = STATUS_COLORS.get(s["status"], "#4A6A8A")
                st.markdown(f"""
                <div class='sub-card'>
                    <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:6px;'>
                        <div>
                            <div class='sub-id'>#{s['id']}</div>
                            <div class='sub-title-text'>{s['title']}</div>
                            <div class='sub-meta'>{s['type']} · {s['discipline']} · Required by: {s['required_by']}</div>
                        </div>
                        <span style='background:{color}20;border:1px solid {color}40;color:{color};
                        font-family:Space Mono,monospace;font-size:0.62rem;padding:3px 10px;border-radius:4px;'>
                        {s['status']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                new_status = st.selectbox(
                    f"Update status #{s['id']}", SUBMITTAL_STATUS,
                    index=SUBMITTAL_STATUS.index(s["status"]),
                    key=f"sub_status_{s['id']}", label_visibility="collapsed"
                )
                if new_status != s["status"]:
                    for sub in st.session_state.submittals:
                        if sub["id"] == s["id"]:
                            sub["status"] = new_status
                            sub["updated_at"] = datetime.now().strftime("%d %b %Y")
                    st.rerun()

    with tab2:
        with st.form("new_sub_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                title       = st.text_input("Submittal Title *", placeholder="e.g. Curtain Wall Shop Drawing")
                stype       = st.selectbox("Type", SUBMITTAL_TYPES)
                discipline  = st.selectbox("Discipline", DISCIPLINES)
            with c2:
                spec_section = st.text_input("Spec Section", placeholder="e.g. 08 44 13")
                required_by  = st.text_input("Required By Date", placeholder="e.g. 15 Jul 2025")
                submitted_by = st.text_input("Submitted By", placeholder="e.g. Main Contractor")
                priority     = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"])
            if st.form_submit_button("➕ Add Submittal"):
                if title.strip():
                    s = create_submittal(title, stype, discipline,
                                         spec_section, required_by, submitted_by, priority)
                    st.session_state.submittals.append(s)
                    st.success(f"✓ Submittal #{s['id']} added.")
                    st.rerun()

    with tab3:
        st.markdown("""<div style='font-family:DM Sans,sans-serif;font-size:0.82rem;color:#2A4A6A;margin-bottom:10px;'>
        Upload your BOQ or quantity takeoff CSV. Each line item becomes a submittal automatically.</div>""",
        unsafe_allow_html=True)
        boq_file = st.file_uploader("BOQ CSV", type=["csv"],
                                     key="sub_boq_upload", label_visibility="collapsed")
        if boq_file:
            df = pd.read_csv(boq_file)
            st.dataframe(df.head(5), use_container_width=True)
            if st.button("⚡ Import as Submittals"):
                count = import_from_boq(df)
                st.success(f"✓ {count} submittals imported.")
                st.rerun()

    with tab4:
        if st.button("🤖 Run Submittal Intelligence Analysis"):
            with st.spinner("Analyzing submittal register..."):
                result = analyze_submittals()
                st.session_state["sub_analysis"] = result
        if "sub_analysis" in st.session_state:
            st.markdown(st.session_state["sub_analysis"])
            st.download_button("⬇️ Download Analysis",
                data=st.session_state["sub_analysis"],
                file_name=f"NexBIM_Submittals_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", key="dl_sub")

    st.markdown("""<div style='text-align:center;font-family:Space Mono,monospace;font-size:0.6rem;
    color:#0E1E30;margin-top:24px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.03);'>
    NEXBIM SUBMITTAL TRACKER v1.0 · DEVENDRA GUPTA</div>""", unsafe_allow_html=True)
