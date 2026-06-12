import streamlit as st
import os
from datetime import datetime
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return ChatGroq(api_key=os.getenv("GROQ_API_KEY"),
                    model_name="llama-3.3-70b-versatile")

SPEC_CATEGORIES = {
    "Architecture": [
        "Curtain Wall System", "Aluminium Windows and Doors", "Flush Doors",
        "Ceramic and Vitrified Tiles", "Marble and Granite Flooring",
        "Gypsum False Ceiling", "Grid False Ceiling", "External Plaster",
        "Internal Plaster", "Exterior Paint", "Interior Emulsion Paint",
        "Terrace Waterproofing", "Basement Waterproofing", "AAC Block Masonry",
        "Brick Masonry", "Raised Access Flooring", "Thermal Insulation",
    ],
    "Structure": [
        "RCC Work M20", "RCC Work M25", "RCC Work M30",
        "Fe500D TMT Reinforcement Steel", "Structural Steelwork",
        "Bored Cast-in-Situ Piles", "Precast Concrete Elements",
        "Post-Tensioned Slabs", "Shotcrete / Gunite",
        "Epoxy Grout for Equipment Bases",
    ],
    "MEP — Mechanical": [
        "HVAC Ductwork GI", "Air Handling Units", "Fan Coil Units",
        "VRF Air Conditioning System", "Chilled Water System",
        "Cooling Towers", "Ventilation Fans",
    ],
    "MEP — Plumbing": [
        "CPVC Hot and Cold Water Piping", "uPVC Soil and Waste Piping",
        "GI Fire Fighting Piping", "Sanitary Ware and CP Fittings",
        "Sewage Treatment Plant", "Water Storage Tanks",
        "Hydro-pneumatic Booster Systems",
    ],
    "MEP — Electrical": [
        "LT Cabling and Wiring", "HT Cabling", "Distribution Boards",
        "Diesel Generator Sets", "Dry Type Transformers",
        "Solar PV Systems", "LED Lighting Systems",
        "Fire Alarm and Detection System", "Public Address System",
        "CCTV and Access Control",
    ],
    "Civil": [
        "Earthwork Excavation", "Bituminous Road Works",
        "Cement Concrete Roads", "Compound Wall",
        "Stormwater Drainage", "Landscaping Works",
        "Interlocking Paver Blocks",
    ]
}

STANDARDS = {
    "Architecture": "NBC 2016, IS 1661, IS 2116, IS 3696, BIS standards",
    "Structure":    "IS 456, IS 13920, IS 2911, IS 800, IS 1786, CPWD specifications",
    "MEP — Mechanical": "NBC 2016 Part 8, ASHRAE, IS 655, ISHRAE guidelines",
    "MEP — Plumbing":   "NBC 2016 Part 9, IS 4985, IS 12235, CPHEEO manual",
    "MEP — Electrical": "NBC 2016 Part 8, IS 732, IE Rules 1956, CEA regulations",
    "Civil":            "MoRTH specifications, IRC codes, IS 456, CPWD DSR"
}

def write_specification(element, discipline, project_type, grade):
    llm = get_llm()
    standards = STANDARDS.get(discipline, "NBC 2016, relevant IS codes, CPWD specifications")
    prompt = f"""You are a senior specification writer with 20 years of Indian construction experience.
Write a complete, professional technical specification section for the following:

Element: {element}
Discipline: {discipline}
Project Type: {project_type}
Grade/Quality: {grade}
Applicable Standards: {standards}

Write the specification in standard CSI/CPWD format with these exact sections:

## SPECIFICATION SECTION
### {element.upper()}

---

**PART 1 — GENERAL**

1.1 SCOPE
[What this section covers]

1.2 RELATED SECTIONS
[List 3-4 related specification sections]

1.3 REFERENCES AND STANDARDS
[List all applicable IS codes, NBC clauses, BIS standards]

1.4 SUBMITTALS
[List required submittals: shop drawings, product data, samples, test reports]

1.5 QUALITY ASSURANCE
[Qualifications, experience requirements, mock-up requirements]

---

**PART 2 — PRODUCTS**

2.1 MATERIALS
[Detailed material specifications with grades, standards, properties]

2.2 MANUFACTURED PRODUCTS / EQUIPMENT
[Specific product requirements, performance specifications]

2.3 MIXES / SYSTEMS
[If applicable — mix design, system configuration]

---

**PART 3 — EXECUTION**

3.1 EXAMINATION
[Substrate conditions, pre-installation checks]

3.2 PREPARATION
[Surface preparation, priming, conditioning]

3.3 INSTALLATION / APPLICATION
[Step-by-step installation requirements, tolerances]

3.4 FIELD QUALITY CONTROL
[Testing requirements, acceptance criteria, frequency]

3.5 PROTECTION AND CLEANING
[Protection during construction, final cleaning]

---

**APPENDIX — KEY TECHNICAL PARAMETERS**
[Summary table of critical specifications in a readable format]

Be technically accurate for the Indian construction market.
Reference specific IS code clauses where relevant.
Use {grade} quality/grade throughout."""

    return llm.invoke(prompt).content

SPEC_CSS = """
<style>
.spec-header { background:linear-gradient(135deg,#070F1E,#0D1B2E); border:1px solid rgba(180,100,255,0.15); border-radius:18px; padding:26px 30px; margin-bottom:20px; }
.spec-title  { font-family:'DM Serif Display',serif; font-size:1.9rem; color:#FFF; }
.spec-title span { color:#B464FF; }
.spec-sub    { font-family:'DM Sans',sans-serif; font-size:0.87rem; color:#2A4A6A; }
.spec-badge  { display:inline-block; background:rgba(180,100,255,0.08); border:1px solid rgba(180,100,255,0.2); color:#B464FF; font-family:'Space Mono',monospace; font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:4px; margin-right:8px; margin-bottom:10px; }
.spec-divider{ border:none; border-top:1px solid rgba(255,255,255,0.04); margin:20px 0; }
</style>
"""

def show_specification_writer():
    st.markdown(SPEC_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class='spec-header'>
        <div><span class='spec-badge'>NEW</span><span class='spec-badge'>v1.0</span><span class='spec-badge'>NBC INDIA</span></div>
        <div class='spec-title'><span>Specification</span> Writer</div>
        <div class='spec-sub'>Select a building element and get a complete technical specification section in seconds. IS codes, NBC 2016, CPWD format. What used to take days now takes 30 seconds.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        discipline = st.selectbox("Discipline", list(SPEC_CATEGORIES.keys()))
        element    = st.selectbox("Element / System",
                                   SPEC_CATEGORIES[discipline])
        project_type = st.selectbox("Project Type", [
            "Residential", "Commercial Office", "Retail / Mall",
            "Hotel", "Industrial", "Institutional", "Mixed Use"
        ])
    with c2:
        grade = st.selectbox("Quality Grade", [
            "Standard — mid-market",
            "Premium — high-end residential / commercial",
            "Economy — affordable housing",
            "Luxury — five-star / premium"
        ])
        custom_element = st.text_input(
            "Or type a custom element",
            placeholder="e.g. Precast concrete facade panels"
        )
        st.markdown("""<div style='font-family:DM Sans,sans-serif;font-size:0.78rem;
        color:#2A4A6A;margin-top:8px;'>Custom element overrides dropdown selection.</div>""",
        unsafe_allow_html=True)

    final_element = custom_element.strip() if custom_element.strip() else element

    if st.button("📝 Write Specification Section"):
        with st.spinner(f"Writing specification for {final_element}..."):
            result = write_specification(
                final_element, discipline, project_type, grade)
            st.session_state["spec_result"]  = result
            st.session_state["spec_element"] = final_element

    if "spec_result" in st.session_state:
        st.markdown("<div class='spec-divider'></div>", unsafe_allow_html=True)
        st.markdown(st.session_state["spec_result"])
        c_a, c_b = st.columns(2)
        with c_a:
            st.download_button("⬇️ Download as TXT",
                data=st.session_state["spec_result"],
                file_name=f"NexBIM_Spec_{st.session_state.get('spec_element','').replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain", key="dl_spec_txt")
        with c_b:
            st.download_button("⬇️ Download as Markdown",
                data=st.session_state["spec_result"],
                file_name=f"NexBIM_Spec_{st.session_state.get('spec_element','').replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown", key="dl_spec_md")

    st.markdown("""<div style='text-align:center;font-family:Space Mono,monospace;font-size:0.6rem;
    color:#0E1E30;margin-top:24px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.03);'>
    NEXBIM SPECIFICATION WRITER v1.0 · DEVENDRA GUPTA · NBC 2016 · IS CODES · CPWD FORMAT</div>""",
    unsafe_allow_html=True)
