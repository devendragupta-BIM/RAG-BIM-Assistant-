from groq import Groq
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, Table, TableStyle, KeepTogether, PageBreak)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib import colors
import streamlit as st
import base64
import io
import os
import zipfile
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Color Palette
C_ACCENT = HexColor("#00FFB2")
C_ACCENT2 = HexColor("#00D4FF")
C_DARK = HexColor("#050D1A")
C_MID = HexColor("#0A1628")
C_HEADING = HexColor("#0D2137")
C_TEXT = HexColor("#1A2A3A")
C_SUBTEXT = HexColor("#4A6A8A")
C_LIGHT = HexColor("#A0B4C8")
C_WHITE = HexColor("#FFFFFF")
C_ROW1 = HexColor("#F0F7FF")
C_ROW2 = HexColor("#FFFFFF")
C_TABLE_HEADER = HexColor("#0A1628")

def get_styles():
    styles = getSampleStyleSheet()
    return {
        "doc_title": ParagraphStyle(
            "doc_title",
            parent=styles["Normal"],
            fontSize=28,
            fontName="Helvetica-Bold",
            textColor=C_ACCENT,
            spaceAfter=4,
            spaceBefore=0,
            leading=32
        ),
        "doc_subtitle": ParagraphStyle(
            "doc_subtitle",
            parent=styles["Normal"],
            fontSize=11,
            fontName="Helvetica",
            textColor=C_LIGHT,
            spaceAfter=4,
            leading=16
        ),
        "doc_meta": ParagraphStyle(
            "doc_meta",
            parent=styles["Normal"],
            fontSize=8,
            fontName="Helvetica",
            textColor=C_SUBTEXT,
            spaceAfter=0,
            leading=12
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=styles["Normal"],
            fontSize=14,
            fontName="Helvetica-Bold",
            textColor=C_ACCENT,
            spaceAfter=8,
            spaceBefore=20,
            leading=18,
            borderPad=4
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=styles["Normal"],
            fontSize=12,
            fontName="Helvetica-Bold",
            textColor=C_TEXT,
            spaceAfter=6,
            spaceBefore=14,
            leading=16
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=styles["Normal"],
            fontSize=11,
            fontName="Helvetica-Bold",
            textColor=C_SUBTEXT,
            spaceAfter=4,
            spaceBefore=10,
            leading=14
        ),
        "body": ParagraphStyle(
            "body",
            parent=styles["Normal"],
            fontSize=10,
            fontName="Helvetica",
            textColor=C_TEXT,
            spaceAfter=6,
            spaceBefore=2,
            leading=16,
            alignment=TA_JUSTIFY
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=styles["Normal"],
            fontSize=10,
            fontName="Helvetica",
            textColor=C_TEXT,
            spaceAfter=4,
            spaceBefore=2,
            leading=15,
            leftIndent=20,
            firstLineIndent=0
        ),
        "sub_bullet": ParagraphStyle(
            "sub_bullet",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica",
            textColor=C_SUBTEXT,
            spaceAfter=3,
            leading=14,
            leftIndent=40
        ),
        "table_header": ParagraphStyle(
            "table_header",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=C_WHITE,
            alignment=TA_CENTER,
            leading=12
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica",
            textColor=C_TEXT,
            alignment=TA_LEFT,
            leading=12
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=styles["Normal"],
            fontSize=8,
            fontName="Helvetica",
            textColor=C_SUBTEXT,
            alignment=TA_CENTER,
            leading=10
        ),
        "page_label": ParagraphStyle(
            "page_label",
            parent=styles["Normal"],
            fontSize=7,
            fontName="Helvetica",
            textColor=C_SUBTEXT,
            alignment=TA_RIGHT,
            leading=10
        ),
        "callout": ParagraphStyle(
            "callout",
            parent=styles["Normal"],
            fontSize=10,
            fontName="Helvetica-Oblique",
            textColor=C_ACCENT,
            spaceAfter=6,
            spaceBefore=6,
            leading=15,
            leftIndent=16,
            rightIndent=16
        ),
    }

def make_cover_block(story, styles, doc_type, project_info, doc_num, total_docs):
    cover_data = [[
        Paragraph(f"<font color='#00FFB2'><b>NexBIM</b></font>", styles["doc_title"]),
    ]]
    cover_table = Table(cover_data, colWidths=[7*inch])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_MID),
        ('TOPPADDING', (0,0), (-1,-1), 24),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 24),
        ('RIGHTPADDING', (0,0), (-1,-1), 24),
        ('ROUNDEDCORNERS', [8]),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 6))

    info_data = [[
        Paragraph(doc_type, styles["doc_subtitle"]),
        Paragraph(
            f"<font color='#4A6A8A'>Document {doc_num} of {total_docs}</font>",
            styles["page_label"]
        )
    ]]
    info_table = Table(info_data, colWidths=[4.5*inch, 2.5*inch])
    story.append(info_table)
    story.append(Spacer(1, 4))

    meta_items = [
        ["Project", project_info['name']],
        ["Client", project_info['client']],
        ["Location", project_info['location']],
        ["Building Type", project_info['type']],
        ["Generated", datetime.now().strftime('%B %d, %Y at %I:%M %p')],
        ["Prepared by", "NexBIM AI Platform v3.0"],
    ]
    meta_data = [[
        Paragraph(f"<font color='#4A6A8A'>{k}</font>", styles["doc_meta"]),
        Paragraph(f"<b>{v}</b>", styles["doc_meta"])
    ] for k, v in meta_items]

    meta_table = Table(meta_data, colWidths=[1.2*inch, 5.8*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor("#F8FBFF")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('LINEBELOW', (0,0), (-1,-2),
            0.3, HexColor("#E0EAF4")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 16))
    story.append(HRFlowable(
        width="100%", thickness=2,
        color=C_ACCENT, spaceAfter=16, spaceBefore=0
    ))

def make_footer_block(story, styles, doc_type, project_info):
    story.append(Spacer(1, 20))
    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=C_ACCENT, spaceAfter=8
    ))
    footer_data = [[
        Paragraph(
            f"NexBIM v3.0 · {doc_type}",
            styles["footer"]
        ),
        Paragraph(
            f"Project: {project_info['name']} · Built by Devendra Gupta",
            styles["footer"]
        )
    ]]
    footer_table = Table(footer_data, colWidths=[3.5*inch, 3.5*inch])
    story.append(footer_table)

def parse_content(story, styles, content):
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == "":
            story.append(Spacer(1, 4))
            i += 1
            continue

        if line.startswith("#### "):
            story.append(Paragraph(line[5:], styles["h3"]))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], styles["h3"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["h2"]))
        elif line.startswith("# "):
            story.append(Paragraph(line[2:], styles["h1"]))
        elif line.startswith("**") and line.endswith("**") and len(line) > 4:
            clean = line[2:-2].strip()
            if clean:
                story.append(Paragraph(clean, styles["h2"]))
        elif line.startswith("- ") or line.startswith("* "):
            text = line[2:].strip()
            text = text.replace("**", "").replace("*", "")
            story.append(Paragraph(f"• &nbsp; {text}", styles["bullet"]))
        elif line.startswith("  - ") or line.startswith("  * "):
            text = line[4:].strip()
            story.append(Paragraph(f"◦ &nbsp; {text}", styles["sub_bullet"]))
        elif len(line) > 2 and line[0].isdigit() and line[1] in ".)" :
            text = line[2:].strip().replace("**", "").replace("*", "")
            story.append(Paragraph(
                f"<b>{line[0]}.</b> &nbsp; {text}", styles["bullet"]))
        elif line.startswith("> "):
            story.append(Paragraph(line[2:], styles["callout"]))
        elif line.startswith("---") or line.startswith("==="):
            story.append(HRFlowable(
                width="100%", thickness=0.5,
                color=HexColor("#E0EAF4"),
                spaceAfter=6, spaceBefore=6
            ))
        else:
            clean = line.replace("**", "").replace("*", "")
            if clean:
                story.append(Paragraph(clean, styles["body"]))
        i += 1

def build_pdf(cover_func, content, project_info):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.85*inch,
        leftMargin=0.85*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
        title=f"NexBIM — {project_info['name']}",
        author="NexBIM v3.0 by Devendra Gupta"
    )
    styles = get_styles()
    story = []
    cover_func(story, styles)
    parse_content(story, styles, content)
    make_footer_block(story, styles,
        cover_func.__name__.replace("_cover", "").replace("_", " ").title(),
        project_info)
    doc.build(story)
    buffer.seek(0)
    return buffer

def analyze_floor_plan(image_base64, project_info, client):
    prompt = f"""You are an expert BIM consultant and architectural analyst.
Analyze this architectural floor plan image carefully and extract all details.

Project Information:
- Project Name: {project_info['name']}
- Location: {project_info['location']}
- Building Type: {project_info['type']}
- Client: {project_info['client']}

Provide a comprehensive technical analysis covering:
1. All rooms and spaces with approximate dimensions and areas
2. Doors count and types
3. Windows count and types
4. Approximate total built up area in square feet and square meters
5. Number of floors visible
6. Structural elements visible
7. MEP elements visible
8. Special architectural features
9. Overall building description
10. Estimated scale

Be as detailed and specific as possible."""

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }}
            ]
        }],
        max_tokens=2000
    )
    return response.choices[0].message.content

def generate_bep(analysis, project_info, client):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"""You are a senior BIM Manager
with 15 years of experience. Write a complete professional BIM Execution Plan
following ISO 19650 standards.

Project: {project_info['name']}
Location: {project_info['location']}
Type: {project_info['type']}
Client: {project_info['client']}

Floor Plan Analysis:
{analysis}

Write the complete BEP with proper markdown headings (## for sections):

## 1. Project Overview and BIM Vision
## 2. BIM Goals and Objectives
## 3. BIM Uses and Applications
## 4. Software and Hardware Requirements
## 5. Project Team Roles and Responsibilities
## 6. Naming Conventions and File Structure
## 7. Common Data Environment Setup
## 8. Coordinate System and Units
## 9. Model Breakdown Structure
## 10. Quality Control Procedures
## 11. Clash Detection Protocol
## 12. Deliverables Schedule
## 13. Communication Protocol

Write each section with detailed bullet points and paragraphs.
Use professional BIM terminology. Make it client-ready."""}],
        max_tokens=3000
    )
    return response.choices[0].message.content

def generate_lod_spec(analysis, project_info, client):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"""You are a BIM specialist
expert in LOD Specifications following BIMForum LOD Spec 2025.

Create a complete LOD Specification for all building elements.

Project: {project_info['name']} - {project_info['type']}

Floor Plan Analysis:
{analysis}

Use proper markdown headings (## for categories, ### for elements):

## Architectural Elements
### Walls
### Floors
### Ceilings
### Roofs
### Doors
### Windows
### Stairs

## Structural Elements
### Columns
### Beams
### Slabs
### Foundations

## MEP Elements
### Mechanical Ductwork
### Plumbing Pipes
### Electrical Conduits
### Equipment

For each element provide LOD 100 through LOD 500 requirements
with geometry and information requirements as bullet points."""}],
        max_tokens=3000
    )
    return response.choices[0].message.content

def generate_clash_rules(analysis, project_info, client):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"""You are a BIM Coordination
expert specializing in Navisworks clash detection.

Create a complete Clash Detection Rules document.

Project: {project_info['name']} - {project_info['type']}

Floor Plan Analysis:
{analysis}

Use proper markdown headings:

## Hard Clash Tests
## Soft Clash Tests
## Workflow Clash Tests
## Clash Review Process
## Clash Status Definitions
## Resolution Procedures

For each clash test use bullet points with:
- Test name
- Selection A and B
- Tolerance in mm
- Priority level
- Responsible party
- Resolution time target

Make it ready to implement directly in Navisworks."""}],
        max_tokens=3000
    )
    return response.choices[0].message.content

def generate_cost_estimate(analysis, project_info, client):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"""You are a senior quantity
surveyor with expertise in Indian construction costs.

Create a detailed preliminary cost estimate in Indian Rupees.

Project: {project_info['name']}
Location: {project_info['location']}
Type: {project_info['type']}

Floor Plan Analysis:
{analysis}

Use proper markdown headings for each category:

## 1. Preliminary and General Works
## 2. Civil and Structural Works
## 3. Architectural Finishes
## 4. Electrical Works
## 5. Plumbing and Sanitary
## 6. HVAC and Mechanical
## 7. External Development
## 8. Cost Summary

For each category list items as:
- Item description | Unit | Qty | Rate INR | Amount INR

End with:
## Grand Total Summary
Including subtotals, contingency 5%, GST 18%, grand total,
cost per sqft and cost per sqm."""}],
        max_tokens=3000
    )
    return response.choices[0].message.content

def generate_health_checklist(analysis, project_info, client):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"""You are a BIM Quality
Manager with deep ISO 19650 expertise.

Create a comprehensive 50-point BIM Project Health Checklist.

Project: {project_info['name']} - {project_info['type']}

Floor Plan Analysis:
{analysis}

Use proper markdown headings:

## Category 1: Project Setup and BIM Environment (10 items)
## Category 2: Model Quality and Standards (10 items)
## Category 3: LOD Compliance and Information (10 items)
## Category 4: Coordination and Clash Management (10 items)
## Category 5: Handover and Closeout Readiness (10 items)

For each checkpoint use this format as bullet points:
- **CP-XX: Checkpoint Title** — Description of what to check,
  how to verify, responsible party, and milestone."""}],
        max_tokens=3000
    )
    return response.choices[0].message.content

def show_generator():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

    .nex-gen-hero {
        position: relative;
        background: linear-gradient(135deg, #050D1A 0%, #0A1628 50%, #0D1F35 100%);
        border: 1px solid rgba(0, 255, 178, 0.3);
        border-radius: 24px;
        padding: 40px;
        margin-bottom: 32px;
        overflow: hidden;
    }
    .nex-gen-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle,
            rgba(0, 255, 178, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .nex-badge {
        display: inline-block;
        background: rgba(0, 255, 178, 0.1);
        border: 1px solid rgba(0, 255, 178, 0.4);
        color: #00FFB2;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 3px;
        padding: 4px 12px;
        border-radius: 4px;
        margin-bottom: 16px;
        text-transform: uppercase;
    }
    .nex-gen-title {
        font-family: 'Syne', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1.1;
        margin: 0 0 8px 0;
        letter-spacing: -1px;
    }
    .nex-gen-title span { color: #00FFB2; }
    .nex-gen-subtitle {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1rem;
        color: #6B8FAF;
        margin: 0;
        line-height: 1.6;
        max-width: 600px;
    }
    .nex-docs-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin: 28px 0 0 0;
    }
    .nex-doc-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px;
        padding: 16px 12px;
        text-align: center;
    }
    .nex-doc-icon { font-size: 1.5rem; margin-bottom: 8px; }
    .nex-doc-name {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        color: #A0B4C8;
        line-height: 1.3;
    }
    .nex-section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 3px;
        color: #00FFB2;
        text-transform: uppercase;
        margin: 24px 0 12px 0;
    }
    .nex-upload-zone {
        background: rgba(0, 255, 178, 0.03);
        border: 2px dashed rgba(0, 255, 178, 0.2);
        border-radius: 16px;
        padding: 32px 20px;
        text-align: center;
        margin: 8px 0 16px 0;
    }
    .nex-upload-icon { font-size: 2.5rem; margin-bottom: 10px; }
    .nex-upload-text {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.95rem;
        color: #4A6A8A;
        line-height: 1.6;
    }
    .nex-progress-step {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: rgba(0, 255, 178, 0.04);
        border-left: 3px solid #00FFB2;
        border-radius: 0 10px 10px 0;
        margin-bottom: 8px;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.9rem;
        color: #E0F0FF;
        animation: fadeIn 0.3s ease;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-10px); }
        to { opacity: 1; transform: translateX(0); }
    }
    .nex-result-card {
        background: linear-gradient(135deg,
            rgba(0, 255, 178, 0.04) 0%,
            rgba(0, 150, 255, 0.02) 100%);
        border: 1px solid rgba(0, 255, 178, 0.2);
        border-radius: 20px;
        padding: 28px 32px;
        margin: 20px 0;
    }
    .nex-result-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: #00FFB2;
        margin-bottom: 20px;
        letter-spacing: -0.3px;
    }
    .nex-doc-list-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.9rem;
        color: #A0B4C8;
    }
    .nex-doc-list-item:last-child { border-bottom: none; }
    .nex-doc-check {
        width: 24px;
        height: 24px;
        background: rgba(0, 255, 178, 0.1);
        border: 1px solid rgba(0, 255, 178, 0.3);
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #00FFB2;
        font-size: 0.8rem;
        flex-shrink: 0;
    }
    .stTextInput input {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #E0F0FF !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='nex-gen-hero'>
        <div class='nex-badge'>⚡ World First · NexBIM Generator v3.0</div>
        <div class='nex-gen-title'>
            Floor Plan <span>→</span><br>Complete BIM Package
        </div>
        <p class='nex-gen-subtitle'>
            Upload any architectural floor plan. Get a complete professional
            BIM package in under 60 seconds. No manual work required.
        </p>
        <div class='nex-docs-grid'>
            <div class='nex-doc-card'>
                <div class='nex-doc-icon'>📋</div>
                <div class='nex-doc-name'>BIM Execution Plan</div>
            </div>
            <div class='nex-doc-card'>
                <div class='nex-doc-icon'>📊</div>
                <div class='nex-doc-name'>LOD Specification</div>
            </div>
            <div class='nex-doc-card'>
                <div class='nex-doc-icon'>⚠️</div>
                <div class='nex-doc-name'>Clash Detection Rules</div>
            </div>
            <div class='nex-doc-card'>
                <div class='nex-doc-icon'>💰</div>
                <div class='nex-doc-name'>Cost Estimate INR</div>
            </div>
            <div class='nex-doc-card'>
                <div class='nex-doc-icon'>✅</div>
                <div class='nex-doc-name'>BIM Health Checklist</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='nex-section-label'>01 — Project Details</div>",
        unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project Name",
            placeholder="e.g. Sunrise Residential Complex",
            key="gen_name")
        project_location = st.text_input("Location",
            placeholder="e.g. Mumbai, Maharashtra",
            key="gen_location")
    with col2:
        project_type = st.selectbox("Building Type", [
            "Residential — Single Family House",
            "Residential — Multi Family Apartment",
            "Commercial — Office Building",
            "Commercial — Retail Mall",
            "Industrial — Warehouse",
            "Healthcare — Hospital",
            "Educational — School or College",
            "Hospitality — Hotel",
            "Mixed Use Development"
        ], key="gen_type")
        project_client = st.text_input("Client Name",
            placeholder="e.g. ABC Developers Pvt Ltd",
            key="gen_client")

    st.markdown("<div class='nex-section-label'>02 — Floor Plan Image</div>",
        unsafe_allow_html=True)

    st.markdown("""
    <div class='nex-upload-zone'>
        <div class='nex-upload-icon'>📐</div>
        <div class='nex-upload-text'>
            Upload your 2D architectural floor plan<br>
            <span style='font-size:0.8rem; color:#2A4060;'>
            JPG or PNG · Any scale · Hand drawn or CAD export
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_image = st.file_uploader(
        "Upload Floor Plan",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
        key="gen_image"
    )

    if uploaded_image:
        col_img, col_space = st.columns([2, 1])
        with col_img:
            st.image(uploaded_image,
                caption="Floor Plan — Ready for AI Analysis",
                use_column_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    generate_clicked = st.button(
        "⚡  Generate Complete BIM Package  →",
        use_container_width=True,
        key="gen_button"
    )

    if generate_clicked:
        if not uploaded_image:
            st.error("Please upload a floor plan image.")
            return
        if not project_name:
            st.error("Please enter a project name.")
            return
        if not project_location:
            st.error("Please enter a project location.")
            return
        if not project_client:
            st.error("Please enter a client name.")
            return

        project_info = {
            "name": project_name,
            "location": project_location,
            "type": project_type,
            "client": project_client
        }

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        image_bytes = uploaded_image.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        st.markdown("<div class='nex-section-label'>03 — Generating Package</div>",
            unsafe_allow_html=True)

        progress = st.progress(0)
        status_box = st.empty()

        try:
            status_box.markdown("""
            <div class='nex-progress-step'>
            🔍 &nbsp; Analyzing floor plan with AI vision model...
            </div>""", unsafe_allow_html=True)
            progress.progress(10)
            analysis = analyze_floor_plan(image_base64, project_info, client)

            status_box.markdown("""
            <div class='nex-progress-step'>
            📋 &nbsp; Writing BIM Execution Plan (ISO 19650)...
            </div>""", unsafe_allow_html=True)
            progress.progress(25)
            bep = generate_bep(analysis, project_info, client)

            status_box.markdown("""
            <div class='nex-progress-step'>
            📊 &nbsp; Creating LOD Specification table...
            </div>""", unsafe_allow_html=True)
            progress.progress(42)
            lod = generate_lod_spec(analysis, project_info, client)

            status_box.markdown("""
            <div class='nex-progress-step'>
            ⚠️ &nbsp; Generating Navisworks clash detection rules...
            </div>""", unsafe_allow_html=True)
            progress.progress(58)
            clash = generate_clash_rules(analysis, project_info, client)

            status_box.markdown("""
            <div class='nex-progress-step'>
            💰 &nbsp; Calculating cost estimate in Indian Rupees...
            </div>""", unsafe_allow_html=True)
            progress.progress(74)
            cost = generate_cost_estimate(analysis, project_info, client)

            status_box.markdown("""
            <div class='nex-progress-step'>
            ✅ &nbsp; Building 50-point BIM health checklist...
            </div>""", unsafe_allow_html=True)
            progress.progress(88)
            checklist = generate_health_checklist(analysis, project_info, client)

            status_box.markdown("""
            <div class='nex-progress-step'>
            📦 &nbsp; Creating perfectly formatted PDF documents...
            </div>""", unsafe_allow_html=True)
            progress.progress(95)

            def bep_cover(story, styles):
                make_cover_block(story, styles,
                    "BIM Execution Plan — ISO 19650 Compliant",
                    project_info, 1, 5)

            def lod_cover(story, styles):
                make_cover_block(story, styles,
                    "LOD Specification — BIMForum 2025 Standards",
                    project_info, 2, 5)

            def clash_cover(story, styles):
                make_cover_block(story, styles,
                    "Clash Detection Rules — Navisworks Ready",
                    project_info, 3, 5)

            def cost_cover(story, styles):
                make_cover_block(story, styles,
                    "Preliminary Cost Estimate — Indian Rupees",
                    project_info, 4, 5)

            def checklist_cover(story, styles):
                make_cover_block(story, styles,
                    "BIM Health Checklist — 50 Quality Checkpoints",
                    project_info, 5, 5)

            bep_pdf = build_pdf(bep_cover, bep, project_info)
            lod_pdf = build_pdf(lod_cover, lod, project_info)
            clash_pdf = build_pdf(clash_cover, clash, project_info)
            cost_pdf = build_pdf(cost_cover, cost, project_info)
            checklist_pdf = build_pdf(checklist_cover, checklist, project_info)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    f"01_{project_name}_BIM_Execution_Plan.pdf",
                    bep_pdf.read())
                zf.writestr(
                    f"02_{project_name}_LOD_Specification.pdf",
                    lod_pdf.read())
                zf.writestr(
                    f"03_{project_name}_Clash_Detection_Rules.pdf",
                    clash_pdf.read())
                zf.writestr(
                    f"04_{project_name}_Cost_Estimate_INR.pdf",
                    cost_pdf.read())
                zf.writestr(
                    f"05_{project_name}_BIM_Health_Checklist.pdf",
                    checklist_pdf.read())
            zip_buffer.seek(0)

            progress.progress(100)
            status_box.empty()

            st.markdown(f"""
            <div class='nex-result-card'>
                <div class='nex-result-title'>
                    ✦ &nbsp; Package Ready — {project_name}
                </div>
                <div class='nex-doc-list-item'>
                    <div class='nex-doc-check'>✓</div>
                    <div>
                        <b>BIM Execution Plan</b>
                        <span style='color:#4A6A8A; font-size:0.8rem;'>
                        &nbsp;·&nbsp; ISO 19650 Compliant · 13 Sections
                        </span>
                    </div>
                </div>
                <div class='nex-doc-list-item'>
                    <div class='nex-doc-check'>✓</div>
                    <div>
                        <b>LOD Specification</b>
                        <span style='color:#4A6A8A; font-size:0.8rem;'>
                        &nbsp;·&nbsp; BIMForum 2025 · LOD 100-500
                        </span>
                    </div>
                </div>
                <div class='nex-doc-list-item'>
                    <div class='nex-doc-check'>✓</div>
                    <div>
                        <b>Clash Detection Rules</b>
                        <span style='color:#4A6A8A; font-size:0.8rem;'>
                        &nbsp;·&nbsp; Navisworks Ready · All Disciplines
                        </span>
                    </div>
                </div>
                <div class='nex-doc-list-item'>
                    <div class='nex-doc-check'>✓</div>
                    <div>
                        <b>Cost Estimate</b>
                        <span style='color:#4A6A8A; font-size:0.8rem;'>
                        &nbsp;·&nbsp; Indian Rupees · With GST
                        </span>
                    </div>
                </div>
                <div class='nex-doc-list-item'>
                    <div class='nex-doc-check'>✓</div>
                    <div>
                        <b>BIM Health Checklist</b>
                        <span style='color:#4A6A8A; font-size:0.8rem;'>
                        &nbsp;·&nbsp; 50 Checkpoints · 5 Categories
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                label="📥  Download Complete BIM Package  →",
                data=zip_buffer,
                file_name=f"NexBIM_{project_name}_{timestamp}.zip",
                mime="application/zip",
                use_container_width=True
            )

            with st.expander("🔍 View Floor Plan Analysis"):
                st.markdown(f"""
                <div style='background:rgba(0,255,178,0.02);
                border:1px solid rgba(0,255,178,0.1);
                border-radius:12px; padding:20px;
                font-family: Space Grotesk, sans-serif;
                color:#6B8FAF; font-size:0.9rem; line-height:1.8;'>
                {analysis.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Generation failed: {str(e)}")
            st.info("Check your Groq API key in the .env file and try again.")