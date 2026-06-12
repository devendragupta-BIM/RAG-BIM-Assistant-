import streamlit as st
import os
from datetime import datetime
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return ChatGroq(api_key=os.getenv("GROQ_API_KEY"),
                    model_name="llama-3.3-70b-versatile")

def extract_minutes(transcript, meeting_type, project_name):
    llm = get_llm()
    prompt = f"""You are a senior BIM project manager extracting structured meeting minutes
from a coordination meeting transcript.

Project: {project_name}
Meeting Type: {meeting_type}
Date: {datetime.now().strftime('%B %d, %Y')}

Transcript:
{transcript}

Extract and structure the following:

## MEETING MINUTES
**Project:** {project_name}
**Meeting Type:** {meeting_type}
**Date:** {datetime.now().strftime('%B %d, %Y')}
**Prepared by:** NexBIM AI

---

### ATTENDEES
List all people mentioned in the transcript with their role/discipline.

### KEY DECISIONS MADE
List every decision made in the meeting. For each: decision, who made it, impact.

### ACTION REGISTER
Format as a table:
| # | Action Item | Responsible | Discipline | Deadline | Priority |
|---|-------------|-------------|------------|----------|----------|
[Extract every action item mentioned, assign discipline, set realistic deadline if mentioned]

### ISSUES RAISED
List every unresolved issue or concern raised. For each: issue, raised by, current status.

### CLASH / COORDINATION ITEMS
List all BIM coordination items, clash discussions, and model review comments.

### NEXT MEETING
Date and agenda items for next meeting if mentioned.

### SUMMARY
2-3 sentence executive summary of what was decided and what happens next.

Be thorough. Extract every action item even if implied. Assign disciplines accurately."""

    return llm.invoke(prompt).content

def push_to_issue_tracker(minutes_text):
    llm = get_llm()
    prompt = f"""From these meeting minutes, extract ONLY the action items as JSON array.
Each item must have: title, discipline, priority (Critical/High/Medium/Low), description.
Return ONLY valid JSON array, no other text, no markdown.

Minutes:
{minutes_text[:3000]}

JSON:"""
    try:
        import json
        response = llm.invoke(prompt).content.strip()
        response = response.replace("```json","").replace("```","").strip()
        items = json.loads(response)
        return items
    except Exception:
        return []

MTG_CSS = """
<style>
.mtg-header { background:linear-gradient(135deg,#070F1E,#0D1B2E); border:1px solid rgba(255,200,50,0.15); border-radius:18px; padding:26px 30px; margin-bottom:20px; }
.mtg-title  { font-family:'DM Serif Display',serif; font-size:1.9rem; color:#FFF; }
.mtg-title span { color:#FFC832; }
.mtg-sub    { font-family:'DM Sans',sans-serif; font-size:0.87rem; color:#2A4A6A; }
.mtg-badge  { display:inline-block; background:rgba(255,200,50,0.08); border:1px solid rgba(255,200,50,0.2); color:#FFC832; font-family:'Space Mono',monospace; font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:4px; margin-right:8px; margin-bottom:10px; }
.mtg-divider{ border:none; border-top:1px solid rgba(255,255,255,0.04); margin:20px 0; }
</style>
"""

def show_meeting_minutes():
    st.markdown(MTG_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class='mtg-header'>
        <div><span class='mtg-badge'>NEW</span><span class='mtg-badge'>v1.0</span></div>
        <div class='mtg-title'>Meeting <span>Minutes</span> Intelligence</div>
        <div class='mtg-sub'>Paste your meeting transcript or notes. Get structured minutes, action register, and issues list — and push action items directly into the Issue Tracker.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        project_name = st.text_input("Project Name",
            placeholder="e.g. Greenview Tower, Mumbai")
    with c2:
        meeting_type = st.selectbox("Meeting Type", [
            "BIM Coordination Meeting",
            "Design Review Meeting",
            "Site Progress Meeting",
            "Clash Review Meeting",
            "MEP Coordination Meeting",
            "Structural Review Meeting",
            "Client Review Meeting",
            "Value Engineering Workshop"
        ])

    transcript = st.text_area(
        "Paste meeting transcript or notes here",
        placeholder="""Example:
Attendees: Rahul (BIM Manager), Priya (MEP), Vikram (Structure)

Rahul: The duct at Grid C/3 is still clashing with the beam. Priya, can you reroute by Friday?
Priya: Yes, I'll drop the duct by 200mm and update the model.
Vikram: The column at Grid B/5 needs to move 150mm east. I'll update the structural model by Wednesday.
Rahul: We need to issue the coordination report to the client by next Tuesday...""",
        height=220
    )

    if st.button("⚡ Extract Meeting Minutes"):
        if transcript.strip():
            with st.spinner("Extracting structured minutes..."):
                result = extract_minutes(transcript, meeting_type,
                                          project_name or "Project")
                st.session_state["mtg_result"] = result
        else:
            st.warning("Paste your meeting transcript first.")

    if "mtg_result" in st.session_state:
        st.markdown("<div class='mtg-divider'></div>", unsafe_allow_html=True)
        st.markdown(st.session_state["mtg_result"])

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.download_button("⬇️ Download Minutes",
                data=st.session_state["mtg_result"],
                file_name=f"NexBIM_Minutes_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", key="dl_mtg")
        with col_b:
            if st.button("📋 Push Actions to Issue Tracker"):
                with st.spinner("Extracting action items..."):
                    items = push_to_issue_tracker(st.session_state["mtg_result"])
                    if items:
                        import uuid
                        for item in items:
                            issue = {
                                "id":          str(uuid.uuid4())[:8].upper(),
                                "title":       item.get("title", "Action from meeting")[:80],
                                "description": item.get("description", "Extracted from meeting minutes"),
                                "discipline":  item.get("discipline", "General"),
                                "priority":    item.get("priority", "Medium"),
                                "status":      "Open",
                                "assigned_to": "",
                                "source":      "Meeting Minutes",
                                "clash_ref":   "",
                                "created_at":  datetime.now().strftime("%d %b %Y, %I:%M %p"),
                                "updated_at":  datetime.now().strftime("%d %b %Y, %I:%M %p"),
                                "comments":    [],
                                "attachments": []
                            }
                            if "issues" not in st.session_state:
                                st.session_state.issues = []
                            st.session_state.issues.append(issue)
                        st.success(f"✓ {len(items)} action items pushed to Issue Tracker.")
                    else:
                        st.warning("Could not extract action items. Try again.")

    st.markdown("""<div style='text-align:center;font-family:Space Mono,monospace;font-size:0.6rem;
    color:#0E1E30;margin-top:24px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.03);'>
    NEXBIM MEETING MINUTES INTELLIGENCE v1.0 · DEVENDRA GUPTA</div>""", unsafe_allow_html=True)
