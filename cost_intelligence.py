import streamlit as st
import pandas as pd
import os
import io
import json
from datetime import datetime
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# ── Indian Construction Rate Database (INR) ───────────────────────────────────
# Rates based on CPWD DSR 2023-25, NBO rates, Indian market averages

RATE_DATABASE = {
    # ── STRUCTURE ─────────────────────────────────────────────────────────
    "concrete_m10":          {"rate": 4800,   "unit": "m³",  "discipline": "Structure",    "description": "M10 Plain Cement Concrete"},
    "concrete_m20":          {"rate": 6200,   "unit": "m³",  "discipline": "Structure",    "description": "M20 RCC (columns, beams, slabs)"},
    "concrete_m25":          {"rate": 6800,   "unit": "m³",  "discipline": "Structure",    "description": "M25 RCC (high-rise, commercial)"},
    "concrete_m30":          {"rate": 7500,   "unit": "m³",  "discipline": "Structure",    "description": "M30 RCC (foundations, podiums)"},
    "rebar_fe415":           {"rate": 68000,  "unit": "MT",  "discipline": "Structure",    "description": "Fe415 Reinforcement Steel"},
    "rebar_fe500":           {"rate": 70000,  "unit": "MT",  "discipline": "Structure",    "description": "Fe500D TMT Reinforcement Steel"},
    "structural_steel":      {"rate": 85000,  "unit": "MT",  "discipline": "Structure",    "description": "Structural Steel IS 2062"},
    "formwork_timber":       {"rate": 320,    "unit": "m²",  "discipline": "Structure",    "description": "Timber Formwork slab/beam"},
    "formwork_shuttering":   {"rate": 280,    "unit": "m²",  "discipline": "Structure",    "description": "Steel Shuttering Plates"},
    "pile_bored":            {"rate": 3200,   "unit": "RMT", "discipline": "Structure",    "description": "Bored Cast-in-situ Pile 600mm"},
    "pile_precast":          {"rate": 2800,   "unit": "RMT", "discipline": "Structure",    "description": "Precast Concrete Pile"},
    "footing_isolated":      {"rate": 18000,  "unit": "No.", "discipline": "Structure",    "description": "Isolated RCC Footing"},
    "retaining_wall":        {"rate": 8500,   "unit": "m³",  "discipline": "Structure",    "description": "RCC Retaining Wall"},

    # ── ARCHITECTURE ──────────────────────────────────────────────────────
    "brick_wall_230":        {"rate": 1800,   "unit": "m³",  "discipline": "Architecture", "description": "230mm Brick Masonry Wall"},
    "brick_wall_115":        {"rate": 1600,   "unit": "m³",  "discipline": "Architecture", "description": "115mm Brick Masonry partition"},
    "aac_block_200":         {"rate": 2800,   "unit": "m³",  "discipline": "Architecture", "description": "200mm AAC Block Wall"},
    "aac_block_100":         {"rate": 2400,   "unit": "m³",  "discipline": "Architecture", "description": "100mm AAC Block partition"},
    "plaster_internal":      {"rate": 180,    "unit": "m²",  "discipline": "Architecture", "description": "12mm Internal Cement Plaster"},
    "plaster_external":      {"rate": 220,    "unit": "m²",  "discipline": "Architecture", "description": "20mm External Cement Plaster"},
    "paint_internal":        {"rate": 85,     "unit": "m²",  "discipline": "Architecture", "description": "Interior Emulsion Paint 2 coats"},
    "paint_external":        {"rate": 120,    "unit": "m²",  "discipline": "Architecture", "description": "Exterior Weather Coat Paint"},
    "tile_vitrified":        {"rate": 680,    "unit": "m²",  "discipline": "Architecture", "description": "Vitrified Floor Tiles 600x600"},
    "tile_ceramic":          {"rate": 420,    "unit": "m²",  "discipline": "Architecture", "description": "Ceramic Floor/Wall Tiles"},
    "tile_granite":          {"rate": 1800,   "unit": "m²",  "discipline": "Architecture", "description": "Granite Flooring polished"},
    "tile_marble":           {"rate": 2400,   "unit": "m²",  "discipline": "Architecture", "description": "Italian Marble Flooring"},
    "door_flush":            {"rate": 6500,   "unit": "No.", "discipline": "Architecture", "description": "Flush Door with Frame and Hardware"},
    "door_upvc":             {"rate": 12000,  "unit": "No.", "discipline": "Architecture", "description": "uPVC Door with Frame"},
    "window_upvc":           {"rate": 8500,   "unit": "No.", "discipline": "Architecture", "description": "uPVC Window 1.2x1.2m"},
    "window_aluminium":      {"rate": 9500,   "unit": "No.", "discipline": "Architecture", "description": "Aluminium Glazed Window"},
    "curtain_wall":          {"rate": 4800,   "unit": "m²",  "discipline": "Architecture", "description": "Aluminium Curtain Wall System"},
    "false_ceiling_gyp":     {"rate": 380,    "unit": "m²",  "discipline": "Architecture", "description": "Gypsum False Ceiling"},
    "false_ceiling_grid":    {"rate": 280,    "unit": "m²",  "discipline": "Architecture", "description": "Grid False Ceiling 600x600"},
    "waterproofing_terrace": {"rate": 320,    "unit": "m²",  "discipline": "Architecture", "description": "Terrace Waterproofing crystalline"},
    "waterproofing_basement":{"rate": 450,    "unit": "m²",  "discipline": "Architecture", "description": "Basement Waterproofing membrane"},
    "insulation_thermal":    {"rate": 280,    "unit": "m²",  "discipline": "Architecture", "description": "Thermal Insulation Board 50mm"},
    "staircase_rcc":         {"rate": 85000,  "unit": "No.", "discipline": "Architecture", "description": "RCC Staircase per flight"},

    # ── MEP — HVAC ────────────────────────────────────────────────────────
    "duct_gi_light":         {"rate": 1200,   "unit": "m²",  "discipline": "MEP",          "description": "GI Ductwork light gauge up to 1m"},
    "duct_gi_medium":        {"rate": 1600,   "unit": "m²",  "discipline": "MEP",          "description": "GI Ductwork medium gauge"},
    "duct_gi_heavy":         {"rate": 2200,   "unit": "m²",  "discipline": "MEP",          "description": "GI Ductwork heavy gauge over 1m"},
    "ahu_unit":              {"rate": 180000, "unit": "No.", "discipline": "MEP",          "description": "Air Handling Unit 10TR"},
    "fcu_unit":              {"rate": 45000,  "unit": "No.", "discipline": "MEP",          "description": "Fan Coil Unit 4-pipe"},
    "chiller_unit":          {"rate": 850000, "unit": "No.", "discipline": "MEP",          "description": "Water-cooled Chiller 100TR"},
    "vrf_outdoor":           {"rate": 280000, "unit": "No.", "discipline": "MEP",          "description": "VRF Outdoor Unit 10HP"},
    "vrf_indoor":            {"rate": 28000,  "unit": "No.", "discipline": "MEP",          "description": "VRF Indoor Unit cassette"},

    # ── MEP — PLUMBING ────────────────────────────────────────────────────
    "pipe_cpvc_25":          {"rate": 180,    "unit": "RMT", "discipline": "MEP",          "description": "CPVC Pipe 25mm hot cold water"},
    "pipe_cpvc_50":          {"rate": 320,    "unit": "RMT", "discipline": "MEP",          "description": "CPVC Pipe 50mm"},
    "pipe_upvc_110":         {"rate": 280,    "unit": "RMT", "discipline": "MEP",          "description": "uPVC Soil Pipe 110mm"},
    "pipe_upvc_160":         {"rate": 420,    "unit": "RMT", "discipline": "MEP",          "description": "uPVC Drainage Pipe 160mm"},
    "pipe_gi_50":            {"rate": 520,    "unit": "RMT", "discipline": "MEP",          "description": "GI Pipe 50mm water supply"},
    "pipe_gi_100":           {"rate": 980,    "unit": "RMT", "discipline": "MEP",          "description": "GI Pipe 100mm fire fighting"},
    "sanitary_wc":           {"rate": 8500,   "unit": "No.", "discipline": "MEP",          "description": "WC Suite wall-hung mid-range"},
    "sanitary_washbasin":    {"rate": 4200,   "unit": "No.", "discipline": "MEP",          "description": "Wash Basin with CP Fittings"},
    "pump_submersible":      {"rate": 32000,  "unit": "No.", "discipline": "MEP",          "description": "Submersible Pump 2HP"},
    "pump_booster":          {"rate": 65000,  "unit": "No.", "discipline": "MEP",          "description": "Hydro-pneumatic Booster Pump Set"},
    "stp_unit":              {"rate": 450000, "unit": "No.", "discipline": "MEP",          "description": "STP Package Unit 50 KLD"},
    "water_tank_overhead":   {"rate": 18000,  "unit": "No.", "discipline": "MEP",          "description": "Overhead Water Tank 10000L HDPE"},

    # ── MEP — ELECTRICAL ─────────────────────────────────────────────────
    "cable_1_5":             {"rate": 28,     "unit": "RMT", "discipline": "MEP",          "description": "1.5 sqmm FR Cable lighting"},
    "cable_4_0":             {"rate": 52,     "unit": "RMT", "discipline": "MEP",          "description": "4 sqmm FR Cable power"},
    "cable_10":              {"rate": 120,    "unit": "RMT", "discipline": "MEP",          "description": "10 sqmm FR Cable"},
    "cable_35":              {"rate": 380,    "unit": "RMT", "discipline": "MEP",          "description": "35 sqmm Armoured Cable"},
    "cable_95":              {"rate": 980,    "unit": "RMT", "discipline": "MEP",          "description": "95 sqmm HT Cable"},
    "conduit_pvc_25":        {"rate": 45,     "unit": "RMT", "discipline": "MEP",          "description": "25mm PVC Conduit concealed"},
    "conduit_gi_32":         {"rate": 120,    "unit": "RMT", "discipline": "MEP",          "description": "32mm GI Conduit surface"},
    "db_mcb_board":          {"rate": 8500,   "unit": "No.", "discipline": "MEP",          "description": "MCB Distribution Board 12-way"},
    "transformer_100kva":    {"rate": 380000, "unit": "No.", "discipline": "MEP",          "description": "100 KVA Transformer dry type"},
    "dg_set_125kva":         {"rate": 950000, "unit": "No.", "discipline": "MEP",          "description": "125 KVA DG Set acoustic enclosure"},
    "solar_panel_1kw":       {"rate": 45000,  "unit": "No.", "discipline": "MEP",          "description": "1 kWp Solar PV Panel and Inverter"},
    "light_led_panel":       {"rate": 1800,   "unit": "No.", "discipline": "MEP",          "description": "LED Panel Light 18W 600x600"},
    "light_street":          {"rate": 8500,   "unit": "No.", "discipline": "MEP",          "description": "LED Street Light 50W on pole"},
    "fire_sprinkler":        {"rate": 1200,   "unit": "No.", "discipline": "MEP",          "description": "Fire Sprinkler Head and Pipe per head"},
    "fire_alarm_detector":   {"rate": 2800,   "unit": "No.", "discipline": "MEP",          "description": "Smoke Detector and Wiring"},
    "fire_extinguisher":     {"rate": 2200,   "unit": "No.", "discipline": "MEP",          "description": "CO2 Fire Extinguisher 4.5kg"},
    "lift_8_person":         {"rate": 1800000,"unit": "No.", "discipline": "MEP",          "description": "Passenger Lift 8-person 6 floors"},
    "lift_13_person":        {"rate": 2800000,"unit": "No.", "discipline": "MEP",          "description": "Passenger Lift 13-person 10 floors"},

    # ── CIVIL / SITEWORK ──────────────────────────────────────────────────
    "earthwork_excavation":  {"rate": 320,    "unit": "m³",  "discipline": "Civil",        "description": "Earth Excavation mechanical"},
    "earthwork_filling":     {"rate": 280,    "unit": "m³",  "discipline": "Civil",        "description": "Earth Filling and Compaction"},
    "pcc_flooring":          {"rate": 3800,   "unit": "m³",  "discipline": "Civil",        "description": "PCC M15 Flooring Bedding"},
    "road_bitumen":          {"rate": 580,    "unit": "m²",  "discipline": "Civil",        "description": "Bituminous Road 60mm BM 25mm SDBC"},
    "road_concrete":         {"rate": 650,    "unit": "m²",  "discipline": "Civil",        "description": "Cement Concrete Road 150mm M25"},
    "compound_wall":         {"rate": 3200,   "unit": "RMT", "discipline": "Civil",        "description": "Compound Wall 1.8m brick plaster"},
    "gate_ms":               {"rate": 45000,  "unit": "No.", "discipline": "Civil",        "description": "MS Gate 3m wide fabricated"},
    "drainage_stormwater":   {"rate": 1800,   "unit": "RMT", "discipline": "Civil",        "description": "Stormwater Drain RCC 600mm"},
    "landscaping_basic":     {"rate": 280,    "unit": "m²",  "discipline": "Civil",        "description": "Basic Landscaping grass and plants"},
    "parking_surface":       {"rate": 420,    "unit": "m²",  "discipline": "Civil",        "description": "Surface Car Parking interlocking paver"},
    "parking_basement":      {"rate": 18000,  "unit": "m²",  "discipline": "Civil",        "description": "Basement Parking RCC structure finishing"},
}

PROJECT_TYPES = [
    "Residential — Low Rise (G+4 and below)",
    "Residential — Mid Rise (G+5 to G+12)",
    "Residential — High Rise (G+13 and above)",
    "Commercial — Office Building",
    "Commercial — Retail / Mall",
    "Commercial — Hotel",
    "Industrial — Factory / Warehouse",
    "Industrial — IT Park / Tech Campus",
    "Infrastructure — Road / Bridge",
    "Infrastructure — Institutional (School / Hospital)",
    "Mixed Use Development"
]

CITY_MULTIPLIERS = {
    "Mumbai":      1.35,
    "Delhi / NCR": 1.30,
    "Bangalore":   1.25,
    "Hyderabad":   1.20,
    "Chennai":     1.18,
    "Pune":        1.15,
    "Kolkata":     1.10,
    "Ahmedabad":   1.08,
    "Tier 2 City": 1.00,
    "Tier 3 City": 0.90,
}

DISC_COLORS = {
    "Structure":    "#FFD93D",
    "Architecture": "#FF6B6B",
    "MEP":          "#00FFB2",
    "Civil":        "#00D4FF",
    "General":      "#A0B4C8"
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile"
    )

def fmt_inr(amount: float) -> str:
    if amount >= 1e7:
        return f"₹{amount/1e7:.2f} Cr"
    elif amount >= 1e5:
        return f"₹{amount/1e5:.2f} L"
    else:
        return f"₹{amount:,.0f}"

def parse_quantity_csv(file) -> pd.DataFrame:
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return None

def detect_columns(df: pd.DataFrame) -> dict:
    col_map = {}
    for col in df.columns:
        cl = col.lower().replace(" ", "").replace("_", "")
        if any(x in cl for x in ["item", "description", "element", "work", "name", "material"]):
            col_map.setdefault("item", col)
        if any(x in cl for x in ["qty", "quantity", "vol", "volume", "area", "count", "number", "nos"]):
            col_map.setdefault("quantity", col)
        if any(x in cl for x in ["unit", "uom", "measure"]):
            col_map.setdefault("unit", col)
        if any(x in cl for x in ["floor", "level", "storey", "story"]):
            col_map.setdefault("floor", col)
        if any(x in cl for x in ["discipline", "trade", "category", "type"]):
            col_map.setdefault("discipline", col)
        if any(x in cl for x in ["rate", "unitrate", "unitcost", "price"]):
            col_map.setdefault("rate", col)
    return col_map

def match_rate(item_name: str, unit: str = "") -> dict:
    item_lower = item_name.lower()
    matches = {}
    for key, data in RATE_DATABASE.items():
        score = 0
        for word in key.replace("_", " ").lower().split():
            if word in item_lower:
                score += 2
        for word in data["description"].lower().split():
            if len(word) > 3 and word in item_lower:
                score += 1
        if score > 0:
            matches[key] = score
    if matches:
        return RATE_DATABASE[max(matches, key=matches.get)]

    unit_lower = unit.lower() if unit else ""
    if any(x in unit_lower for x in ["m³", "cum", "m3"]):
        return {"rate": 5500, "unit": "m³",  "discipline": "Structure",    "description": "Concrete or masonry work (estimated)"}
    if any(x in unit_lower for x in ["m²", "sqm", "m2"]):
        return {"rate": 450,  "unit": "m²",  "discipline": "Architecture", "description": "Surface work (estimated)"}
    if any(x in unit_lower for x in ["rmt", "rm", "lm"]) or unit_lower.strip() == "m":
        return {"rate": 350,  "unit": "RMT", "discipline": "Civil",        "description": "Linear work (estimated)"}
    if any(x in unit_lower for x in ["no", "nr", "nos"]):
        return {"rate": 8000, "unit": "No.", "discipline": "MEP",          "description": "Equipment or fitting (estimated)"}
    if any(x in unit_lower for x in ["mt", "ton", "kg"]):
        return {"rate": 70000,"unit": "MT",  "discipline": "Structure",    "description": "Steel or metal work (estimated)"}
    return {"rate": 2000, "unit": "unit", "discipline": "General", "description": "General item (estimated)"}

def compute_estimate(df, col_map, city_multiplier, project_type):
    rows     = []
    by_disc  = {}
    by_floor = {}

    item_col  = col_map.get("item",     df.columns[0])
    qty_col   = col_map.get("quantity", None)
    unit_col  = col_map.get("unit",     None)
    floor_col = col_map.get("floor",    None)
    rate_col  = col_map.get("rate",     None)

    for _, row in df.iterrows():
        item_name = str(row.get(item_col, "Unknown Item")).strip()
        if not item_name or item_name.lower() in ["nan", "total", "subtotal", ""]:
            continue
        try:
            qty = float(str(row[qty_col]).replace(",", "")) \
                if qty_col and str(row.get(qty_col, "")) not in ["nan", ""] else 1.0
        except Exception:
            qty = 1.0

        unit  = str(row[unit_col]).strip() \
            if unit_col and str(row.get(unit_col, "")) not in ["nan", ""] else ""
        floor = str(row[floor_col]).strip() \
            if floor_col and str(row.get(floor_col, "")) not in ["nan", ""] else "Unspecified"

        if rate_col and str(row.get(rate_col, "")) not in ["nan", ""]:
            try:
                db_rate   = float(str(row[rate_col]).replace(",", ""))
                rate_data = match_rate(item_name, unit)
                discipline, description, matched = rate_data["discipline"], rate_data["description"], False
            except Exception:
                rate_data = match_rate(item_name, unit)
                db_rate, discipline, description, matched = rate_data["rate"], rate_data["discipline"], rate_data["description"], True
        else:
            rate_data = match_rate(item_name, unit)
            db_rate, discipline, description, matched = rate_data["rate"], rate_data["discipline"], rate_data["description"], True

        adjusted_rate = db_rate * city_multiplier
        line_total    = qty * adjusted_rate

        rows.append({
            "item": item_name, "description": description,
            "discipline": discipline, "floor": floor,
            "quantity": qty, "unit": unit or rate_data.get("unit", "unit"),
            "base_rate": db_rate, "adjusted_rate": round(adjusted_rate, 0),
            "line_total": round(line_total, 0), "matched": matched
        })

        by_disc[discipline]  = by_disc.get(discipline, 0) + line_total
        by_floor[floor]      = by_floor.get(floor, 0)    + line_total

    grand_total = sum(r["line_total"] for r in rows)
    contingency = grand_total * 0.05
    overheads   = grand_total * 0.03

    return {
        "rows": rows, "by_disc": by_disc, "by_floor": by_floor,
        "grand_total": round(grand_total, 0),
        "contingency": round(contingency, 0),
        "overheads":   round(overheads, 0),
        "final_total": round(grand_total + contingency + overheads, 0),
        "project_type": project_type, "item_count": len(rows)
    }

def generate_ai_report(estimate, project_type, city):
    llm = get_llm()
    disc_summary = "\n".join([
        f"  {d}: {fmt_inr(v)} ({v/estimate['grand_total']*100:.1f}%)"
        for d, v in sorted(estimate["by_disc"].items(), key=lambda x: -x[1])
    ])
    floor_summary = "\n".join([
        f"  {f}: {fmt_inr(v)}"
        for f, v in sorted(estimate["by_floor"].items(), key=lambda x: -x[1])
        if f != "Unspecified"
    ]) or "  No floor-level data available"
    top_items = "\n".join([
        f"  {r['item'][:50]}: {fmt_inr(r['line_total'])} "
        f"({r['quantity']} {r['unit']} @ ₹{r['adjusted_rate']:,.0f})"
        for r in sorted(estimate["rows"], key=lambda x: -x["line_total"])[:10]
    ])

    prompt = f"""You are a Senior Quantity Surveyor with 20 years of Indian construction experience.
Deep knowledge of CPWD DSR rates, IS codes, and value engineering for all project types.

PROJECT: {project_type} in {city}
Total BOQ Items: {estimate['item_count']}

COST SUMMARY:
Base Estimate:    {fmt_inr(estimate['grand_total'])}
Contingency 5%:   {fmt_inr(estimate['contingency'])}
Overheads 3%:     {fmt_inr(estimate['overheads'])}
FINAL COST:       {fmt_inr(estimate['final_total'])}

BY DISCIPLINE:
{disc_summary}

BY FLOOR:
{floor_summary}

TOP 10 COST ITEMS:
{top_items}

Write a comprehensive COST INTELLIGENCE REPORT with these exact sections:

## EXECUTIVE SUMMARY
2-3 sentences: total cost, project type assessment, is this estimate reasonable for {city}?

## COST BREAKDOWN ANALYSIS
Is the discipline ratio typical for {project_type}? Flag any discipline that seems over or under-estimated.
Comment on floor-by-floor distribution if available.

## MARKET RATE ASSESSMENT — {city}
Compare against current {city} market rates. Give typical cost per sqft or sqm range for {project_type} in {city}.
Flag any line items significantly above or below market. Call out volatile materials (steel, cement, copper, aluminium).

## VALUE ENGINEERING RECOMMENDATIONS
5 specific actionable recommendations. For each: what to change, estimated saving %, quality trade-off.
Focus on Indian substitutions: AAC vs brick, uPVC vs GI, VRF vs chilled water, etc.

## COST RISK FLAGS
3-5 risks that could cause overrun. For each: what, why it matters for {project_type} in {city}, how to mitigate.

## PROCUREMENT RECOMMENDATIONS
Which items need early procurement (long lead times), which benefit from bulk buying,
which need rate contracts.

## BOTTOM LINE
Is this a well-structured estimate? Confidence level? Single most important action before finalising budget.

Use INR throughout. Reference CPWD DSR, IS codes, Indian standards where relevant. Be direct and specific."""

    return llm.invoke(prompt).content

def export_estimate_csv(estimate):
    lines = ["Item,Description,Discipline,Floor,Quantity,Unit,Base Rate INR,Adjusted Rate INR,Line Total INR"]
    for r in estimate["rows"]:
        lines.append(f'"{r["item"]}","{r["description"]}",{r["discipline"]},{r["floor"]},'
                     f'{r["quantity"]},{r["unit"]},{r["base_rate"]},{r["adjusted_rate"]},{r["line_total"]}')
    lines.append(f'"","","","","","","","Subtotal",{estimate["grand_total"]}')
    lines.append(f'"","","","","","","","Contingency 5%",{estimate["contingency"]}')
    lines.append(f'"","","","","","","","Overheads 3%",{estimate["overheads"]}')
    lines.append(f'"","","","","","","","TOTAL COST INR",{estimate["final_total"]}')
    return "\n".join(lines)

# ── CSS ───────────────────────────────────────────────────────────────────────

COST_CSS = """
<style>
.ci-header {
    background: linear-gradient(135deg, #070F1E 0%, #0D1B2E 100%);
    border: 1px solid rgba(0,255,100,0.15);
    border-radius: 18px; padding: 26px 30px;
    margin-bottom: 20px; position: relative; overflow: hidden;
}
.ci-header::after {
    content:''; position:absolute; top:-40%; right:-5%;
    width:300px; height:300px;
    background:radial-gradient(circle,rgba(0,255,100,0.05) 0%,transparent 70%);
    pointer-events:none;
}
.ci-title { font-family:'Syne',sans-serif; font-size:1.9rem; font-weight:800; color:#FFF; margin:0 0 4px 0; letter-spacing:-0.5px; }
.ci-title span { color:#00FF64; }
.ci-sub { font-family:'Space Grotesk',sans-serif; font-size:0.87rem; color:#2A4A6A; margin:0; }
.ci-badge { display:inline-block; background:rgba(0,255,100,0.08); border:1px solid rgba(0,255,100,0.2); color:#00FF64; font-family:'JetBrains Mono',monospace; font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:4px; margin-right:8px; }
.ci-stat-row { display:flex; gap:10px; flex-wrap:wrap; margin:16px 0; }
.ci-stat-card { background:rgba(255,255,255,0.02); border:1px solid rgba(0,255,100,0.1); border-radius:12px; padding:16px 20px; flex:1; min-width:130px; }
.ci-stat-value { font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:800; color:#00FF64; line-height:1.1; }
.ci-stat-label { font-family:'JetBrains Mono',monospace; font-size:0.6rem; color:#1E3A5F; letter-spacing:1.5px; text-transform:uppercase; margin-top:4px; }
.ci-disc-bar-row { margin-bottom:10px; }
.ci-disc-name { font-family:'Space Grotesk',sans-serif; font-size:0.82rem; color:#4A6A8A; display:flex; justify-content:space-between; margin-bottom:3px; }
.ci-disc-bar-bg { background:rgba(255,255,255,0.04); border-radius:4px; height:6px; overflow:hidden; }
.ci-disc-bar-fill { height:6px; border-radius:4px; }
.ci-line-item { display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.03); font-family:'Space Grotesk',sans-serif; font-size:0.8rem; }
.ci-line-name  { color:#4A6A8A; flex:3; padding-right:12px; }
.ci-line-qty   { color:#2A4A6A; flex:1; text-align:right; font-family:'JetBrains Mono',monospace; font-size:0.72rem; }
.ci-line-rate  { color:#2A4A6A; flex:1; text-align:right; font-family:'JetBrains Mono',monospace; font-size:0.72rem; }
.ci-line-total { color:#00FF64; flex:1; text-align:right; font-family:'JetBrains Mono',monospace; font-size:0.75rem; font-weight:600; }
.ci-total-row { background:rgba(0,255,100,0.04); border:1px solid rgba(0,255,100,0.15); border-radius:10px; padding:14px 18px; margin-top:12px; }
.ci-total-label { font-family:'Syne',sans-serif; font-size:1rem; font-weight:700; color:#FFF; }
.ci-total-value { font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800; color:#00FF64; }
.ci-info-pill { background:rgba(0,255,100,0.03); border:1px solid rgba(0,255,100,0.1); border-radius:8px; padding:10px 14px; margin-bottom:8px; font-family:'Space Grotesk',sans-serif; font-size:0.82rem; color:#4A6A8A; }
.ci-info-pill strong { color:#00FF64; }
.ci-section-label { font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:#1E3A5F; letter-spacing:2px; text-transform:uppercase; margin:18px 0 8px 0; }
.ci-divider { border:none; border-top:1px solid rgba(255,255,255,0.04); margin:20px 0; }
.ci-db-tag  { font-family:'JetBrains Mono',monospace; font-size:0.58rem; padding:1px 6px; border-radius:3px; background:rgba(0,255,100,0.08); color:#00FF64; border:1px solid rgba(0,255,100,0.2); margin-left:4px; }
.ci-est-tag { font-family:'JetBrains Mono',monospace; font-size:0.58rem; padding:1px 6px; border-radius:3px; background:rgba(255,178,0,0.08); color:#FFB200; border:1px solid rgba(255,178,0,0.2); margin-left:4px; }
</style>
"""

# ── Render helpers ────────────────────────────────────────────────────────────

def render_discipline_bars(by_disc, grand_total):
    if not by_disc or grand_total == 0:
        return
    st.markdown("<div class='ci-section-label'>Cost by Discipline</div>", unsafe_allow_html=True)
    for disc, amount in sorted(by_disc.items(), key=lambda x: -x[1]):
        pct   = (amount / grand_total * 100)
        color = DISC_COLORS.get(disc, "#A0B4C8")
        st.markdown(f"""
        <div class='ci-disc-bar-row'>
            <div class='ci-disc-name'>
                <span style='color:{color};'>{disc}</span>
                <span>{fmt_inr(amount)} &nbsp;<span style='color:#1E3A5F;'>{pct:.1f}%</span></span>
            </div>
            <div class='ci-disc-bar-bg'>
                <div class='ci-disc-bar-fill' style='width:{pct}%; background:{color};'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_floor_table(by_floor):
    filtered = {f: v for f, v in by_floor.items() if f != "Unspecified"}
    if not filtered:
        return
    st.markdown("<div class='ci-section-label'>Cost by Floor / Level</div>", unsafe_allow_html=True)
    total = sum(filtered.values())
    for floor, amount in sorted(filtered.items()):
        pct = (amount / total * 100) if total > 0 else 0
        st.markdown(f"""
        <div class='ci-line-item'>
            <div class='ci-line-name'>{floor}</div>
            <div class='ci-line-total' style='color:#00D4FF;'>{fmt_inr(amount)}</div>
            <div class='ci-line-rate'>{pct:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

def render_line_items(rows):
    st.markdown("<div class='ci-section-label'>Line Item Breakdown</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='ci-line-item' style='border-bottom:1px solid rgba(0,255,100,0.1); padding-bottom:6px;'>
        <div class='ci-line-name'  style='color:#1E3A5F; font-family:JetBrains Mono,monospace; font-size:0.68rem;'>ITEM</div>
        <div class='ci-line-qty'   style='color:#1E3A5F; font-family:JetBrains Mono,monospace; font-size:0.68rem;'>QTY</div>
        <div class='ci-line-rate'  style='color:#1E3A5F; font-family:JetBrains Mono,monospace; font-size:0.68rem;'>RATE</div>
        <div class='ci-line-total' style='color:#1E3A5F; font-family:JetBrains Mono,monospace; font-size:0.68rem;'>TOTAL</div>
    </div>
    """, unsafe_allow_html=True)
    for r in rows:
        tag   = "<span class='ci-db-tag'>DB</span>" if r["matched"] else "<span class='ci-est-tag'>EST</span>"
        color = DISC_COLORS.get(r["discipline"], "#A0B4C8")
        st.markdown(f"""
        <div class='ci-line-item'>
            <div class='ci-line-name'>
                <span style='color:{color}; font-size:0.65rem;'>▸</span>
                {r['item'][:55]}{'...' if len(r['item'])>55 else ''}{tag}
            </div>
            <div class='ci-line-qty'>{r['quantity']:,.2f} {r['unit']}</div>
            <div class='ci-line-rate'>₹{r['adjusted_rate']:,.0f}</div>
            <div class='ci-line-total'>{fmt_inr(r['line_total'])}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Main entry point ──────────────────────────────────────────────────────────

def show_cost_intelligence():
    st.markdown(COST_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class='ci-header'>
        <div style='margin-bottom:10px;'>
            <span class='ci-badge'>NEW</span>
            <span class='ci-badge'>v1.0</span>
            <span class='ci-badge'>INDIA</span>
        </div>
        <div class='ci-title'>BIM <span>Cost Intelligence</span></div>
        <div class='ci-sub'>
            Upload your quantity takeoff CSV — get a full project cost estimate in INR.
            Discipline breakdown · Floor-by-floor split · Market rate assessment ·
            Value engineering · AI cost narrative.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("→ How it works + sample CSV format"):
        st.markdown("""
        <div class='ci-info-pill'><strong>Step 1</strong> — Export your quantity takeoff from Revit (Schedule → Export) or any QS software as CSV. Minimum: Item/Description + Quantity. Optional: Unit, Floor, Discipline.</div>
        <div class='ci-info-pill'><strong>Step 2</strong> — Select project type and city. City multipliers are applied to base rates (Mumbai 1.35x · Tier 2 cities 1.0x baseline).</div>
        <div class='ci-info-pill'><strong>Step 3</strong> — NexBIM matches each item to the built-in Indian rate database (CPWD DSR 2023-25 basis), computes line totals, adds 5% contingency + 3% overheads, and runs a full AI cost intelligence report.</div>
        <div class='ci-info-pill'><strong>DB tag</strong> = rate matched from NexBIM database &nbsp;|&nbsp; <strong>EST tag</strong> = rate estimated from unit type</div>
        """, unsafe_allow_html=True)
        st.markdown("**Sample CSV format:**")
        st.dataframe(pd.DataFrame({
            "Item Description": ["M20 RCC Columns","Fe500 Reinforcement","230mm Brick Wall","Vitrified Floor Tiles","GI Ductwork","CPVC Pipe 25mm"],
            "Quantity":         [45.5, 2.8, 320.0, 850.0, 1200.0, 450.0],
            "Unit":             ["m³","MT","m³","m²","m²","RMT"],
            "Floor":            ["Basement","Ground","First Floor","First Floor","Second Floor","All Floors"],
            "Discipline":       ["Structure","Structure","Architecture","Architecture","MEP","MEP"]
        }), use_container_width=True)

    st.markdown("<hr class='ci-divider'>", unsafe_allow_html=True)

    # Config
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        project_type = st.selectbox("Project Type", PROJECT_TYPES)
    with c2:
        city = st.selectbox("Project City / Region", list(CITY_MULTIPLIERS.keys()))
    with c3:
        multiplier = CITY_MULTIPLIERS[city]
        st.markdown(f"""<br>
        <div style='background:rgba(0,255,100,0.04);border:1px solid rgba(0,255,100,0.15);
        border-radius:8px;padding:10px 12px;text-align:center;'>
        <div style='font-family:Syne,sans-serif;font-size:1.3rem;font-weight:800;color:#00FF64;'>{multiplier}x</div>
        <div style='font-family:JetBrains Mono,monospace;font-size:0.58rem;color:#1E3A5F;letter-spacing:1px;'>CITY FACTOR</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='ci-section-label'>Upload Quantity Takeoff CSV</div>", unsafe_allow_html=True)
    qty_file = st.file_uploader("Quantity CSV", type=["csv"], label_visibility="collapsed", key="cost_qty_upload")

    if qty_file:
        df = parse_quantity_csv(qty_file)
        if df is None:
            st.error("Could not parse CSV. Please check the file format.")
            return

        col_map = detect_columns(df)
        st.markdown(f"""
        <div style='font-family:JetBrains Mono,monospace;font-size:0.68rem;color:#00FF64;padding:6px 0;'>
        ✓ {len(df)} rows loaded &nbsp;·&nbsp; Columns: {', '.join(df.columns[:6])}{'...' if len(df.columns)>6 else ''}
        &nbsp;·&nbsp; Item="{col_map.get('item','?')}" Qty="{col_map.get('quantity','?')}"
        {'Floor="'+col_map['floor']+'"' if 'floor' in col_map else ''}
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Preview data"):
            st.dataframe(df.head(8), use_container_width=True)

        st.markdown("<hr class='ci-divider'>", unsafe_allow_html=True)

        if st.button("⚡ Run Cost Intelligence Analysis"):
            with st.spinner("Computing estimate and generating AI report..."):
                estimate  = compute_estimate(df, col_map, multiplier, project_type)
                ai_report = generate_ai_report(estimate, project_type, city)
                st.session_state["cost_estimate"]      = estimate
                st.session_state["cost_ai_report"]     = ai_report
                st.session_state["cost_city"]          = city
                st.session_state["cost_project_type"]  = project_type

    if "cost_estimate" in st.session_state:
        est = st.session_state["cost_estimate"]
        ai  = st.session_state["cost_ai_report"]

        st.markdown(f"""
        <div class='ci-stat-row'>
            <div class='ci-stat-card'><div class='ci-stat-value'>{fmt_inr(est['final_total'])}</div><div class='ci-stat-label'>Total Project Cost</div></div>
            <div class='ci-stat-card'><div class='ci-stat-value'>{fmt_inr(est['grand_total'])}</div><div class='ci-stat-label'>Base Estimate</div></div>
            <div class='ci-stat-card'><div class='ci-stat-value'>{est['item_count']}</div><div class='ci-stat-label'>BOQ Items</div></div>
            <div class='ci-stat-card'><div class='ci-stat-value'>{len(est['by_disc'])}</div><div class='ci-stat-label'>Disciplines</div></div>
            <div class='ci-stat-card'><div class='ci-stat-value' style='font-size:1rem;padding-top:4px;'>{st.session_state.get('cost_city','—')}</div><div class='ci-stat-label'>City</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='ci-total-row'>
            <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;'>
                <div>
                    <div class='ci-total-label'>Final Project Cost</div>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:#1E3A5F;'>
                    Base {fmt_inr(est['grand_total'])} + Contingency {fmt_inr(est['contingency'])} + Overheads {fmt_inr(est['overheads'])}</div>
                </div>
                <div class='ci-total-value'>{fmt_inr(est['final_total'])}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Cost Breakdown",
            "📋 Line Items",
            "🤖 AI Cost Report",
            "⬇️ Export"
        ])

        with tab1:
            render_discipline_bars(est["by_disc"], est["grand_total"])
            st.markdown("<hr class='ci-divider'>", unsafe_allow_html=True)
            render_floor_table(est["by_floor"])

        with tab2:
            render_line_items(est["rows"])

        with tab3:
            st.markdown(ai)

        with tab4:
            st.markdown("<div class='ci-section-label'>Export</div>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    "⬇️ Download Cost Estimate CSV",
                    data=export_estimate_csv(est),
                    file_name=f"NexBIM_CostEstimate_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv", key="dl_cost_csv"
                )
            with col_b:
                full_report = (
                    f"NEXBIM COST INTELLIGENCE REPORT\n"
                    f"Generated: {datetime.now().strftime('%B %d, %Y')}\n"
                    f"Project: {st.session_state.get('cost_project_type','')}\n"
                    f"City: {st.session_state.get('cost_city','')}\n\n"
                    f"TOTAL COST: {fmt_inr(est['final_total'])}\n"
                    f"Base: {fmt_inr(est['grand_total'])} | "
                    f"Contingency: {fmt_inr(est['contingency'])} | "
                    f"Overheads: {fmt_inr(est['overheads'])}\n\n"
                    f"BY DISCIPLINE:\n" +
                    "\n".join([f"{d}: {fmt_inr(v)}" for d, v in sorted(est["by_disc"].items(), key=lambda x: -x[1])]) +
                    f"\n\n{'='*50}\nAI COST INTELLIGENCE REPORT\n{'='*50}\n\n{ai}"
                )
                st.download_button(
                    "⬇️ Download Full Report TXT",
                    data=full_report,
                    file_name=f"NexBIM_CostReport_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain", key="dl_cost_txt"
                )

    elif not qty_file:
        st.markdown("""
        <div style='text-align:center;padding:60px 20px;'>
            <div style='font-family:Syne,sans-serif;font-size:3rem;color:#00FF64;opacity:0.12;margin-bottom:16px;'>₹</div>
            <div style='font-family:Syne,sans-serif;font-size:1.1rem;font-weight:700;color:#1E3A5F;margin-bottom:10px;'>Upload a Quantity Takeoff to Begin</div>
            <div style='font-family:Space Grotesk,sans-serif;font-size:0.83rem;color:#162840;line-height:2;'>
                "What will this G+7 building cost in Mumbai?"<br>
                "Is my MEP estimate too high for a commercial project?"<br>
                "Where can I save 10% without compromising quality?"
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center;font-family:JetBrains Mono,monospace;font-size:0.6rem;
    letter-spacing:1px;color:#0E1E30;margin-top:30px;padding-top:14px;
    border-top:1px solid rgba(255,255,255,0.03);'>
        NEXBIM COST INTELLIGENCE v1.0 · DEVENDRA GUPTA · CPWD DSR 2023-25 BASIS · BIM + AI + AUTOMATION
    </div>
    """, unsafe_allow_html=True)
