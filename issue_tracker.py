import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime

# ── Constants ─────────────────────────────────────────────────────────────────

DISCIPLINES = [
    "Architecture",
    "Structure",
    "MEP — Mechanical",
    "MEP — Electrical",
    "MEP — Plumbing",
    "Civil",
    "Facade",
    "General"
]

PRIORITIES = ["Critical", "High", "Medium", "Low"]
STATUSES   = ["Open", "In Progress", "Under Review", "Resolved", "Closed"]

PRIORITY_COLORS = {
    "Critical": "#FF4444",
    "High":     "#FF8C00",
    "Medium":   "#FFD93D",
    "Low":      "#00FFB2"
}

STATUS_COLORS = {
    "Open":         "#FF4444",
    "In Progress":  "#FF8C00",
    "Under Review": "#00D4FF",
    "Resolved":     "#00FFB2",
    "Closed":       "#4A6A8A"
}

# ── Session state init ────────────────────────────────────────────────────────

def init_tracker_state():
    if "issues" not in st.session_state:
        st.session_state.issues = []
    if "selected_issue_id" not in st.session_state:
        st.session_state.selected_issue_id = None
    if "tracker_view" not in st.session_state:
        st.session_state.tracker_view = "board"  # board | list | detail

# ── Issue helpers ─────────────────────────────────────────────────────────────

def create_issue(title, description, discipline, priority,
                 assigned_to="", source="Manual", clash_ref=""):
    return {
        "id":           str(uuid.uuid4())[:8].upper(),
        "title":        title,
        "description":  description,
        "discipline":   discipline,
        "priority":     priority,
        "status":       "Open",
        "assigned_to":  assigned_to,
        "source":       source,
        "clash_ref":    clash_ref,
        "created_at":   datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "updated_at":   datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "comments":     [],
        "attachments":  []
    }

def update_issue(issue_id, **kwargs):
    for i, issue in enumerate(st.session_state.issues):
        if issue["id"] == issue_id:
            for k, v in kwargs.items():
                st.session_state.issues[i][k] = v
            st.session_state.issues[i]["updated_at"] = \
                datetime.now().strftime("%d %b %Y, %I:%M %p")
            break

def add_comment(issue_id, author, text):
    for i, issue in enumerate(st.session_state.issues):
        if issue["id"] == issue_id:
            st.session_state.issues[i]["comments"].append({
                "author":     author,
                "text":       text,
                "timestamp":  datetime.now().strftime("%d %b %Y, %I:%M %p")
            })
            st.session_state.issues[i]["updated_at"] = \
                datetime.now().strftime("%d %b %Y, %I:%M %p")
            break

def add_attachment(issue_id, filename, file_bytes):
    for i, issue in enumerate(st.session_state.issues):
        if issue["id"] == issue_id:
            st.session_state.issues[i]["attachments"].append({
                "filename":  filename,
                "size_kb":   round(len(file_bytes) / 1024, 1),
                "uploaded":  datetime.now().strftime("%d %b %Y, %I:%M %p")
            })
            break

def delete_issue(issue_id):
    st.session_state.issues = [
        i for i in st.session_state.issues if i["id"] != issue_id
    ]
    if st.session_state.selected_issue_id == issue_id:
        st.session_state.selected_issue_id = None

def get_stats():
    issues = st.session_state.issues
    total = len(issues)
    by_status   = {s: 0 for s in STATUSES}
    by_priority = {p: 0 for p in PRIORITIES}
    by_disc     = {}
    for issue in issues:
        by_status[issue["status"]]     = by_status.get(issue["status"], 0) + 1
        by_priority[issue["priority"]] = by_priority.get(issue["priority"], 0) + 1
        d = issue["discipline"]
        by_disc[d] = by_disc.get(d, 0) + 1
    open_count     = by_status["Open"]
    resolved_count = by_status["Resolved"] + by_status["Closed"]
    critical_count = by_priority["Critical"]
    top_disc = max(by_disc, key=by_disc.get) if by_disc else "—"
    return {
        "total": total, "open": open_count,
        "resolved": resolved_count, "critical": critical_count,
        "top_disc": top_disc, "by_status": by_status,
        "by_priority": by_priority
    }

def import_from_clash_csv(df: pd.DataFrame) -> int:
    """Parse Navisworks clash CSV and create issues automatically."""
    imported = 0
    # Detect column names flexibly
    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if "name" in cl or "clash" in cl:
            col_map.setdefault("title", col)
        if "description" in cl or "desc" in cl:
            col_map.setdefault("description", col)
        if "item1" in cl or "layer1" in cl or "discipline1" in cl or "element1" in cl:
            col_map.setdefault("disc1", col)
        if "item2" in cl or "layer2" in cl or "discipline2" in cl or "element2" in cl:
            col_map.setdefault("disc2", col)
        if "status" in cl:
            col_map.setdefault("status", col)
        if "type" in cl:
            col_map.setdefault("type", col)

    for _, row in df.iterrows():
        title = str(row.get(col_map.get("title", df.columns[0]), "Unnamed Clash"))
        description = str(row.get(col_map.get("description", ""), "Imported from Navisworks clash report"))
        disc1 = str(row.get(col_map.get("disc1", ""), ""))
        disc2 = str(row.get(col_map.get("disc2", ""), ""))

        # Map to discipline
        discipline = "General"
        combined = (disc1 + " " + disc2).lower()
        if any(x in combined for x in ["mep", "mech", "hvac", "duct"]):
            discipline = "MEP — Mechanical"
        elif any(x in combined for x in ["elec", "conduit", "cable"]):
            discipline = "MEP — Electrical"
        elif any(x in combined for x in ["plumb", "pipe", "sanit"]):
            discipline = "MEP — Plumbing"
        elif any(x in combined for x in ["struct", "beam", "column", "slab"]):
            discipline = "Structure"
        elif any(x in combined for x in ["arch", "wall", "floor", "ceiling"]):
            discipline = "Architecture"

        issue = create_issue(
            title=title[:80],
            description=description[:300] if description != "nan" else
                f"Clash between {disc1} and {disc2}",
            discipline=discipline,
            priority="High",
            source="Clash Import",
            clash_ref=f"{disc1} ↔ {disc2}"
        )
        st.session_state.issues.append(issue)
        imported += 1

    return imported

def export_issues_json() -> str:
    return json.dumps(st.session_state.issues, indent=2)

# ── CSS ───────────────────────────────────────────────────────────────────────

TRACKER_CSS = """
<style>
.it-header {
    background: linear-gradient(135deg, #070F1E 0%, #0D1B2E 100%);
    border: 1px solid rgba(255,178,0,0.15);
    border-radius: 18px; padding: 26px 30px;
    margin-bottom: 20px; position: relative; overflow: hidden;
}
.it-header::after {
    content: ''; position: absolute; top: -40%; right: -5%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(255,178,0,0.05) 0%, transparent 70%);
    pointer-events: none;
}
.it-title {
    font-family: 'Syne', sans-serif; font-size: 1.9rem;
    font-weight: 800; color: #FFFFFF; margin: 0 0 4px 0;
    letter-spacing: -0.5px;
}
.it-title span { color: #FFB200; }
.it-sub {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.87rem; color: #2A4A6A; margin: 0;
}
.it-badge {
    display: inline-block;
    background: rgba(255,178,0,0.08);
    border: 1px solid rgba(255,178,0,0.2);
    color: #FFB200; font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem; letter-spacing: 2px;
    padding: 3px 10px; border-radius: 4px; margin-right: 8px;
}
.it-stat-row {
    display: flex; gap: 10px; flex-wrap: wrap; margin: 16px 0;
}
.it-stat-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,178,0,0.1);
    border-radius: 12px; padding: 14px 20px; flex: 1; min-width: 110px;
}
.it-stat-value {
    font-family: 'Syne', sans-serif; font-size: 2rem;
    font-weight: 800; line-height: 1;
}
.it-stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem; color: #1E3A5F;
    letter-spacing: 1.5px; text-transform: uppercase; margin-top: 4px;
}
.it-issue-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;
    cursor: pointer; transition: border-color 0.2s;
}
.it-issue-card:hover {
    border-color: rgba(255,178,0,0.25);
}
.it-issue-card.selected {
    border-color: rgba(255,178,0,0.4);
    background: rgba(255,178,0,0.03);
}
.it-issue-id {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem; color: #FFB200; letter-spacing: 1px;
}
.it-issue-title {
    font-family: 'Syne', sans-serif; font-size: 0.95rem;
    font-weight: 700; color: #E0F0FF; margin: 4px 0;
}
.it-issue-meta {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.75rem; color: #2A4A6A;
}
.it-priority-dot {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; margin-right: 5px; vertical-align: middle;
}
.it-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem; letter-spacing: 1px;
    padding: 2px 8px; border-radius: 4px; margin-right: 4px;
}
.it-section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem; color: #1E3A5F;
    letter-spacing: 2px; text-transform: uppercase;
    margin: 16px 0 8px 0;
}
.it-detail-box {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,178,0,0.1);
    border-radius: 14px; padding: 20px 24px; margin-bottom: 14px;
}
.it-comment-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px; padding: 12px 14px; margin-bottom: 8px;
}
.it-comment-author {
    font-family: 'Syne', sans-serif; font-size: 0.82rem;
    font-weight: 700; color: #00FFB2;
}
.it-comment-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem; color: #1E3A5F; margin-left: 8px;
}
.it-comment-text {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.83rem; color: #4A6A8A; margin-top: 6px;
}
.it-attach-item {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; color: #2A4A6A;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 6px; padding: 6px 10px; margin-bottom: 4px;
}
.it-empty {
    text-align: center; padding: 60px 20px;
}
.it-empty-icon {
    font-family: 'Syne', sans-serif; font-size: 3rem;
    color: #FFB200; opacity: 0.15; margin-bottom: 14px;
}
.it-empty-title {
    font-family: 'Syne', sans-serif; font-size: 1.1rem;
    font-weight: 700; color: #1E3A5F; margin-bottom: 8px;
}
.it-divider {
    border: none; border-top: 1px solid rgba(255,255,255,0.04);
    margin: 20px 0;
}
</style>
"""

# ── Render helpers ────────────────────────────────────────────────────────────

def priority_tag(priority):
    color = PRIORITY_COLORS.get(priority, "#4A6A8A")
    return (f"<span class='it-tag' style='background:rgba(0,0,0,0.3);"
            f"border:1px solid {color}40; color:{color};'>"
            f"<span class='it-priority-dot' style='background:{color};'></span>"
            f"{priority}</span>")

def status_tag(status):
    color = STATUS_COLORS.get(status, "#4A6A8A")
    return (f"<span class='it-tag' style='background:{color}15;"
            f"border:1px solid {color}40; color:{color};'>{status}</span>")

def source_tag(source):
    color = "#00D4FF" if source == "Clash Import" else "#A0B4C8"
    return (f"<span class='it-tag' style='background:rgba(0,0,0,0.3);"
            f"border:1px solid {color}30; color:{color};'>{source}</span>")

# ── Views ─────────────────────────────────────────────────────────────────────

def render_stats():
    if not st.session_state.issues:
        return
    s = get_stats()
    open_color     = STATUS_COLORS["Open"]
    critical_color = PRIORITY_COLORS["Critical"]
    resolved_color = STATUS_COLORS["Resolved"]

    st.markdown(f"""
    <div class='it-stat-row'>
        <div class='it-stat-card'>
            <div class='it-stat-value' style='color:#FFB200;'>{s['total']}</div>
            <div class='it-stat-label'>Total Issues</div>
        </div>
        <div class='it-stat-card'>
            <div class='it-stat-value' style='color:{open_color};'>{s['open']}</div>
            <div class='it-stat-label'>Open</div>
        </div>
        <div class='it-stat-card'>
            <div class='it-stat-value' style='color:{critical_color};'>{s['critical']}</div>
            <div class='it-stat-label'>Critical</div>
        </div>
        <div class='it-stat-card'>
            <div class='it-stat-value' style='color:{resolved_color};'>{s['resolved']}</div>
            <div class='it-stat-label'>Resolved</div>
        </div>
        <div class='it-stat-card'>
            <div class='it-stat-value' style='color:#00D4FF; font-size:1rem;
            padding-top:6px;'>{s['top_disc'].split('—')[-1].strip()}</div>
            <div class='it-stat-label'>Top Discipline</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_issue_list(filter_status=None, filter_priority=None,
                      filter_discipline=None, search_query=""):
    issues = st.session_state.issues

    # Filter
    if filter_status and filter_status != "All":
        issues = [i for i in issues if i["status"] == filter_status]
    if filter_priority and filter_priority != "All":
        issues = [i for i in issues if i["priority"] == filter_priority]
    if filter_discipline and filter_discipline != "All":
        issues = [i for i in issues if i["discipline"] == filter_discipline]
    if search_query:
        q = search_query.lower()
        issues = [i for i in issues if
                  q in i["title"].lower() or
                  q in i["description"].lower() or
                  q in i["id"].lower()]

    # Sort — Critical first, then by created date
    priority_order = {p: idx for idx, p in enumerate(PRIORITIES)}
    issues = sorted(issues, key=lambda x: priority_order.get(x["priority"], 99))

    if not issues:
        st.markdown("""
        <div class='it-empty'>
            <div class='it-empty-icon'>◈</div>
            <div class='it-empty-title'>No issues match your filter</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for issue in issues:
        selected = st.session_state.selected_issue_id == issue["id"]
        card_class = "it-issue-card selected" if selected else "it-issue-card"

        st.markdown(f"""
        <div class='{card_class}'>
            <div style='display:flex; justify-content:space-between;
            align-items:flex-start; flex-wrap:wrap; gap:6px;'>
                <div>
                    <div class='it-issue-id'>#{issue['id']}</div>
                    <div class='it-issue-title'>{issue['title']}</div>
                    <div class='it-issue-meta' style='margin-top:4px;'>
                        {issue['discipline']} &nbsp;·&nbsp;
                        Assigned: {issue['assigned_to'] or '—'} &nbsp;·&nbsp;
                        {issue['created_at']}
                    </div>
                </div>
                <div style='display:flex; gap:4px; flex-wrap:wrap; align-items:center;'>
                    {priority_tag(issue['priority'])}
                    {status_tag(issue['status'])}
                    {source_tag(issue['source'])}
                </div>
            </div>
            <div style='font-family:Space Grotesk,sans-serif;
            font-size:0.78rem; color:#1E3A5F; margin-top:8px;'>
                {issue['description'][:120]}{'...' if len(issue['description']) > 120 else ''}
            </div>
            <div style='font-family:JetBrains Mono,monospace;
            font-size:0.6rem; color:#0E1E30; margin-top:6px;'>
                {len(issue['comments'])} comment{'s' if len(issue['comments']) != 1 else ''}
                &nbsp;·&nbsp;
                {len(issue['attachments'])} attachment{'s' if len(issue['attachments']) != 1 else ''}
                &nbsp;·&nbsp; Updated {issue['updated_at']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_open, col_del = st.columns([3, 1])
        with col_open:
            if st.button(f"Open Issue #{issue['id']}",
                         key=f"open_{issue['id']}"):
                st.session_state.selected_issue_id = issue["id"]
                st.session_state.tracker_view = "detail"
                st.rerun()
        with col_del:
            if st.button(f"Delete", key=f"del_{issue['id']}"):
                delete_issue(issue["id"])
                st.rerun()


def render_issue_detail(issue_id):
    issue = next(
        (i for i in st.session_state.issues if i["id"] == issue_id), None)
    if not issue:
        st.error("Issue not found.")
        return

    if st.button("← Back to Issue List"):
        st.session_state.tracker_view = "list"
        st.session_state.selected_issue_id = None
        st.rerun()

    st.markdown(f"""
    <div class='it-detail-box'>
        <div style='display:flex; justify-content:space-between;
        align-items:flex-start; flex-wrap:wrap; gap:8px;'>
            <div>
                <div class='it-issue-id' style='font-size:0.72rem;'>
                    ISSUE #{issue['id']}
                    &nbsp;·&nbsp; Source: {issue['source']}
                    {f"&nbsp;·&nbsp; Clash Ref: {issue['clash_ref']}"
                     if issue['clash_ref'] else ''}
                </div>
                <div class='it-issue-title' style='font-size:1.3rem;
                margin-top:6px;'>{issue['title']}</div>
            </div>
            <div>
                {priority_tag(issue['priority'])}
                {status_tag(issue['status'])}
            </div>
        </div>
        <div style='font-family:Space Grotesk,sans-serif;
        font-size:0.87rem; color:#4A6A8A; margin-top:12px;
        line-height:1.6;'>{issue['description']}</div>
        <div style='font-family:JetBrains Mono,monospace;
        font-size:0.62rem; color:#1E3A5F; margin-top:12px;'>
            Discipline: {issue['discipline']}
            &nbsp;·&nbsp; Assigned to: {issue['assigned_to'] or 'Unassigned'}
            &nbsp;·&nbsp; Created: {issue['created_at']}
            &nbsp;·&nbsp; Updated: {issue['updated_at']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Edit panel ────────────────────────────────────────────────────────
    with st.expander("✏️ Edit Issue"):
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            new_status = st.selectbox(
                "Status", STATUSES,
                index=STATUSES.index(issue["status"]),
                key=f"edit_status_{issue_id}"
            )
            new_priority = st.selectbox(
                "Priority", PRIORITIES,
                index=PRIORITIES.index(issue["priority"]),
                key=f"edit_priority_{issue_id}"
            )
        with e_col2:
            new_assigned = st.text_input(
                "Assigned To",
                value=issue["assigned_to"],
                key=f"edit_assigned_{issue_id}"
            )
            new_discipline = st.selectbox(
                "Discipline", DISCIPLINES,
                index=DISCIPLINES.index(issue["discipline"])
                if issue["discipline"] in DISCIPLINES else 0,
                key=f"edit_disc_{issue_id}"
            )
        new_title = st.text_input(
            "Title", value=issue["title"],
            key=f"edit_title_{issue_id}"
        )
        new_desc = st.text_area(
            "Description", value=issue["description"],
            key=f"edit_desc_{issue_id}", height=80
        )
        if st.button("💾 Save Changes", key=f"save_{issue_id}"):
            update_issue(
                issue_id,
                status=new_status,
                priority=new_priority,
                assigned_to=new_assigned,
                discipline=new_discipline,
                title=new_title,
                description=new_desc
            )
            st.success("Issue updated.")
            st.rerun()

    # ── Comments ──────────────────────────────────────────────────────────
    st.markdown("<div class='it-section-label'>Comments</div>",
                unsafe_allow_html=True)

    if issue["comments"]:
        for comment in issue["comments"]:
            st.markdown(f"""
            <div class='it-comment-card'>
                <span class='it-comment-author'>{comment['author']}</span>
                <span class='it-comment-time'>{comment['timestamp']}</span>
                <div class='it-comment-text'>{comment['text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='font-family:Space Grotesk,sans-serif;
        font-size:0.8rem; color:#1E3A5F; padding:8px 0;'>
        No comments yet.</div>
        """, unsafe_allow_html=True)

    c_col1, c_col2 = st.columns([1, 3])
    with c_col1:
        comment_author = st.text_input(
            "Your Name", placeholder="e.g. Devendra",
            key=f"c_author_{issue_id}"
        )
    with c_col2:
        comment_text = st.text_area(
            "Comment", placeholder="Add a comment...",
            key=f"c_text_{issue_id}", height=68
        )
    if st.button("💬 Add Comment", key=f"c_btn_{issue_id}"):
        if comment_author.strip() and comment_text.strip():
            add_comment(issue_id, comment_author.strip(),
                        comment_text.strip())
            st.success("Comment added.")
            st.rerun()
        else:
            st.warning("Enter your name and a comment.")

    # ── Attachments ───────────────────────────────────────────────────────
    st.markdown("<div class='it-section-label'>Attachments</div>",
                unsafe_allow_html=True)

    if issue["attachments"]:
        for att in issue["attachments"]:
            st.markdown(f"""
            <div class='it-attach-item'>
                📎 {att['filename']} &nbsp;·&nbsp; {att['size_kb']} KB
                &nbsp;·&nbsp; {att['uploaded']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='font-family:Space Grotesk,sans-serif;
        font-size:0.8rem; color:#1E3A5F; padding:4px 0;'>
        No attachments yet.</div>
        """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Attach a file (image, PDF, DWG, IFC...)",
        key=f"att_{issue_id}",
        label_visibility="visible"
    )
    if uploaded_file:
        add_attachment(issue_id, uploaded_file.name,
                       uploaded_file.getvalue())
        st.success(f"✓ {uploaded_file.name} attached.")
        st.rerun()

    # ── Close / Resolve quick actions ─────────────────────────────────────
    st.markdown("<hr class='it-divider'>", unsafe_allow_html=True)
    qa_col1, qa_col2, qa_col3 = st.columns(3)
    with qa_col1:
        if st.button("✅ Mark Resolved", key=f"resolve_{issue_id}"):
            update_issue(issue_id, status="Resolved")
            st.success("Marked as Resolved.")
            st.rerun()
    with qa_col2:
        if st.button("🔄 Mark In Progress", key=f"inprog_{issue_id}"):
            update_issue(issue_id, status="In Progress")
            st.rerun()
    with qa_col3:
        if st.button("🔒 Close Issue", key=f"close_{issue_id}"):
            update_issue(issue_id, status="Closed")
            st.rerun()


def render_new_issue_form():
    st.markdown("<div class='it-section-label'>New Issue</div>",
                unsafe_allow_html=True)
    with st.form("new_issue_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            title = st.text_input("Issue Title *",
                placeholder="e.g. MEP duct clashes with structural beam at GL-C/3")
            discipline = st.selectbox("Discipline", DISCIPLINES)
            priority = st.selectbox("Priority", PRIORITIES)
        with f_col2:
            assigned_to = st.text_input("Assign To",
                placeholder="e.g. MEP Coordinator")
            description = st.text_area("Description",
                placeholder="Describe the issue, location, and impact...",
                height=108)
        submitted = st.form_submit_button("➕ Create Issue")
        if submitted:
            if title.strip():
                issue = create_issue(
                    title=title.strip(),
                    description=description.strip(),
                    discipline=discipline,
                    priority=priority,
                    assigned_to=assigned_to.strip()
                )
                st.session_state.issues.append(issue)
                st.success(f"✓ Issue #{issue['id']} created.")
                st.rerun()
            else:
                st.warning("Issue title is required.")


def render_clash_import():
    st.markdown("<div class='it-section-label'>Import from Clash CSV</div>",
                unsafe_allow_html=True)
    st.markdown("""
    <div style='font-family:Space Grotesk,sans-serif;
    font-size:0.8rem; color:#2A4A6A; margin-bottom:10px;'>
    Export your Navisworks Clash Detective report as CSV and upload here.
    Each clash row becomes an issue automatically.
    </div>
    """, unsafe_allow_html=True)

    clash_file = st.file_uploader(
        "Navisworks Clash CSV",
        type=["csv"],
        key="tracker_clash_import",
        label_visibility="collapsed"
    )
    if clash_file:
        df = pd.read_csv(clash_file)
        st.markdown(f"""
        <div style='font-family:JetBrains Mono,monospace;
        font-size:0.68rem; color:#00D4FF; padding:6px 0;'>
        Detected {len(df)} rows · Columns: {', '.join(df.columns[:6])}
        {'...' if len(df.columns) > 6 else ''}
        </div>
        """, unsafe_allow_html=True)
        with st.expander("Preview"):
            st.dataframe(df.head(5), use_container_width=True)
        if st.button("⚡ Import All as Issues"):
            count = import_from_clash_csv(df)
            st.success(f"✓ {count} issues imported from clash report.")
            st.rerun()


# ── Main entry point ──────────────────────────────────────────────────────────

def show_issue_tracker():
    init_tracker_state()
    st.markdown(TRACKER_CSS, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class='it-header'>
        <div style='margin-bottom:10px;'>
            <span class='it-badge'>NEW</span>
            <span class='it-badge'>v1.0</span>
        </div>
        <div class='it-title'>BIM <span>Issue</span> Tracker</div>
        <div class='it-sub'>
            Log, assign, comment, and resolve BIM coordination issues —
            manual or imported directly from your Navisworks clash report.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # If in detail view, show detail and return
    if st.session_state.tracker_view == "detail" and \
            st.session_state.selected_issue_id:
        render_issue_detail(st.session_state.selected_issue_id)
        return

    # Stats row
    render_stats()

    # Top action bar
    top_col1, top_col2, top_col3 = st.columns([2, 2, 1])
    with top_col1:
        search = st.text_input(
            "Search", placeholder="Search by title, ID, or description...",
            label_visibility="collapsed"
        )
    with top_col2:
        view_mode = st.radio(
            "View", ["📋 Issue List", "➕ New Issue", "📥 Import from Clash"],
            horizontal=True, label_visibility="collapsed"
        )
    with top_col3:
        if st.session_state.issues:
            st.download_button(
                label="⬇️ Export JSON",
                data=export_issues_json(),
                file_name=f"NexBIM_Issues_"
                          f"{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )

    st.markdown("<hr class='it-divider'>", unsafe_allow_html=True)

    if view_mode == "➕ New Issue":
        render_new_issue_form()

    elif view_mode == "📥 Import from Clash":
        render_clash_import()

    else:
        # Filter bar
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            filter_status = st.selectbox(
                "Status", ["All"] + STATUSES,
                label_visibility="visible"
            )
        with f_col2:
            filter_priority = st.selectbox(
                "Priority", ["All"] + PRIORITIES,
                label_visibility="visible"
            )
        with f_col3:
            filter_discipline = st.selectbox(
                "Discipline", ["All"] + DISCIPLINES,
                label_visibility="visible"
            )

        if not st.session_state.issues:
            st.markdown("""
            <div class='it-empty'>
                <div class='it-empty-icon'>◈</div>
                <div class='it-empty-title'>No issues yet</div>
                <div style='font-family:Space Grotesk,sans-serif;
                font-size:0.83rem; color:#162840; line-height:2;'>
                    Create your first issue manually<br>
                    or import from a Navisworks clash report
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            render_issue_list(
                filter_status=filter_status,
                filter_priority=filter_priority,
                filter_discipline=filter_discipline,
                search_query=search
            )

    # Footer
    st.markdown("""
    <div style='text-align:center; font-family:JetBrains Mono,monospace;
    font-size:0.6rem; letter-spacing:1px; color:#0E1E30;
    margin-top:30px; padding-top:14px;
    border-top:1px solid rgba(255,255,255,0.03);'>
        NEXBIM ISSUE TRACKER v1.0 · DEVENDRA GUPTA · BIM + AI + AUTOMATION
    </div>
    """, unsafe_allow_html=True)
