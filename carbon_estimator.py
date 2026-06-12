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

# Embodied carbon factors (kgCO2e per unit) — ICE Database v3 + Indian market data
CARBON_DB = {
    # Structure
    "concrete_m20":       {"factor": 148,   "unit": "m³",  "discipline": "Structure",    "name": "M20 RCC"},
    "concrete_m25":       {"factor": 162,   "unit": "m³",  "discipline": "Structure",    "name": "M25 RCC"},
    "concrete_m30":       {"factor": 178,   "unit": "m³",  "discipline": "Structure",    "name": "M30 RCC"},
    "rebar_steel":        {"factor": 1460,  "unit": "MT",  "discipline": "Structure",    "name": "Reinforcement Steel"},
    "structural_steel":   {"factor": 1550,  "unit": "MT",  "discipline": "Structure",    "name": "Structural Steel"},
    "brick_masonry":      {"factor": 330,   "unit": "m³",  "discipline": "Architecture", "name": "Brick Masonry"},
    "aac_block":          {"factor": 180,   "unit": "m³",  "discipline": "Architecture", "name": "AAC Block"},
    "glass":              {"factor": 25.5,  "unit": "m²",  "discipline": "Architecture", "name": "Float Glass"},
    "aluminium":          {"factor": 155,   "unit": "kg",  "discipline": "Architecture", "name": "Aluminium (virgin)"},
    "aluminium_recycled": {"factor": 28,    "unit": "kg",  "discipline": "Architecture", "name": "Aluminium (recycled)"},
    "upvc":               {"factor": 3.1,   "unit": "kg",  "discipline": "Architecture", "name": "uPVC"},
    "ceramic_tile":       {"factor": 12.4,  "unit": "m²",  "discipline": "Architecture", "name": "Ceramic Tile"},
    "granite":            {"factor": 640,   "unit": "MT",  "discipline": "Architecture", "name": "Granite"},
    "marble":             {"factor": 580,   "unit": "MT",  "discipline": "Architecture", "name": "Marble"},
    "gypsum_board":       {"factor": 6.75,  "unit": "m²",  "discipline": "Architecture", "name": "Gypsum Board"},
    "paint":              {"factor": 34.6,  "unit": "L",   "discipline": "Architecture", "name": "Paint"},
    "gi_ductwork":        {"factor": 2.55,  "unit": "kg",  "discipline": "MEP",          "name": "GI Ductwork"},
    "gi_pipe":            {"factor": 2.55,  "unit": "kg",  "discipline": "MEP",          "name": "GI Pipe"},
    "cpvc_pipe":          {"factor": 3.23,  "unit": "kg",  "discipline": "MEP",          "name": "CPVC Pipe"},
    "upvc_pipe":          {"factor": 3.1,   "unit": "kg",  "discipline": "MEP",          "name": "uPVC Pipe"},
    "copper_wire":        {"factor": 3.66,  "unit": "kg",  "discipline": "MEP",          "name": "Copper Cable"},
    "bitumen":            {"factor": 0.369, "unit": "kg",  "discipline": "Civil",        "name": "Bitumen"},
    "aggregate":          {"factor": 7.57,  "unit": "MT",  "discipline": "Civil",        "name": "Aggregate"},
    "sand":               {"factor": 5.5,   "unit": "MT",  "discipline": "Civil",        "name": "Sand"},
    "cement":             {"factor": 830,   "unit": "MT",  "discipline": "Structure",    "name": "Cement (OPC)"},
    "fly_ash_cement":     {"factor": 450,   "unit": "MT",  "discipline": "Structure",    "name": "Fly Ash Blended Cement"},
    "timber":             {"factor": 310,   "unit": "m³",  "discipline": "Architecture", "name": "Timber (general)"},
    "plywood":            {"factor": 1070,  "unit": "MT",  "discipline": "Architecture", "name": "Plywood"},
}

IGBC_BENCHMARKS = {
    "Residential":  {"low": 300, "medium": 450, "high": 650},
    "Commercial":   {"low": 400, "medium": 600, "high": 900},
    "Industrial":   {"low": 350, "medium": 500, "high": 750},
    "Institutional":{"low": 350, "medium": 500, "high": 700},
}

def match_carbon(item_name, unit=""):
    item_lower = item_name.lower()
    scores = {}
    for key, data in CARBON_DB.items():
        score = 0
        for word in key.replace("_", " ").split():
            if word in item_lower: score += 2
        for word in data["name"].lower().split():
            if len(word) > 3 and word in item_lower: score += 1
        if score > 0:
            scores[key] = score
    if scores:
        return CARBON_DB[max(scores, key=scores.get)]
    unit_lower = unit.lower()
    if any(x in unit_lower for x in ["m³","m3","cum"]):
        return {"factor": 150, "unit": "m³", "discipline": "Structure", "name": "Concrete (estimated)"}
    if any(x in unit_lower for x in ["mt","ton"]):
        return {"factor": 1460, "unit": "MT", "discipline": "Structure", "name": "Steel (estimated)"}
    if any(x in unit_lower for x in ["m²","m2","sqm"]):
        return {"factor": 15, "unit": "m²", "discipline": "Architecture", "name": "Surface material (estimated)"}
    return {"factor": 50, "unit": "unit", "discipline": "General", "name": "General item (estimated)"}

def compute_carbon(df, project_type="Commercial"):
    col_map = {}
    for col in df.columns:
        cl = col.lower().replace(" ","").replace("_","")
        if any(x in cl for x in ["item","description","element","name","material"]):
            col_map.setdefault("item", col)
        if any(x in cl for x in ["qty","quantity","vol","area","count"]):
            col_map.setdefault("quantity", col)
        if any(x in cl for x in ["unit","uom"]):
            col_map.setdefault("unit", col)

    item_col = col_map.get("item", df.columns[0])
    qty_col  = col_map.get("quantity", None)
    unit_col = col_map.get("unit", None)

    rows     = []
    by_disc  = {}
    total_co2 = 0

    for _, row in df.iterrows():
        item = str(row.get(item_col, "")).strip()
        if not item or item.lower() in ["nan","total","subtotal",""]:
            continue
        try:
            qty = float(str(row[qty_col]).replace(",","")) \
                if qty_col and str(row.get(qty_col,"")) not in ["nan",""] else 1.0
        except Exception:
            qty = 1.0
        unit = str(row[unit_col]).strip() \
            if unit_col and str(row.get(unit_col,"")) not in ["nan",""] else ""

        carbon_data = match_carbon(item, unit)
        line_co2    = qty * carbon_data["factor"]

        rows.append({
            "item":       item,
            "material":   carbon_data["name"],
            "discipline": carbon_data["discipline"],
            "quantity":   qty,
            "unit":       unit or carbon_data["unit"],
            "factor":     carbon_data["factor"],
            "line_co2":   round(line_co2, 2)
        })
        by_disc[carbon_data["discipline"]] = \
            by_disc.get(carbon_data["discipline"], 0) + line_co2
        total_co2 += line_co2

    return {
        "rows":      rows,
        "by_disc":   by_disc,
        "total_co2": round(total_co2, 2),
        "item_count": len(rows),
        "benchmark": IGBC_BENCHMARKS.get(project_type,
                                          IGBC_BENCHMARKS["Commercial"])
    }

def fmt_co2(val):
    if val >= 1000:
        return f"{val/1000:.2f} tCO₂e"
    return f"{val:.1f} kgCO₂e"

def generate_carbon_report(result, project_type, project_area):
    llm = get_llm()
    disc_summary = "\n".join([
        f"  {d}: {fmt_co2(v)} ({v/result['total_co2']*100:.1f}%)"
        for d, v in sorted(result["by_disc"].items(), key=lambda x:-x[1])
    ])
    top_items = "\n".join([
        f"  {r['item'][:50]}: {fmt_co2(r['line_co2'])} ({r['quantity']} {r['unit']})"
        for r in sorted(result["rows"], key=lambda x:-x["line_co2"])[:8]
    ])
    intensity = result["total_co2"] / max(project_area, 1)

    prompt = f"""You are a sustainability consultant specializing in Indian green buildings
and embodied carbon assessment.

PROJECT: {project_type}, {project_area} sqm
Total Embodied Carbon: {fmt_co2(result['total_co2'])}
Carbon Intensity: {intensity:.1f} kgCO₂e/sqm
IGBC Benchmark (Low Carbon): <{result['benchmark']['low']} kgCO₂e/sqm

BY DISCIPLINE:
{disc_summary}

TOP CARBON ITEMS:
{top_items}

Write a CARBON INTELLIGENCE REPORT:

## CARBON ASSESSMENT SUMMARY
Overall verdict: is this project carbon-efficient? Compare intensity to IGBC/GRIHA benchmarks.
What rating could this project target (IGBC Gold, Platinum, GRIHA 4-star, 5-star)?

## HIGH CARBON HOTSPOTS
Top 3 materials driving carbon. For each: why it's high, what fraction of total, what substitution exists.

## LOW-CARBON SUBSTITUTIONS — INDIAN MARKET
For each major material, suggest a lower-carbon alternative available in India.
Format: Material → Substitution → Carbon saving % → Trade-off.
Focus on: fly ash cement vs OPC, AAC vs brick, recycled steel, timber alternatives,
low-e glass, recycled aluminium.

## IGBC / GRIHA COMPLIANCE PATH
What specific changes would move this project to IGBC Gold or Platinum?
List 3-5 concrete actions with estimated carbon reduction for each.

## OPERATIONAL CARBON NOTE
Brief note on solar PV potential, energy-efficient MEP systems, and passive design
strategies relevant for this project type in India.

## BOTTOM LINE
One paragraph: current carbon status, biggest opportunity, recommended next step.

Use kgCO₂e and tCO₂e throughout. Reference ICE Database, IGBC, and GRIHA."""

    return llm.invoke(prompt).content

CARBON_CSS = """
<style>
.co2-header { background:linear-gradient(135deg,#070F1E,#0D1B2E); border:1px solid rgba(50,200,100,0.15); border-radius:18px; padding:26px 30px; margin-bottom:20px; }
.co2-title  { font-family:'DM Serif Display',serif; font-size:1.9rem; color:#FFF; }
.co2-title span { color:#32C864; }
.co2-sub    { font-family:'DM Sans',sans-serif; font-size:0.87rem; color:#2A4A6A; }
.co2-badge  { display:inline-block; background:rgba(50,200,100,0.08); border:1px solid rgba(50,200,100,0.2); color:#32C864; font-family:'Space Mono',monospace; font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:4px; margin-right:8px; margin-bottom:10px; }
.co2-divider{ border:none; border-top:1px solid rgba(255,255,255,0.04); margin:20px 0; }
.co2-bar-bg { background:rgba(255,255,255,0.04); border-radius:4px; height:7px; overflow:hidden; margin-top:3px; }
.co2-bar-fill { height:7px; border-radius:4px; background:linear-gradient(90deg,#32C864,#00FFB2); }
</style>
"""

DISC_COLORS = {
    "Structure": "#FFD93D", "Architecture": "#FF6B6B",
    "MEP": "#00FFB2", "Civil": "#00D4FF", "General": "#A0B4C8"
}

def show_carbon_estimator():
    st.markdown(CARBON_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class='co2-header'>
        <div><span class='co2-badge'>NEW</span><span class='co2-badge'>v1.0</span><span class='co2-badge'>IGBC</span><span class='co2-badge'>GRIHA</span></div>
        <div class='co2-title'><span>Carbon</span> Estimator</div>
        <div class='co2-sub'>Upload your quantity takeoff. Get embodied carbon in kgCO₂e, IGBC/GRIHA benchmarking, low-carbon substitutions for the Indian market, and a compliance path to Green Building certification.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        project_type = st.selectbox("Project Type",
            ["Residential","Commercial","Industrial","Institutional"])
    with c2:
        project_area = st.number_input("Total Built-up Area (sqm)",
            min_value=100, max_value=500000, value=5000, step=100)
    with c3:
        target = st.selectbox("Green Building Target",
            ["IGBC Gold","IGBC Platinum","GRIHA 4-Star","GRIHA 5-Star","None"])

    qty_file = st.file_uploader("Upload Quantity Takeoff CSV",
                                 type=["csv"], key="carbon_upload", label_visibility="visible")

    if qty_file:
        df = pd.read_csv(qty_file)
        df.columns = [c.strip() for c in df.columns]
        with st.expander("Preview data"):
            st.dataframe(df.head(6), use_container_width=True)

        if st.button("🌿 Run Carbon Analysis"):
            with st.spinner("Computing embodied carbon..."):
                result = compute_carbon(df, project_type)
                report = generate_carbon_report(result, project_type, project_area)
                st.session_state["carbon_result"] = result
                st.session_state["carbon_report"] = report

    if "carbon_result" in st.session_state:
        r = st.session_state["carbon_result"]
        intensity = r["total_co2"] / max(project_area, 1)
        benchmark = r["benchmark"]

        # Verdict color
        if intensity < benchmark["low"]:
            verdict_color, verdict = "#32C864", "LOW CARBON ✓"
        elif intensity < benchmark["medium"]:
            verdict_color, verdict = "#FFD93D", "MEDIUM CARBON"
        else:
            verdict_color, verdict = "#FF4444", "HIGH CARBON ⚠"

        st.markdown(f"""
        <div style='display:flex;gap:10px;flex-wrap:wrap;margin:16px 0;'>
            <div style='background:rgba(255,255,255,0.02);border:1px solid rgba(50,200,100,0.1);border-radius:12px;padding:16px 20px;flex:1;min-width:130px;'>
                <div style='font-family:DM Serif Display,serif;font-size:1.4rem;color:#32C864;'>{fmt_co2(r['total_co2'])}</div>
                <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#1E3A5F;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>Total Embodied Carbon</div>
            </div>
            <div style='background:rgba(255,255,255,0.02);border:1px solid rgba(50,200,100,0.1);border-radius:12px;padding:16px 20px;flex:1;min-width:130px;'>
                <div style='font-family:DM Serif Display,serif;font-size:1.4rem;color:#32C864;'>{intensity:.0f} kgCO₂e/m²</div>
                <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#1E3A5F;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>Carbon Intensity</div>
            </div>
            <div style='background:rgba(255,255,255,0.02);border:1px solid rgba(50,200,100,0.1);border-radius:12px;padding:16px 20px;flex:1;min-width:130px;'>
                <div style='font-family:DM Serif Display,serif;font-size:1.1rem;color:{verdict_color};'>{verdict}</div>
                <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#1E3A5F;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>vs IGBC Benchmark</div>
            </div>
            <div style='background:rgba(255,255,255,0.02);border:1px solid rgba(50,200,100,0.1);border-radius:12px;padding:16px 20px;flex:1;min-width:130px;'>
                <div style='font-family:DM Serif Display,serif;font-size:1.4rem;color:#32C864;'>{r['item_count']}</div>
                <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#1E3A5F;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>Materials Assessed</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["🌿 Carbon Breakdown", "📋 Line Items", "🤖 AI Carbon Report"])

        with tab1:
            st.markdown("""<div style='font-family:Space Mono,monospace;font-size:0.62rem;
            color:#1E3A5F;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;'>
            Carbon by Discipline</div>""", unsafe_allow_html=True)
            for disc, val in sorted(r["by_disc"].items(), key=lambda x:-x[1]):
                pct   = val / r["total_co2"] * 100
                color = DISC_COLORS.get(disc, "#A0B4C8")
                st.markdown(f"""
                <div style='margin-bottom:10px;'>
                    <div style='display:flex;justify-content:space-between;
                    font-family:DM Sans,sans-serif;font-size:0.82rem;color:#4A6A8A;margin-bottom:3px;'>
                        <span style='color:{color};'>{disc}</span>
                        <span>{fmt_co2(val)} &nbsp;<span style='color:#1E3A5F;'>{pct:.1f}%</span></span>
                    </div>
                    <div class='co2-bar-bg'>
                        <div class='co2-bar-fill' style='width:{pct}%;background:{color};'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Benchmark comparison
            st.markdown(f"""<div style='margin-top:16px;font-family:Space Mono,monospace;
            font-size:0.62rem;color:#1E3A5F;letter-spacing:2px;text-transform:uppercase;
            margin-bottom:8px;'>IGBC Benchmark — {project_type}</div>
            <div style='font-family:DM Sans,sans-serif;font-size:0.82rem;color:#2A4A6A;'>
            Low Carbon: &lt;{benchmark['low']} kgCO₂e/m² &nbsp;|&nbsp;
            Medium: {benchmark['low']}–{benchmark['medium']} &nbsp;|&nbsp;
            High: &gt;{benchmark['medium']} &nbsp;|&nbsp;
            <span style='color:{verdict_color};font-weight:600;'>This project: {intensity:.0f} kgCO₂e/m²</span>
            </div>""", unsafe_allow_html=True)

        with tab2:
            st.markdown("""<div style='font-family:Space Mono,monospace;font-size:0.62rem;
            color:#1E3A5F;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;'>
            Line Item Carbon</div>""", unsafe_allow_html=True)
            for row in sorted(r["rows"], key=lambda x:-x["line_co2"]):
                color = DISC_COLORS.get(row["discipline"], "#A0B4C8")
                st.markdown(f"""
                <div style='display:flex;justify-content:space-between;align-items:center;
                padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.03);
                font-family:DM Sans,sans-serif;font-size:0.8rem;'>
                    <div style='flex:3;color:#4A6A8A;padding-right:12px;'>
                        <span style='color:{color};font-size:0.65rem;'>▸</span>
                        {row['item'][:55]}{'...' if len(row['item'])>55 else ''}
                    </div>
                    <div style='flex:1;text-align:right;font-family:Space Mono,monospace;
                    font-size:0.7rem;color:#2A4A6A;'>{row['quantity']:,.2f} {row['unit']}</div>
                    <div style='flex:1;text-align:right;font-family:Space Mono,monospace;
                    font-size:0.75rem;color:#32C864;font-weight:600;'>{fmt_co2(row['line_co2'])}</div>
                </div>
                """, unsafe_allow_html=True)

        with tab3:
            st.markdown(st.session_state["carbon_report"])
            st.download_button("⬇️ Download Carbon Report",
                data=st.session_state["carbon_report"],
                file_name=f"NexBIM_Carbon_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", key="dl_carbon")

    st.markdown("""<div style='text-align:center;font-family:Space Mono,monospace;font-size:0.6rem;
    color:#0E1E30;margin-top:24px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.03);'>
    NEXBIM CARBON ESTIMATOR v1.0 · DEVENDRA GUPTA · ICE DATABASE · IGBC · GRIHA</div>""",
    unsafe_allow_html=True)
