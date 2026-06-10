import streamlit as st
from groq import Groq
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_projects():
    if "projects" not in st.session_state:
        st.session_state.projects = {}
    return st.session_state.projects

def save_project(project_id, project_data):
    if "projects" not in st.session_state:
        st.session_state.projects = {}
    st.session_state.projects[project_id] = project_data

def delete_project(project_id):
    if "projects" in st.session_state:
        if project_id in st.session_state.projects:
            del st.session_state.projects[project_id]

def calculate_health_score(project):
    score = 0
    checks = project.get("checks", {})
    total_checks = 10
    completed = sum(1 for v in checks.values() if v)
    score = int((completed / total_checks) * 100)
    return score

def get_health_color(score):
    if score >= 80:
        return "#00FFB2"
    elif score >= 60:
        return "#FFD93D"
    elif score >= 40:
        return "#FF9F43"
    else:
        return "#FF6B6B"

def get_health_label(score):
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Needs Attention"

def show_dashboard():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

    .dash-hero {
        background: linear-gradient(135deg, #050D1A 0%, #0A1628 100%);
        border: 1px solid rgba(0,255,178,0.2);
        border-radius: 20px;
        padding: 28px 32px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .dash-hero::before {
        content: '';
        position: absolute;
        top: -40%; right: -10%;
        width: 350px; height: 350px;
        background: radial-gradient(circle,
            rgba(0,255,178,0.06) 0%, transparent 70%);
        pointer-events: none;
    }
    .dash-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem; font-weight: 800;
        color: #FFFFFF; margin: 0 0 4px 0;
        letter-spacing: -0.5px;
    }
    .dash-title span { color: #00FFB2; }
    .dash-sub {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.88rem; color: #4A6A8A;
    }
    .dash-kpi-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 24px;
    }
    .dash-kpi {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 18px 20px;
    }
    .dash-kpi-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem; color: #2A4A6A;
        letter-spacing: 2px; text-transform: uppercase;
        margin-bottom: 8px;
    }
    .dash-kpi-value {
        font-family: 'Syne', sans-serif;
        font-size: 2rem; font-weight: 800;
        color: #00FFB2; line-height: 1;
        margin-bottom: 4px;
    }
    .dash-kpi-sub {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.78rem; color: #4A6A8A;
    }
    .proj-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 12px;
        transition: border-color 0.2s ease;
    }
    .proj-card:hover {
        border-color: rgba(0,255,178,0.2);
    }
    .proj-name {
        font-family: 'Syne', sans-serif;
        font-size: 1.1rem; font-weight: 700;
        color: #E0F0FF; margin-bottom: 4px;
    }
    .proj-meta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem; color: #2A4A6A;
        letter-spacing: 1px; margin-bottom: 12px;
    }
    .proj-score-bar {
        height: 4px;
        border-radius: 2px;
        background: rgba(255,255,255,0.06);
        margin-bottom: 8px;
        overflow: hidden;
    }
    .proj-score-fill {
        height: 100%;
        border-radius: 2px;
        transition: width 0.5s ease;
    }
    .proj-tags {
        display: flex; gap: 8px;
        flex-wrap: wrap; margin-top: 8px;
    }
    .proj-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem; padding: 2px 8px;
        border-radius: 4px;
    }
    .tag-type {
        background: rgba(0,212,255,0.08);
        color: #00D4FF;
        border: 1px solid rgba(0,212,255,0.2);
    }
    .tag-status {
        background: rgba(0,255,178,0.08);
        color: #00FFB2;
        border: 1px solid rgba(0,255,178,0.2);
    }
    .tag-loc {
        background: rgba(255,107,107,0.08);
        color: #FF6B6B;
        border: 1px solid rgba(255,107,107,0.2);
    }
    .add-proj-form {
        background: rgba(0,255,178,0.02);
        border: 1px solid rgba(0,255,178,0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .form-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem; color: #00FFB2;
        letter-spacing: 2px; margin-bottom: 16px;
    }
    .health-check-item {
        display: flex; gap: 10px;
        align-items: center; padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.85rem; color: #A0B4C8;
    }
    .analytics-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .analytics-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem; color: #00FFB2;
        letter-spacing: 2px; margin-bottom: 14px;
    }
    .nex-section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem; color: #1E3A5F;
        letter-spacing: 2px; text-transform: uppercase;
        margin: 20px 0 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    projects = get_projects()

    total_projects = len(projects)
    avg_health = int(sum(
        calculate_health_score(p) for p in projects.values()
    ) / total_projects) if total_projects > 0 else 0
    active_projects = sum(
        1 for p in projects.values()
        if p.get("status") == "Active"
    )
    total_cost = sum(
        p.get("estimated_cost", 0) for p in projects.values()
    )

    st.markdown(f"""
    <div class='dash-hero'>
        <div style='font-family:JetBrains Mono,monospace;
        font-size:0.68rem; color:#00FFB2;
        letter-spacing:3px; margin-bottom:10px;'>
        ◈ NEXBIM DASHBOARD</div>
        <div class='dash-title'>
            Multi Project <span>Intelligence</span>
        </div>
        <p class='dash-sub'>
            Track, analyze, and manage all your BIM projects
            in one place. Monitor health scores, costs, and
            milestones across your entire portfolio.
        </p>
    </div>
    """, unsafe_allow_html=True)

    health_color = get_health_color(avg_health)
    cost_display = f"₹{total_cost/100000:.1f}L" if total_cost > 0 else "—"

    st.markdown(f"""
    <div class='dash-kpi-row'>
        <div class='dash-kpi'>
            <div class='dash-kpi-label'>Total Projects</div>
            <div class='dash-kpi-value'>{total_projects}</div>
            <div class='dash-kpi-sub'>In portfolio</div>
        </div>
        <div class='dash-kpi'>
            <div class='dash-kpi-label'>Active Projects</div>
            <div class='dash-kpi-value' style='color:#00D4FF;'>
            {active_projects}</div>
            <div class='dash-kpi-sub'>Currently running</div>
        </div>
        <div class='dash-kpi'>
            <div class='dash-kpi-label'>Avg Health Score</div>
            <div class='dash-kpi-value' style='color:{health_color};'>
            {avg_health}%</div>
            <div class='dash-kpi-sub'>{get_health_label(avg_health)}</div>
        </div>
        <div class='dash-kpi'>
            <div class='dash-kpi-label'>Total Est. Cost</div>
            <div class='dash-kpi-value' style='color:#FFD93D;'>
            {cost_display}</div>
            <div class='dash-kpi-sub'>Across all projects</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📋  Projects",
        "➕  Add Project",
        "📊  Analytics"
    ])

    with tab1:
        if not projects:
            st.markdown("""
            <div style='text-align:center; padding:60px 20px;
            color:#1E3A5F;'>
                <div style='font-size:3rem; margin-bottom:12px;
                opacity:0.3;'>◈</div>
                <div style='font-family:Syne,sans-serif;
                font-size:1.1rem; font-weight:700;
                color:#1E3A5F; margin-bottom:8px;'>
                No Projects Yet</div>
                <div style='font-family:Space Grotesk,sans-serif;
                font-size:0.85rem; color:#0E1E30;'>
                Go to Add Project tab to create your first project
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for proj_id, proj in projects.items():
                score = calculate_health_score(proj)
                health_col = get_health_color(score)
                health_lab = get_health_label(score)

                col_main, col_btn = st.columns([5, 1])

                with col_main:
                    st.markdown(f"""
                    <div class='proj-card'>
                        <div class='proj-name'>
                        {proj.get('name', 'Unnamed Project')}</div>
                        <div class='proj-meta'>
                        {proj.get('created', 'Unknown date')} &nbsp;·&nbsp;
                        {proj.get('client', 'No client')}
                        </div>
                        <div style='display:flex; align-items:center;
                        gap:10px; margin-bottom:6px;'>
                            <div class='proj-score-bar' style='flex:1;'>
                                <div class='proj-score-fill'
                                style='width:{score}%;
                                background:{health_col};'></div>
                            </div>
                            <div style='font-family:JetBrains Mono,monospace;
                            font-size:0.75rem; color:{health_col};
                            white-space:nowrap;'>
                            {score}% · {health_lab}</div>
                        </div>
                        <div class='proj-tags'>
                            <span class='proj-tag tag-type'>
                            {proj.get('type', 'Unknown')}</span>
                            <span class='proj-tag tag-status'>
                            {proj.get('status', 'Active')}</span>
                            <span class='proj-tag tag-loc'>
                            {proj.get('location', 'Unknown')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_btn:
                    st.markdown("<br><br><br>", unsafe_allow_html=True)
                    if st.button("🗑", key=f"del_{proj_id}"):
                        delete_project(proj_id)
                        st.rerun()

                with st.expander(f"📊 Manage — {proj.get('name', '')}"):
                    st.markdown("""
                    <div style='font-family:JetBrains Mono,monospace;
                    font-size:0.65rem; color:#00FFB2;
                    letter-spacing:2px; margin-bottom:12px;'>
                    BIM HEALTH CHECKLIST</div>
                    """, unsafe_allow_html=True)

                    checks_config = [
                        ("bep_done", "BIM Execution Plan created"),
                        ("lod_defined", "LOD Specification defined"),
                        ("cde_setup", "Common Data Environment set up"),
                        ("naming_conv", "Naming conventions established"),
                        ("clash_rules", "Clash detection rules configured"),
                        ("coord_meeting", "Coordination meetings scheduled"),
                        ("model_audit", "Model audit completed"),
                        ("handover_plan", "Handover plan prepared"),
                        ("qs_done", "Quantity survey completed"),
                        ("client_approval", "Client approval received")
                    ]

                    checks = proj.get("checks", {})
                    updated = False

                    for check_key, check_label in checks_config:
                        current_val = checks.get(check_key, False)
                        new_val = st.checkbox(
                            check_label,
                            value=current_val,
                            key=f"chk_{proj_id}_{check_key}"
                        )
                        if new_val != current_val:
                            checks[check_key] = new_val
                            updated = True

                    if updated:
                        proj["checks"] = checks
                        save_project(proj_id, proj)
                        st.rerun()

                    new_score = calculate_health_score(proj)
                    new_color = get_health_color(new_score)
                    st.markdown(f"""
                    <div style='background:rgba(255,255,255,0.02);
                    border:1px solid rgba(255,255,255,0.06);
                    border-radius:10px; padding:14px;
                    margin-top:12px; text-align:center;'>
                        <div style='font-family:Syne,sans-serif;
                        font-size:2.5rem; font-weight:800;
                        color:{new_color};'>{new_score}%</div>
                        <div style='font-family:JetBrains Mono,monospace;
                        font-size:0.7rem; color:{new_color};
                        letter-spacing:1px;'>
                        BIM HEALTH SCORE · {get_health_label(new_score).upper()}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("""
                    <div style='font-family:JetBrains Mono,monospace;
                    font-size:0.65rem; color:#00FFB2;
                    letter-spacing:2px; margin:16px 0 8px 0;'>
                    AI PROJECT INSIGHTS</div>
                    """, unsafe_allow_html=True)

                    if st.button(
                            "Generate AI Insights →",
                            key=f"ai_{proj_id}"):
                        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                        completed_checks = [
                            label for key, label in checks_config
                            if checks.get(key, False)
                        ]
                        pending_checks = [
                            label for key, label in checks_config
                            if not checks.get(key, False)
                        ]
                        with st.spinner("Analyzing project..."):
                            response = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{
                                    "role": "user",
                                    "content": f"""You are NexBIM,
an expert BIM project manager.

Analyze this BIM project and give actionable insights.

Project: {proj.get('name')}
Type: {proj.get('type')}
Location: {proj.get('location')}
Client: {proj.get('client')}
Health Score: {new_score}%

Completed BIM Checks: {', '.join(completed_checks) if completed_checks else 'None'}
Pending BIM Checks: {', '.join(pending_checks) if pending_checks else 'None'}

Provide:
1. Project health assessment
2. Top 3 immediate action items
3. Risks if pending items are not addressed
4. Timeline recommendation

Keep it concise and practical."""
                                }],
                                max_tokens=800
                            )
                        answer = response.choices[0].message.content
                        st.markdown(f"""
                        <div style='background:rgba(0,255,178,0.02);
                        border:1px solid rgba(0,255,178,0.1);
                        border-left:3px solid #00FFB2;
                        border-radius:0 12px 12px 0;
                        padding:16px 20px; margin-top:8px;
                        font-family:Space Grotesk,sans-serif;
                        font-size:0.88rem; color:#A0B4C8;
                        line-height:1.7;'>
                        {answer.replace(chr(10), '<br>')}
                        </div>
                        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("""
        <div class='add-proj-form'>
        <div class='form-title'>◈ ADD NEW PROJECT</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input(
                "Project Name",
                placeholder="e.g. Sunrise Tower Block A",
                key="new_proj_name"
            )
            new_location = st.text_input(
                "Location",
                placeholder="e.g. Mumbai, Maharashtra",
                key="new_proj_loc"
            )
            new_client = st.text_input(
                "Client Name",
                placeholder="e.g. ABC Developers",
                key="new_proj_client"
            )

        with col2:
            new_type = st.selectbox(
                "Building Type",
                [
                    "Residential — Single Family",
                    "Residential — Multi Family",
                    "Commercial — Office",
                    "Commercial — Retail",
                    "Industrial",
                    "Healthcare",
                    "Educational",
                    "Hospitality — Hotel",
                    "Mixed Use",
                    "Infrastructure"
                ],
                key="new_proj_type"
            )
            new_status = st.selectbox(
                "Project Status",
                ["Active", "On Hold", "Completed", "Planning"],
                key="new_proj_status"
            )
            new_cost = st.number_input(
                "Estimated Cost (₹ Lakhs)",
                min_value=0,
                value=0,
                step=10,
                key="new_proj_cost"
            )

        new_desc = st.text_area(
            "Project Description",
            placeholder="Brief description of the project scope...",
            key="new_proj_desc",
            height=80
        )

        if st.button(
                "➕  Add Project to Dashboard",
                key="add_proj_btn"):
            if new_name and new_location and new_client:
                proj_id = f"proj_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                project_data = {
                    "name": new_name,
                    "location": new_location,
                    "client": new_client,
                    "type": new_type,
                    "status": new_status,
                    "estimated_cost": new_cost * 100000,
                    "description": new_desc,
                    "created": datetime.now().strftime("%B %d, %Y"),
                    "checks": {}
                }
                save_project(proj_id, project_data)
                st.success(f"✓ Project '{new_name}' added successfully!")
                st.rerun()
            else:
                st.error(
                    "Please fill in Project Name, Location, and Client.")

    with tab3:
        if not projects:
            st.markdown("""
            <div style='text-align:center; padding:40px;
            color:#1E3A5F; font-family:Space Grotesk,sans-serif;'>
            Add projects first to see analytics.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='font-family:JetBrains Mono,monospace;
            font-size:0.65rem; color:#00FFB2;
            letter-spacing:2px; margin-bottom:16px;'>
            PROJECT HEALTH COMPARISON</div>
            """, unsafe_allow_html=True)

            for proj_id, proj in projects.items():
                score = calculate_health_score(proj)
                health_col = get_health_color(score)
                bar_width = score

                st.markdown(f"""
                <div style='margin-bottom:12px;'>
                    <div style='display:flex; justify-content:space-between;
                    align-items:center; margin-bottom:4px;'>
                        <div style='font-family:Space Grotesk,sans-serif;
                        font-size:0.88rem; color:#E0F0FF;'>
                        {proj.get('name', 'Unknown')}</div>
                        <div style='font-family:JetBrains Mono,monospace;
                        font-size:0.72rem; color:{health_col};'>
                        {score}%</div>
                    </div>
                    <div style='height:6px; background:rgba(255,255,255,0.05);
                    border-radius:3px; overflow:hidden;'>
                        <div style='height:100%; width:{bar_width}%;
                        background:linear-gradient(90deg,
                        {health_col} 0%, {health_col}88 100%);
                        border-radius:3px;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div style='font-family:JetBrains Mono,monospace;
            font-size:0.65rem; color:#00D4FF;
            letter-spacing:2px; margin:20px 0 12px 0;'>
            PROJECT STATUS BREAKDOWN</div>
            """, unsafe_allow_html=True)

            status_counts = {}
            for proj in projects.values():
                s = proj.get("status", "Unknown")
                status_counts[s] = status_counts.get(s, 0) + 1

            for status, count in status_counts.items():
                pct = int((count / total_projects) * 100)
                status_colors = {
                    "Active": "#00FFB2",
                    "Planning": "#00D4FF",
                    "On Hold": "#FFD93D",
                    "Completed": "#A0B4C8"
                }
                col = status_colors.get(status, "#4A6A8A")
                st.markdown(f"""
                <div style='display:flex; align-items:center;
                gap:12px; margin-bottom:8px;'>
                    <div style='font-family:Space Grotesk,sans-serif;
                    font-size:0.85rem; color:#A0B4C8;
                    width:100px;'>{status}</div>
                    <div style='flex:1; height:4px;
                    background:rgba(255,255,255,0.05);
                    border-radius:2px; overflow:hidden;'>
                        <div style='height:100%; width:{pct}%;
                        background:{col};
                        border-radius:2px;'></div>
                    </div>
                    <div style='font-family:JetBrains Mono,monospace;
                    font-size:0.7rem; color:{col};'>
                    {count} ({pct}%)</div>
                </div>
                """, unsafe_allow_html=True)

            if any(p.get("estimated_cost", 0) > 0
                   for p in projects.values()):
                st.markdown("""
                <div style='font-family:JetBrains Mono,monospace;
                font-size:0.65rem; color:#FFD93D;
                letter-spacing:2px; margin:20px 0 12px 0;'>
                COST BREAKDOWN BY PROJECT</div>
                """, unsafe_allow_html=True)

                for proj_id, proj in projects.items():
                    cost = proj.get("estimated_cost", 0)
                    if cost > 0:
                        cost_display = f"₹{cost/100000:.1f}L"
                        total_c = sum(
                            p.get("estimated_cost", 0)
                            for p in projects.values()
                        )
                        pct_cost = int((cost / total_c) * 100) \
                            if total_c > 0 else 0
                        st.markdown(f"""
                        <div style='display:flex;
                        align-items:center;
                        gap:12px; margin-bottom:8px;'>
                            <div style='font-family:Space Grotesk,sans-serif;
                            font-size:0.85rem; color:#A0B4C8;
                            width:160px; overflow:hidden;
                            text-overflow:ellipsis;
                            white-space:nowrap;'>
                            {proj.get('name', 'Unknown')}</div>
                            <div style='flex:1; height:4px;
                            background:rgba(255,255,255,0.05);
                            border-radius:2px; overflow:hidden;'>
                                <div style='height:100%;
                                width:{pct_cost}%;
                                background:#FFD93D;
                                border-radius:2px;'></div>
                            </div>
                            <div style='font-family:JetBrains Mono,monospace;
                            font-size:0.7rem; color:#FFD93D;'>
                            {cost_display}</div>
                        </div>
                        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; margin-top:20px;
    font-family:JetBrains Mono,monospace;
    font-size:0.6rem; color:#0E1E30; letter-spacing:1px;'>
        NEXBIM DASHBOARD · MULTI PROJECT INTELLIGENCE ·
        BUILT BY DEVENDRA GUPTA
    </div>
    """, unsafe_allow_html=True)