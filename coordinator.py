import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# ── helpers ──────────────────────────────────────────────────────────────────

def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile"
    )

def parse_clash_csv(file) -> pd.DataFrame:
    """Accept Navisworks CSV export or any clash CSV."""
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        return None

def parse_schedule_csv(file) -> pd.DataFrame:
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return None

def parse_rfi_csv(file) -> pd.DataFrame:
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return None

def df_to_text(df: pd.DataFrame, max_rows: int = 60) -> str:
    return df.head(max_rows).to_csv(index=False)

# ── AI analysis functions ─────────────────────────────────────────────────────

def analyze_clash_priority(clash_df: pd.DataFrame) -> str:
    llm = get_llm()
    clash_text = df_to_text(clash_df)
    prompt = f"""You are a senior BIM Coordination Manager analyzing a Navisworks clash report.

Clash Report Data:
{clash_text}

Analyze these clashes and produce a structured CLASH PRIORITY MATRIX.

Your output must follow this exact structure:

## CLASH PRIORITY MATRIX

### CRITICAL — Stop-Work Risk (resolve within 24 hours)
List clashes that will physically block construction or cause rework if unresolved. For each: clash name/ID, disciplines involved, why it is critical, consequence if ignored.

### HIGH — Schedule Risk (resolve within 3 days)
List clashes that sit on likely critical path activities. For each: clash name/ID, disciplines involved, schedule impact.

### MEDIUM — Coordination Required (resolve within 1 week)
List clashes needing inter-discipline coordination but not immediately blocking work.

### LOW — Monitor (resolve before construction phase)
List clashes that can be resolved during normal coordination cycles.

### SUMMARY INTELLIGENCE
- Total clashes reviewed: [number]
- Critical clashes: [number]
- Most conflicting discipline pair: [e.g. MEP vs Structure]
- Top recommendation: [one clear action the coordination team should take today]

Be specific. Use actual clash names and data from the CSV. Do not be vague."""

    response = llm.invoke(prompt)
    return response.content


def analyze_critical_path(clash_df: pd.DataFrame, schedule_df: pd.DataFrame) -> str:
    llm = get_llm()
    clash_text = df_to_text(clash_df)
    schedule_text = df_to_text(schedule_df)
    prompt = f"""You are a senior BIM Coordination Manager with deep knowledge of construction scheduling.

Clash Report:
{clash_text}

Project Schedule:
{schedule_text}

Cross-reference the clash data against the project schedule and produce a CRITICAL PATH CONFLICT REPORT.

Your output must follow this exact structure:

## CRITICAL PATH CONFLICT REPORT

### CLASHES DIRECTLY ON CRITICAL PATH
For each conflict: which clash, which schedule activity it affects, planned start date of that activity, days of delay risk if clash is unresolved.

### PROCUREMENT TRIGGERS
List any clashes involving elements that have long lead times (structural steel, large MEP equipment, facade systems). Flag if procurement has likely not been triggered yet.

### CASCADE RISK
Identify any clashes where resolving one will likely create new clashes downstream. Explain the cascade.

### SCHEDULE IMPACT SUMMARY
- Activities at immediate risk: [list]
- Estimated total delay if top 3 clashes go unresolved: [X days]
- Recommended sequencing for clash resolution: [ordered list]

### IMMEDIATE ACTIONS
List exactly 3 things the project manager must do TODAY to protect the schedule.

Use actual data from both CSVs. Be direct and specific."""

    response = llm.invoke(prompt)
    return response.content


def generate_stakeholder_briefing(clash_df: pd.DataFrame, schedule_df=None, rfi_df=None) -> str:
    llm = get_llm()
    clash_text = df_to_text(clash_df)
    schedule_section = f"\nProject Schedule:\n{df_to_text(schedule_df)}" if schedule_df is not None else ""
    rfi_section = f"\nRFI Log:\n{df_to_text(rfi_df)}" if rfi_df is not None else ""

    prompt = f"""You are translating a BIM coordination report for a non-technical client — a developer, building owner, or project director who does not use Revit or Navisworks.

Clash Report:
{clash_text}{schedule_section}{rfi_section}

Write a STAKEHOLDER BRIEFING in plain language. No BIM jargon. No technical terms without explanation.

Your output must follow this exact structure:

## PROJECT COORDINATION BRIEFING
### For: Project Owner / Developer
### Date: {datetime.now().strftime('%B %d, %Y')}

---

### WHAT IS THIS REPORT?
One paragraph explaining what BIM coordination clashes are in plain language — what they mean for the project and why they matter to cost and schedule.

### PROJECT HEALTH: [GREEN / AMBER / RED]
One sentence verdict on the current coordination health of this project and why.

### THE 3 THINGS YOU NEED TO KNOW RIGHT NOW
Written as numbered points in plain English. Each point: what the issue is, what it means for you as the client, and what should happen next.

### WHAT COULD THIS COST IF IGNORED?
Translate the top clashes into potential cost and time consequences in plain terms. Use INR estimates where relevant. Be honest, not alarming.

### QUESTIONS TO ASK YOUR BIM TEAM TODAY
List 5 specific questions the client should ask their architects, engineers, or BIM manager at the next meeting.

### WHAT HAPPENS NEXT
A clear description of the coordination process that should now happen, and what the client should expect to receive and when.

Write in a calm, professional tone. This person is paying for the building. They deserve clarity."""

    response = llm.invoke(prompt)
    return response.content


def generate_coordination_summary(clash_df: pd.DataFrame) -> dict:
    """Generate quick stats for the dashboard cards."""
    total = len(clash_df)
    
    # Try to find status column
    status_col = next((c for c in clash_df.columns 
                       if 'status' in c.lower()), None)
    active = total
    if status_col:
        active = len(clash_df[clash_df[status_col].str.lower().isin(
            ['new', 'active', 'open']) if clash_df[status_col].dtype == object else []])

    # Try to find discipline columns
    disc_cols = [c for c in clash_df.columns 
                 if any(x in c.lower() for x in ['discipline', 'layer', 'item1', 'item2', 'element'])]
    
    top_discipline = "N/A"
    if disc_cols:
        try:
            all_vals = []
            for c in disc_cols[:2]:
                all_vals.extend(clash_df[c].dropna().tolist())
            if all_vals:
                from collections import Counter
                top_discipline = Counter(all_vals).most_common(1)[0][0]
                if len(top_discipline) > 20:
                    top_discipline = top_discipline[:20] + "..."
        except Exception:
            pass

    return {
        "total": total,
        "active": active,
        "top_discipline": top_discipline,
        "columns": list(clash_df.columns)
    }


# ── UI ────────────────────────────────────────────────────────────────────────

def show_coordinator():
    # CSS — inherits NexBIM theme, adds coordination-specific styles
    st.markdown("""
    <style>
    .coord-header {
        background: linear-gradient(135deg, #070F1E 0%, #0D1B2E 100%);
        border: 1px solid rgba(0,212,255,0.15);
        border-radius: 18px; padding: 26px 30px;
        margin-bottom: 20px; position: relative; overflow: hidden;
    }
    .coord-header::after {
        content: ''; position: absolute; top: -40%; right: -5%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%);
        pointer-events: none;
    }
    .coord-title {
        font-family: 'Syne', sans-serif; font-size: 1.9rem;
        font-weight: 800; color: #FFFFFF; margin: 0 0 4px 0;
        letter-spacing: -0.5px;
    }
    .coord-title span { color: #00D4FF; }
    .coord-sub {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.87rem; color: #2A4A6A; margin: 0;
    }
    .coord-badge {
        display: inline-block;
        background: rgba(0,212,255,0.08);
        border: 1px solid rgba(0,212,255,0.2);
        color: #00D4FF; font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem; letter-spacing: 2px;
        padding: 3px 10px; border-radius: 4px; margin-right: 8px;
    }
    .coord-stat-row {
        display: flex; gap: 10px; flex-wrap: wrap; margin: 16px 0;
    }
    .coord-stat-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(0,212,255,0.1);
        border-radius: 12px; padding: 14px 18px; flex: 1;
        min-width: 120px;
    }
    .coord-stat-value {
        font-family: 'Syne', sans-serif; font-size: 1.8rem;
        font-weight: 800; color: #00D4FF; line-height: 1;
    }
    .coord-stat-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem; color: #1E3A5F;
        letter-spacing: 1.5px; text-transform: uppercase;
        margin-top: 4px;
    }
    .coord-upload-zone {
        background: rgba(0,212,255,0.02);
        border: 1px dashed rgba(0,212,255,0.2);
        border-radius: 14px; padding: 18px 20px; margin-bottom: 12px;
    }
    .coord-upload-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem; color: #00D4FF;
        letter-spacing: 2px; text-transform: uppercase;
        margin-bottom: 8px;
    }
    .coord-upload-hint {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.78rem; color: #1E3A5F; margin-top: 6px;
    }
    .coord-result-box {
        background: rgba(0,212,255,0.02);
        border: 1px solid rgba(0,212,255,0.1);
        border-radius: 14px; padding: 20px 24px; margin-top: 16px;
    }
    .coord-result-title {
        font-family: 'Syne', sans-serif; font-size: 1rem;
        font-weight: 700; color: #00D4FF;
        letter-spacing: 0.3px; margin-bottom: 12px;
    }
    .coord-tab-bar {
        display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap;
    }
    .coord-info-pill {
        background: rgba(0,255,178,0.04);
        border: 1px solid rgba(0,255,178,0.12);
        border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.82rem; color: #4A6A8A;
    }
    .coord-info-pill strong { color: #00FFB2; }
    .coord-divider {
        border: none; border-top: 1px solid rgba(255,255,255,0.04);
        margin: 24px 0;
    }
    .coord-columns-list {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem; color: #2A4A6A;
        background: rgba(255,255,255,0.02);
        border-radius: 8px; padding: 10px 14px; margin-top: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class='coord-header'>
        <div style='margin-bottom:10px;'>
            <span class='coord-badge'>NEW</span>
            <span class='coord-badge'>v1.0</span>
        </div>
        <div class='coord-title'>BIM <span>Coordination</span> Intelligence</div>
        <div class='coord-sub'>
            Upload clash reports, schedules, and RFI logs.
            Get ranked priorities, critical path conflicts, and plain-language briefings — in seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # How it works
    with st.expander("→ How it works"):
        st.markdown("""
        <div class='coord-info-pill'>
            <strong>Step 1 — Upload your files.</strong>
            Export your clash report from Navisworks as CSV.
            Optionally add your project schedule and RFI log.
        </div>
        <div class='coord-info-pill'>
            <strong>Step 2 — Choose your analysis.</strong>
            Clash Priority Matrix ranks every clash by consequence, not just count.
            Critical Path Report crosses clash data with your schedule.
            Stakeholder Briefing translates everything into plain language for your client.
        </div>
        <div class='coord-info-pill'>
            <strong>Step 3 — Act on the intelligence.</strong>
            Download any report as a text file. Share with your team or client directly.
        </div>
        <div class='coord-info-pill'>
            <strong>Navisworks CSV Export:</strong>
            In Navisworks → Clash Detective → Report → Export as CSV.
            Standard columns: Clash Name, Status, Description, Item 1 Layer, Item 2 Layer.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='coord-divider'>", unsafe_allow_html=True)

    # File uploads
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<div class='coord-upload-label'>① Clash Report (Required)</div>",
                    unsafe_allow_html=True)
        clash_file = st.file_uploader(
            "Clash CSV", type=["csv"],
            label_visibility="collapsed",
            key="clash_upload"
        )
        st.markdown(
            "<div class='coord-upload-hint'>Navisworks Clash Detective → Export CSV</div>",
            unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='coord-upload-label'>② Project Schedule (Optional)</div>",
                    unsafe_allow_html=True)
        schedule_file = st.file_uploader(
            "Schedule CSV", type=["csv"],
            label_visibility="collapsed",
            key="schedule_upload"
        )
        st.markdown(
            "<div class='coord-upload-hint'>MS Project / Primavera → Export CSV</div>",
            unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='coord-upload-label'>③ RFI Log (Optional)</div>",
                    unsafe_allow_html=True)
        rfi_file = st.file_uploader(
            "RFI CSV", type=["csv"],
            label_visibility="collapsed",
            key="rfi_upload"
        )
        st.markdown(
            "<div class='coord-upload-hint'>Procore / Aconex → Export CSV</div>",
            unsafe_allow_html=True)

    # Parse files
    clash_df = None
    schedule_df = None
    rfi_df = None

    if clash_file:
        clash_df = parse_clash_csv(clash_file)

    if schedule_file:
        schedule_df = parse_schedule_csv(schedule_file)

    if rfi_file:
        rfi_df = parse_rfi_csv(rfi_file)

    # Show stats if clash file loaded
    if clash_df is not None:
        stats = generate_coordination_summary(clash_df)

        st.markdown(f"""
        <div class='coord-stat-row'>
            <div class='coord-stat-card'>
                <div class='coord-stat-value'>{stats['total']}</div>
                <div class='coord-stat-label'>Total Clashes</div>
            </div>
            <div class='coord-stat-card'>
                <div class='coord-stat-value'>{len(clash_df.columns)}</div>
                <div class='coord-stat-label'>Data Columns</div>
            </div>
            <div class='coord-stat-card'>
                <div class='coord-stat-value'>{'✓' if schedule_df is not None else '—'}</div>
                <div class='coord-stat-label'>Schedule Loaded</div>
            </div>
            <div class='coord-stat-card'>
                <div class='coord-stat-value'>{'✓' if rfi_df is not None else '—'}</div>
                <div class='coord-stat-label'>RFI Log Loaded</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            f"<div class='coord-columns-list'>Detected columns: "
            f"{' · '.join(stats['columns'])}</div>",
            unsafe_allow_html=True
        )

        with st.expander("→ Preview clash data"):
            st.dataframe(clash_df.head(10), use_container_width=True)

        st.markdown("<hr class='coord-divider'>", unsafe_allow_html=True)

        # Analysis tabs
        st.markdown("""
        <div style='font-family:JetBrains Mono,monospace;
        font-size:0.65rem; color:#00D4FF;
        letter-spacing:2px; margin-bottom:12px;'>
        SELECT ANALYSIS
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs([
            "🎯 Clash Priority Matrix",
            "📅 Critical Path Report",
            "👤 Stakeholder Briefing"
        ])

        # ── Tab 1: Clash Priority Matrix ──────────────────────────────────
        with tab1:
            st.markdown("""
            <div class='coord-info-pill'>
                <strong>Clash Priority Matrix</strong> — ranks every clash by consequence.
                Tells you which 3 clashes to fix today, not which 300 exist.
            </div>
            """, unsafe_allow_html=True)

            if st.button("⚡ Run Clash Priority Analysis", key="btn_clash"):
                with st.spinner("Analyzing clash data with AI..."):
                    result = analyze_clash_priority(clash_df)
                    st.session_state["clash_priority_result"] = result

            if "clash_priority_result" in st.session_state:
                st.markdown(
                    "<div class='coord-result-title'>→ Clash Priority Matrix</div>",
                    unsafe_allow_html=True)
                st.markdown(st.session_state["clash_priority_result"])
                st.download_button(
                    label="⬇️ Download Report",
                    data=st.session_state["clash_priority_result"],
                    file_name=f"NexBIM_ClashPriority_"
                              f"{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    key="dl_clash"
                )

        # ── Tab 2: Critical Path Report ───────────────────────────────────
        with tab2:
            st.markdown("""
            <div class='coord-info-pill'>
                <strong>Critical Path Conflict Report</strong> — crosses your clash data with the project schedule.
                Identifies which unresolved clashes will delay your slab pours, steel erection, or handover date.
            </div>
            """, unsafe_allow_html=True)

            if schedule_df is None:
                st.markdown("""
                <div style='background:rgba(255,107,107,0.04);
                border:1px solid rgba(255,107,107,0.15);
                border-radius:10px; padding:14px 18px;
                font-family:Space Grotesk,sans-serif;
                font-size:0.85rem; color:#FF6B6B;'>
                ⚠️ Upload your project schedule CSV (column 2 above) to enable critical path analysis.
                Without the schedule, the AI will still give a best-estimate based on clash data alone.
                </div>
                """, unsafe_allow_html=True)

            if st.button("📅 Run Critical Path Analysis", key="btn_cp"):
                with st.spinner("Cross-referencing clashes with schedule..."):
                    result = analyze_critical_path(
                        clash_df,
                        schedule_df if schedule_df is not None else pd.DataFrame(
                            {"Note": ["No schedule uploaded — AI using clash data only"]})
                    )
                    st.session_state["critical_path_result"] = result

            if "critical_path_result" in st.session_state:
                st.markdown(
                    "<div class='coord-result-title'>→ Critical Path Conflict Report</div>",
                    unsafe_allow_html=True)
                st.markdown(st.session_state["critical_path_result"])
                st.download_button(
                    label="⬇️ Download Report",
                    data=st.session_state["critical_path_result"],
                    file_name=f"NexBIM_CriticalPath_"
                              f"{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    key="dl_cp"
                )

        # ── Tab 3: Stakeholder Briefing ───────────────────────────────────
        with tab3:
            st.markdown("""
            <div class='coord-info-pill'>
                <strong>Stakeholder Briefing</strong> — plain language for your client, developer, or project director.
                No BIM jargon. Just what the issues are, what they mean, and what questions to ask.
            </div>
            """, unsafe_allow_html=True)

            if st.button("👤 Generate Stakeholder Briefing", key="btn_sh"):
                with st.spinner("Writing plain-language briefing..."):
                    result = generate_stakeholder_briefing(
                        clash_df, schedule_df, rfi_df)
                    st.session_state["stakeholder_result"] = result

            if "stakeholder_result" in st.session_state:
                st.markdown(
                    "<div class='coord-result-title'>→ Stakeholder Briefing</div>",
                    unsafe_allow_html=True)
                st.markdown(st.session_state["stakeholder_result"])
                st.download_button(
                    label="⬇️ Download Briefing",
                    data=st.session_state["stakeholder_result"],
                    file_name=f"NexBIM_StakeholderBriefing_"
                              f"{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    key="dl_sh"
                )

    else:
        # Empty state
        st.markdown("""
        <div style='text-align:center; padding:60px 20px;'>
            <div style='font-family:Syne,sans-serif; font-size:3rem;
            color:#00D4FF; opacity:0.15; margin-bottom:16px;'>◈</div>
            <div style='font-family:Syne,sans-serif; font-size:1.1rem;
            font-weight:700; color:#1E3A5F; margin-bottom:10px;'>
            Upload a Clash Report to Begin</div>
            <div style='font-family:Space Grotesk,sans-serif;
            font-size:0.83rem; color:#162840; line-height:2;'>
                "Which of my 847 clashes will actually stop work on site?"<br>
                "Which clash will delay my Level 3 slab pour?"<br>
                "What do I tell my client at tomorrow's meeting?"
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style='text-align:center; font-family:JetBrains Mono,monospace;
    font-size:0.6rem; letter-spacing:1px; color:#0E1E30;
    margin-top:30px; padding-top:14px;
    border-top:1px solid rgba(255,255,255,0.03);'>
        NEXBIM COORDINATION INTELLIGENCE v1.0 · DEVENDRA GUPTA · BIM + AI + AUTOMATION
    </div>
    """, unsafe_allow_html=True)
