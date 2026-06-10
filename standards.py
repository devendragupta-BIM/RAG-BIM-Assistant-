import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

STANDARDS_DB = {
    "ISO 19650-1": {
        "full_name": "ISO 19650-1:2018 — Organization and digitization of information about buildings and civil engineering works",
        "category": "BIM Information Management",
        "region": "International",
        "description": "Defines concepts and principles for information management using BIM across the whole life cycle of a built asset.",
        "key_requirements": [
            "Information management framework for all project stages",
            "Defines roles: Appointing Party, Lead Appointed Party, Appointed Party",
            "Common Data Environment (CDE) requirements",
            "Information container naming conventions",
            "Structured information delivery process"
        ],
        "applies_to": ["All building types", "Infrastructure", "Civil works"],
        "related_standards": ["ISO 19650-2", "ISO 19650-3", "ISO 19650-5"],
        "year": "2018",
        "status": "Active"
    },
    "ISO 19650-2": {
        "full_name": "ISO 19650-2:2018 — Delivery phase of assets",
        "category": "BIM Information Management",
        "region": "International",
        "description": "Specifies requirements for information management during the delivery phase of assets using BIM.",
        "key_requirements": [
            "BIM Execution Plan requirements",
            "Master Information Delivery Plan",
            "Task Information Delivery Plan",
            "Information model delivery milestones",
            "Appointing party information requirements"
        ],
        "applies_to": ["New construction", "Renovation projects"],
        "related_standards": ["ISO 19650-1", "ISO 19650-3"],
        "year": "2018",
        "status": "Active"
    },
    "ISO 19650-3": {
        "full_name": "ISO 19650-3:2020 — Operational phase of assets",
        "category": "BIM Information Management",
        "region": "International",
        "description": "Specifies requirements for information management during the operational phase of assets.",
        "key_requirements": [
            "Asset information model requirements",
            "Trigger events for information updates",
            "Operations and maintenance information",
            "Asset information requirements",
            "Exchange information requirements"
        ],
        "applies_to": ["Building operations", "Facilities management", "Asset management"],
        "related_standards": ["ISO 19650-1", "ISO 19650-2"],
        "year": "2020",
        "status": "Active"
    },
    "ISO 19650-5": {
        "full_name": "ISO 19650-5:2020 — Security-minded approach to information management",
        "category": "BIM Security",
        "region": "International",
        "description": "Provides a security-minded approach to information management using BIM.",
        "key_requirements": [
            "Security threat assessment",
            "Sensitive information identification",
            "Security management plan",
            "Supply chain security requirements",
            "Information security protocols"
        ],
        "applies_to": ["All BIM projects", "Critical infrastructure", "Government buildings"],
        "related_standards": ["ISO 19650-1", "ISO 19650-2"],
        "year": "2020",
        "status": "Active"
    },
    "LOD Specification 2025": {
        "full_name": "Level of Development Specification Part I 2025",
        "category": "BIM Level of Development",
        "region": "International",
        "description": "BIMForum specification defining what BIM model elements should include at various stages of design and construction.",
        "key_requirements": [
            "LOD 100: Conceptual representation",
            "LOD 200: Approximate geometry and location",
            "LOD 300: Specific geometry and information",
            "LOD 350: Model element interfaces",
            "LOD 400: Fabrication and assembly detail",
            "LOD 500: As-built field verification"
        ],
        "applies_to": ["All building elements", "Infrastructure", "MEP systems"],
        "related_standards": ["ISO 19650-2", "AIA E203"],
        "year": "2025",
        "status": "Active"
    },
    "IFC 4.3": {
        "full_name": "ISO 16739-1:2018 — Industry Foundation Classes 4.3",
        "category": "BIM Data Exchange",
        "region": "International",
        "description": "Open international standard for BIM data exchange between software applications.",
        "key_requirements": [
            "Open BIM data format",
            "Software interoperability",
            "Geometry and property exchange",
            "Infrastructure and building support",
            "Classification and relationships"
        ],
        "applies_to": ["All BIM software", "Data exchange", "Open BIM workflows"],
        "related_standards": ["ISO 19650", "BCF 2.1"],
        "year": "2018",
        "status": "Active"
    },
    "BCF 2.1": {
        "full_name": "BIM Collaboration Format 2.1",
        "category": "BIM Collaboration",
        "region": "International",
        "description": "Open standard for communicating coordination issues in BIM workflows.",
        "key_requirements": [
            "Issue tracking in BIM models",
            "Camera position and viewpoints",
            "Markup and annotations",
            "Software neutral format",
            "Integration with IFC"
        ],
        "applies_to": ["BIM coordination", "Clash management", "Design review"],
        "related_standards": ["IFC 4.3", "ISO 19650"],
        "year": "2021",
        "status": "Active"
    },
    "COBie": {
        "full_name": "Construction Operations Building Information Exchange",
        "category": "BIM Handover",
        "region": "International",
        "description": "Standard for capturing and delivering asset data during construction for facility management.",
        "key_requirements": [
            "Facility and floor data",
            "Space and zone information",
            "Component and equipment data",
            "Systems and connections",
            "Spare parts and resources"
        ],
        "applies_to": ["Facilities management", "Asset management", "Handover"],
        "related_standards": ["ISO 19650-3", "IFC 4.3"],
        "year": "2017",
        "status": "Active"
    },
    "NBC India 2016": {
        "full_name": "National Building Code of India 2016",
        "category": "Building Codes",
        "region": "India",
        "description": "India comprehensive building code covering planning, design, and construction.",
        "key_requirements": [
            "Building planning and design",
            "Structural design requirements",
            "Fire and life safety",
            "Building services",
            "Constructional practices"
        ],
        "applies_to": ["All buildings in India", "Government projects"],
        "related_standards": ["IS codes", "BIS standards"],
        "year": "2016",
        "status": "Active"
    },
    "IS 456:2000": {
        "full_name": "IS 456:2000 — Plain and Reinforced Concrete Code of Practice",
        "category": "Structural Standards",
        "region": "India",
        "description": "Indian standard for design and construction of reinforced concrete structures.",
        "key_requirements": [
            "Concrete mix design",
            "Reinforcement detailing",
            "Structural analysis methods",
            "Durability requirements",
            "Quality control"
        ],
        "applies_to": ["RCC structures in India", "All concrete construction"],
        "related_standards": ["NBC India 2016", "IS 13920"],
        "year": "2000",
        "status": "Active"
    },
    "IS 13920:2016": {
        "full_name": "IS 13920:2016 — Ductile Design and Detailing of RCC Structures",
        "category": "Structural Standards",
        "region": "India",
        "description": "Indian standard for earthquake resistant design of reinforced concrete structures.",
        "key_requirements": [
            "Ductile detailing of beams",
            "Ductile detailing of columns",
            "Shear wall design",
            "Beam-column joints",
            "Seismic zone requirements"
        ],
        "applies_to": ["Buildings in seismic zones", "RCC structures"],
        "related_standards": ["IS 456", "IS 1893"],
        "year": "2016",
        "status": "Active"
    },
    "IS 1893:2016": {
        "full_name": "IS 1893:2016 — Criteria for Earthquake Resistant Design",
        "category": "Structural Standards",
        "region": "India",
        "description": "Indian standard for seismic design of buildings and structures.",
        "key_requirements": [
            "Seismic zone classification",
            "Design base shear calculation",
            "Response spectrum method",
            "Time history analysis",
            "Soil-structure interaction"
        ],
        "applies_to": ["All structures in India", "Seismic design"],
        "related_standards": ["IS 13920", "IS 456"],
        "year": "2016",
        "status": "Active"
    },
    "LEED v4.1": {
        "full_name": "Leadership in Energy and Environmental Design v4.1",
        "category": "Green Building",
        "region": "International",
        "description": "US Green Building Council certification program for sustainable buildings.",
        "key_requirements": [
            "Location and transportation",
            "Sustainable sites",
            "Water efficiency",
            "Energy and atmosphere",
            "Materials and resources",
            "Indoor environmental quality"
        ],
        "applies_to": ["Commercial buildings", "Residential", "Schools", "Healthcare"],
        "related_standards": ["ASHRAE 90.1", "BREEAM"],
        "year": "2019",
        "status": "Active"
    },
    "BREEAM": {
        "full_name": "Building Research Establishment Environmental Assessment Method",
        "category": "Green Building",
        "region": "International",
        "description": "Leading sustainability assessment method for buildings.",
        "key_requirements": [
            "Energy performance",
            "Water efficiency",
            "Materials sustainability",
            "Waste management",
            "Health and wellbeing"
        ],
        "applies_to": ["All building types", "Green building certification"],
        "related_standards": ["ISO 14001", "LEED"],
        "year": "1990",
        "status": "Active"
    },
    "GRIHA": {
        "full_name": "Green Rating for Integrated Habitat Assessment",
        "category": "Green Building",
        "region": "India",
        "description": "India national green building rating system developed by TERI.",
        "key_requirements": [
            "Site planning and design",
            "Building envelope optimization",
            "Building systems optimization",
            "Renewable energy",
            "Water management"
        ],
        "applies_to": ["Indian buildings", "Government projects"],
        "related_standards": ["NBC India 2016", "LEED"],
        "year": "2007",
        "status": "Active"
    },
    "ASHRAE 90.1": {
        "full_name": "ASHRAE 90.1 — Energy Standard for Buildings",
        "category": "Energy Standards",
        "region": "International",
        "description": "Energy efficiency standard for commercial buildings and high-rise residential.",
        "key_requirements": [
            "Building envelope requirements",
            "HVAC system efficiency",
            "Service water heating",
            "Power and lighting",
            "Energy cost budget method"
        ],
        "applies_to": ["Commercial buildings", "High-rise residential"],
        "related_standards": ["LEED", "IECC"],
        "year": "2019",
        "status": "Active"
    },
    "ISO 9001:2015": {
        "full_name": "ISO 9001:2015 — Quality Management Systems",
        "category": "Quality Management",
        "region": "International",
        "description": "International standard for quality management systems.",
        "key_requirements": [
            "Context of the organization",
            "Leadership and commitment",
            "Planning and risk management",
            "Support and resources",
            "Performance evaluation"
        ],
        "applies_to": ["All organizations", "Construction companies", "BIM practices"],
        "related_standards": ["ISO 14001", "ISO 45001"],
        "year": "2015",
        "status": "Active"
    },
    "ISO 14001:2015": {
        "full_name": "ISO 14001:2015 — Environmental Management Systems",
        "category": "Environmental Management",
        "region": "International",
        "description": "International standard for environmental management systems.",
        "key_requirements": [
            "Environmental policy",
            "Environmental aspects and impacts",
            "Legal compliance",
            "Objectives and targets",
            "Operational controls"
        ],
        "applies_to": ["Construction companies", "Project management"],
        "related_standards": ["ISO 9001", "ISO 45001"],
        "year": "2015",
        "status": "Active"
    },
    "ISO 45001:2018": {
        "full_name": "ISO 45001:2018 — Occupational Health and Safety",
        "category": "Health and Safety",
        "region": "International",
        "description": "International standard for occupational health and safety management systems.",
        "key_requirements": [
            "OH&S policy and objectives",
            "Hazard identification and risk assessment",
            "Legal and other requirements",
            "Emergency preparedness",
            "Incident investigation"
        ],
        "applies_to": ["Construction sites", "All organizations"],
        "related_standards": ["ISO 9001", "ISO 14001"],
        "year": "2018",
        "status": "Active"
    },
    "CPWD Specifications": {
        "full_name": "Central Public Works Department General Specifications",
        "category": "Construction Specifications",
        "region": "India",
        "description": "Indian government specifications for civil engineering works.",
        "key_requirements": [
            "Civil works specifications",
            "Electrical works specifications",
            "Material quality standards",
            "Workmanship standards",
            "Quality control procedures"
        ],
        "applies_to": ["Government buildings in India", "Public works"],
        "related_standards": ["NBC India 2016", "IS codes"],
        "year": "2019",
        "status": "Active"
    },
    "RIBA Plan of Work 2020": {
        "full_name": "RIBA Plan of Work 2020 — Royal Institute of British Architects",
        "category": "Project Delivery",
        "region": "United Kingdom",
        "description": "UK framework for organizing and managing the process of briefing, designing, and constructing buildings.",
        "key_requirements": [
            "Stage 0: Strategic Definition",
            "Stage 1: Preparation and Briefing",
            "Stage 2: Concept Design",
            "Stage 3: Spatial Coordination",
            "Stage 4: Technical Design",
            "Stage 5: Manufacturing and Construction",
            "Stage 6: Handover",
            "Stage 7: Use"
        ],
        "applies_to": ["UK architectural projects", "BIM project stages"],
        "related_standards": ["ISO 19650", "PAS 1192"],
        "year": "2020",
        "status": "Active"
    },
    "PAS 1192-2": {
        "full_name": "PAS 1192-2:2013 — Specification for information management for the capital delivery phase",
        "category": "BIM Information Management",
        "region": "United Kingdom",
        "description": "UK specification for information management for the capital delivery phase of construction projects.",
        "key_requirements": [
            "Employer Information Requirements",
            "BIM Execution Plan",
            "Master Information Delivery Plan",
            "BIM Protocol",
            "Data drops at project milestones"
        ],
        "applies_to": ["UK construction", "Government projects"],
        "related_standards": ["ISO 19650-2", "PAS 1192-3"],
        "year": "2013",
        "status": "Superseded by ISO 19650"
    },
    "Uniclass 2015": {
        "full_name": "Uniclass 2015 — Unified Classification for the Construction Industry",
        "category": "BIM Classification",
        "region": "United Kingdom",
        "description": "UK classification system for the construction industry used in BIM projects.",
        "key_requirements": [
            "Entities classification",
            "Activities classification",
            "Spaces classification",
            "Products classification",
            "Systems classification"
        ],
        "applies_to": ["UK BIM projects", "Asset management"],
        "related_standards": ["ISO 19650", "Omniclass"],
        "year": "2015",
        "status": "Active"
    },
    "OmniClass": {
        "full_name": "OmniClass Construction Classification System",
        "category": "BIM Classification",
        "region": "North America",
        "description": "North American classification system for the construction industry.",
        "key_requirements": [
            "Construction entities by function",
            "Construction entities by form",
            "Spaces by function",
            "Products",
            "Work results"
        ],
        "applies_to": ["North American BIM projects"],
        "related_standards": ["Uniclass", "MasterFormat"],
        "year": "2006",
        "status": "Active"
    },
    "MasterFormat 2020": {
        "full_name": "MasterFormat 2020 — Master List of Numbers and Titles",
        "category": "Construction Specification",
        "region": "North America",
        "description": "Standard for organizing construction specifications and cost data.",
        "key_requirements": [
            "General requirements",
            "Facility construction subgroup",
            "Facility services subgroup",
            "Site and infrastructure subgroup",
            "Process equipment subgroup"
        ],
        "applies_to": ["Construction specifications", "Cost estimating", "BIM data"],
        "related_standards": ["OmniClass", "UniFormat"],
        "year": "2020",
        "status": "Active"
    },
    "NFPA 101": {
        "full_name": "NFPA 101 — Life Safety Code",
        "category": "Fire Safety",
        "region": "International",
        "description": "Standard for life safety from fire in buildings and structures.",
        "key_requirements": [
            "Means of egress requirements",
            "Fire protection systems",
            "Interior finish requirements",
            "Detection and alarm systems",
            "Emergency lighting"
        ],
        "applies_to": ["All building types", "Fire safety design"],
        "related_standards": ["NFPA 13", "IBC"],
        "year": "2021",
        "status": "Active"
    },
    "ISO 55000": {
        "full_name": "ISO 55000:2014 — Asset Management Overview",
        "category": "Asset Management",
        "region": "International",
        "description": "International standard for asset management systems.",
        "key_requirements": [
            "Asset management policy",
            "Strategic asset management plan",
            "Asset management objectives",
            "Asset management plans",
            "Asset management system"
        ],
        "applies_to": ["Facilities management", "Infrastructure", "Asset lifecycle"],
        "related_standards": ["ISO 19650-3", "PAS 55"],
        "year": "2014",
        "status": "Active"
    },
    "SMACNA": {
        "full_name": "Sheet Metal and Air Conditioning Contractors National Association Standards",
        "category": "MEP Standards",
        "region": "International",
        "description": "Industry standards for HVAC duct construction and installation.",
        "key_requirements": [
            "Duct construction standards",
            "Seismic restraint requirements",
            "Hanger and support spacing",
            "Leakage testing requirements",
            "Installation quality standards"
        ],
        "applies_to": ["HVAC systems", "MEP coordination"],
        "related_standards": ["ASHRAE", "NFPA 90A"],
        "year": "2005",
        "status": "Active"
    },
    "openBIM Standards": {
        "full_name": "buildingSMART International — openBIM Standards",
        "category": "Open BIM",
        "region": "International",
        "description": "Suite of open international standards for BIM interoperability.",
        "key_requirements": [
            "IFC data format",
            "BCF collaboration format",
            "bSDD data dictionary",
            "Information delivery specifications",
            "Open BIM workflow"
        ],
        "applies_to": ["Multi-software BIM projects", "Open BIM workflows"],
        "related_standards": ["IFC 4.3", "ISO 19650"],
        "year": "2023",
        "status": "Active"
    },
    "MoHUA BIM Guidelines": {
        "full_name": "Ministry of Housing and Urban Affairs — BIM Guidelines India",
        "category": "BIM Standards",
        "region": "India",
        "description": "Indian government guidelines for BIM implementation in urban development projects.",
        "key_requirements": [
            "BIM implementation roadmap",
            "Software requirements",
            "Data standards",
            "Capacity building requirements",
            "Phased implementation plan"
        ],
        "applies_to": ["Urban development in India", "Smart cities", "AMRUT projects"],
        "related_standards": ["ISO 19650", "NBC India 2016"],
        "year": "2021",
        "status": "Active"
    },
    "RERA India": {
        "full_name": "Real Estate Regulatory Authority Act — Technical Standards",
        "category": "Legal Standards",
        "region": "India",
        "description": "Indian real estate regulatory standards for project delivery and documentation.",
        "key_requirements": [
            "Project registration requirements",
            "Drawing submission standards",
            "Construction timeline compliance",
            "Quality assurance requirements",
            "Handover documentation"
        ],
        "applies_to": ["Real estate projects in India", "Residential developments"],
        "related_standards": ["NBC India", "CPWD"],
        "year": "2016",
        "status": "Active"
    },
    "ISO 21500": {
        "full_name": "ISO 21500:2021 — Project Management Standard",
        "category": "Project Management",
        "region": "International",
        "description": "International standard for project management.",
        "key_requirements": [
            "Project initiation",
            "Project planning",
            "Project implementation",
            "Project control",
            "Project closure"
        ],
        "applies_to": ["All projects", "Construction projects"],
        "related_standards": ["PMBOK", "PRINCE2"],
        "year": "2021",
        "status": "Active"
    },
    "Navisworks Best Practices": {
        "full_name": "Autodesk Navisworks — BIM Coordination Best Practices",
        "category": "BIM Software Standards",
        "region": "International",
        "description": "Industry best practices for using Navisworks in BIM coordination.",
        "key_requirements": [
            "Model aggregation standards",
            "Clash detection workflow",
            "Clash review process",
            "TimeLiner 4D simulation",
            "Quantification setup"
        ],
        "applies_to": ["BIM coordination", "Clash detection", "4D planning"],
        "related_standards": ["ISO 19650", "BCF 2.1"],
        "year": "2024",
        "status": "Active"
    },
    "Dynamo Standards": {
        "full_name": "Autodesk Dynamo — Visual Programming Standards for BIM",
        "category": "BIM Automation",
        "region": "International",
        "description": "Best practice standards for Dynamo scripting in BIM workflows.",
        "key_requirements": [
            "Script documentation requirements",
            "Node naming conventions",
            "Error handling standards",
            "Performance optimization",
            "Version control for scripts"
        ],
        "applies_to": ["Revit automation", "BIM scripting", "Parametric design"],
        "related_standards": ["Revit Standards", "ISO 19650"],
        "year": "2023",
        "status": "Active"
    },
    "AIA E203": {
        "full_name": "AIA E203 — Building Information Modeling and Digital Data Exhibit",
        "category": "BIM Legal",
        "region": "United States",
        "description": "AIA contract document establishing protocols for BIM and digital data on projects.",
        "key_requirements": [
            "BIM and digital data protocols",
            "Authorized uses of models",
            "Model ownership and rights",
            "Reliance on model content",
            "Electronic data protocols"
        ],
        "applies_to": ["US architectural projects", "Legal BIM framework"],
        "related_standards": ["LOD Specification", "NBIMS"],
        "year": "2013",
        "status": "Active"
    },
    "FIDIC Red Book": {
        "full_name": "FIDIC Conditions of Contract for Construction",
        "category": "Contract Standards",
        "region": "International",
        "description": "International standard contract for construction projects.",
        "key_requirements": [
            "Employer requirements",
            "Contractor obligations",
            "Engineer role",
            "Payment provisions",
            "Dispute resolution"
        ],
        "applies_to": ["International construction contracts"],
        "related_standards": ["FIDIC Yellow Book", "NEC4"],
        "year": "2017",
        "status": "Active"
    },
    "NEC4": {
        "full_name": "New Engineering Contract 4th Edition",
        "category": "Contract Standards",
        "region": "International",
        "description": "Modern contract suite for engineering and construction projects.",
        "key_requirements": [
            "Early warning system",
            "Compensation events",
            "Programme requirements",
            "Collaborative working",
            "BIM integration"
        ],
        "applies_to": ["Engineering projects", "UK government projects"],
        "related_standards": ["FIDIC", "ISO 19650"],
        "year": "2017",
        "status": "Active"
    },
    "PWD India Standards": {
        "full_name": "Public Works Department — Schedule of Rates India",
        "category": "Cost Standards",
        "region": "India",
        "description": "Indian government schedule of rates for construction works.",
        "key_requirements": [
            "Civil works rates",
            "Electrical works rates",
            "Plumbing rates",
            "State-wise rate variations",
            "Annual rate revisions"
        ],
        "applies_to": ["Government projects in India", "Cost estimation"],
        "related_standards": ["CPWD Specifications", "NBC India"],
        "year": "2023",
        "status": "Active"
    },
    "SP 7 India": {
        "full_name": "SP 7 National Building Code of India Part 6 Structural Design",
        "category": "Structural Standards",
        "region": "India",
        "description": "Indian standard for structural design requirements in buildings.",
        "key_requirements": [
            "Loads on structures",
            "Foundation design",
            "RCC design",
            "Steel structure design",
            "Masonry design"
        ],
        "applies_to": ["All structures in India"],
        "related_standards": ["IS 456", "NBC India 2016"],
        "year": "2016",
        "status": "Active"
    },
    "BIM for Infrastructure": {
        "full_name": "ISO 19650 Application to Infrastructure Projects",
        "category": "Infrastructure BIM",
        "region": "International",
        "description": "Guidelines for applying ISO 19650 to infrastructure and civil engineering projects.",
        "key_requirements": [
            "Infrastructure information model",
            "Linear assets management",
            "GIS integration requirements",
            "Survey and geospatial data",
            "Asset lifecycle management"
        ],
        "applies_to": ["Roads", "Bridges", "Railways", "Utilities"],
        "related_standards": ["ISO 19650", "IFC 4.3"],
        "year": "2022",
        "status": "Active"
    },
    "ISO 29481": {
        "full_name": "ISO 29481 — Building Information Modelling Information Delivery Manual",
        "category": "BIM Information Management",
        "region": "International",
        "description": "Standard for information delivery in BIM projects.",
        "key_requirements": [
            "Process map requirements",
            "Exchange requirements",
            "Information delivery specification",
            "Functional parts definition",
            "Actor definition"
        ],
        "applies_to": ["BIM information management", "Data exchange planning"],
        "related_standards": ["ISO 19650", "IFC"],
        "year": "2016",
        "status": "Active"
    },
    "CIC BIM Protocol": {
        "full_name": "Construction Industry Council BIM Protocol",
        "category": "BIM Legal",
        "region": "United Kingdom",
        "description": "UK legal protocol for BIM projects defining rights and responsibilities.",
        "key_requirements": [
            "BIM obligations of parties",
            "Permitted purposes for models",
            "Information requirements",
            "Model production schedule",
            "Legal framework for BIM"
        ],
        "applies_to": ["UK BIM contracts", "Legal BIM framework"],
        "related_standards": ["ISO 19650", "PAS 1192"],
        "year": "2018",
        "status": "Active"
    },
    "NBIMS-US V3": {
        "full_name": "National BIM Standard United States Version 3",
        "category": "BIM Standards",
        "region": "United States",
        "description": "US national standard for BIM practice and implementation.",
        "key_requirements": [
            "BIM minimum modeling matrix",
            "Information delivery manual",
            "Interactive capability maturity model",
            "Reference standards",
            "Practice documents"
        ],
        "applies_to": ["US construction projects", "Government projects"],
        "related_standards": ["IFC", "COBie", "OmniClass"],
        "year": "2015",
        "status": "Active"
    },
    "EN 15221": {
        "full_name": "EN 15221 — Facility Management European Standard",
        "category": "Facilities Management",
        "region": "Europe",
        "description": "European standard for facility management.",
        "key_requirements": [
            "FM terms and definitions",
            "Guidance on FM agreements",
            "Guidance on quality in FM",
            "FM taxonomy",
            "Performance measurement"
        ],
        "applies_to": ["European FM projects", "Asset management"],
        "related_standards": ["ISO 55000", "ISO 19650-3"],
        "year": "2011",
        "status": "Active"
    },
    "Revit BIM Template Standards": {
        "full_name": "Autodesk Revit BIM Template and Family Standards",
        "category": "BIM Software Standards",
        "region": "International",
        "description": "Standards for creating and managing Revit templates and families.",
        "key_requirements": [
            "Project template requirements",
            "Family naming conventions",
            "Parameter standards",
            "View template requirements",
            "Shared parameter files"
        ],
        "applies_to": ["Revit projects", "BIM team setup"],
        "related_standards": ["LOD Specification", "ISO 19650"],
        "year": "2024",
        "status": "Active"
    },
    "ISO 16739": {
        "full_name": "ISO 16739-1:2018 — Industry Foundation Classes for Data Sharing",
        "category": "BIM Data Exchange",
        "region": "International",
        "description": "International standard defining IFC schema for BIM data exchange.",
        "key_requirements": [
            "IFC schema definition",
            "Geometry representation",
            "Property sets",
            "Relationship definitions",
            "Classification references"
        ],
        "applies_to": ["All BIM software", "Data exchange"],
        "related_standards": ["ISO 19650", "BCF"],
        "year": "2018",
        "status": "Active"
    },
    "AISC Standards": {
        "full_name": "American Institute of Steel Construction Standards",
        "category": "Structural Standards",
        "region": "United States",
        "description": "Standards for design and construction of steel structures.",
        "key_requirements": [
            "Load and resistance factor design",
            "Allowable strength design",
            "Seismic provisions",
            "Connection design",
            "BIM for steel fabrication"
        ],
        "applies_to": ["Steel structures", "Structural BIM"],
        "related_standards": ["ASTM", "AWS"],
        "year": "2022",
        "status": "Active"
    },
    "BIEN India BIM Guidelines": {
        "full_name": "BIM Excellence India Network National BIM Guidelines",
        "category": "BIM Standards",
        "region": "India",
        "description": "India national BIM guidelines for government and public sector projects.",
        "key_requirements": [
            "BIM mandate for government projects",
            "LOD requirements for Indian projects",
            "Software interoperability",
            "Data handover requirements",
            "Training and capacity building"
        ],
        "applies_to": ["Indian government projects", "Smart city projects"],
        "related_standards": ["ISO 19650", "NBC India"],
        "year": "2019",
        "status": "Active"
    },
    "RERA India": {
        "full_name": "Real Estate Regulatory Authority Act Technical Standards",
        "category": "Legal Standards",
        "region": "India",
        "description": "Indian real estate regulatory standards for project delivery.",
        "key_requirements": [
            "Project registration requirements",
            "Drawing submission standards",
            "Construction timeline compliance",
            "Quality assurance requirements",
            "Handover documentation"
        ],
        "applies_to": ["Real estate projects in India"],
        "related_standards": ["NBC India", "CPWD"],
        "year": "2016",
        "status": "Active"
    },
}

CATEGORIES = sorted(list(set(v["category"] for v in STANDARDS_DB.values())))
REGIONS = sorted(list(set(v["region"] for v in STANDARDS_DB.values())))

def show_standards_library():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

    .nex-lib-hero {
        background: linear-gradient(135deg, #050D1A 0%, #0A1628 100%);
        border: 1px solid rgba(0,255,178,0.2);
        border-radius: 20px;
        padding: 32px 36px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .nex-lib-hero::before {
        content: '';
        position: absolute;
        top: -40%; right: -10%;
        width: 400px; height: 400px;
        background: radial-gradient(circle,
            rgba(0,255,178,0.06) 0%, transparent 70%);
    }
    .nex-lib-title {
        font-family: 'Syne', sans-serif;
        font-size: 2rem; font-weight: 800;
        color: #FFFFFF; margin: 0 0 6px 0;
        letter-spacing: -0.5px;
    }
    .nex-lib-title span { color: #00FFB2; }
    .nex-lib-sub {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.9rem; color: #4A6A8A; margin: 0;
    }
    .nex-lib-stats {
        display: flex; gap: 12px;
        margin-top: 16px; flex-wrap: wrap;
    }
    .nex-lib-stat {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem; color: #00FFB2;
        background: rgba(0,255,178,0.08);
        border: 1px solid rgba(0,255,178,0.2);
        padding: 4px 12px; border-radius: 4px;
    }
    .nex-std-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px; padding: 16px;
        margin-bottom: 10px;
    }
    .nex-std-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem; color: #00FFB2;
        letter-spacing: 1px; margin-bottom: 4px;
    }
    .nex-std-name {
        font-family: 'Syne', sans-serif;
        font-size: 0.95rem; font-weight: 700;
        color: #E0F0FF; margin-bottom: 6px;
        line-height: 1.3;
    }
    .nex-std-desc {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.82rem; color: #4A6A8A;
        line-height: 1.5; margin-bottom: 10px;
    }
    .nex-std-tags {
        display: flex; gap: 6px; flex-wrap: wrap;
    }
    .nex-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem; padding: 2px 8px;
        border-radius: 4px; letter-spacing: 0.5px;
    }
    .nex-tag-cat {
        background: rgba(0,212,255,0.1);
        color: #00D4FF;
        border: 1px solid rgba(0,212,255,0.2);
    }
    .nex-tag-region {
        background: rgba(255,107,107,0.1);
        color: #FF6B6B;
        border: 1px solid rgba(255,107,107,0.2);
    }
    .nex-tag-year {
        background: rgba(255,217,61,0.1);
        color: #FFD93D;
        border: 1px solid rgba(255,217,61,0.2);
    }
    .nex-tag-active {
        background: rgba(0,255,178,0.1);
        color: #00FFB2;
        border: 1px solid rgba(0,255,178,0.2);
    }
    .nex-tag-super {
        background: rgba(150,150,150,0.1);
        color: #888888;
        border: 1px solid rgba(150,150,150,0.2);
    }
    .nex-detail-card {
        background: linear-gradient(135deg,
            rgba(0,255,178,0.03) 0%,
            rgba(0,150,255,0.02) 100%);
        border: 1px solid rgba(0,255,178,0.15);
        border-radius: 16px; padding: 24px;
        margin-bottom: 16px;
    }
    .nex-detail-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.3rem; font-weight: 800;
        color: #00FFB2; margin-bottom: 4px;
    }
    .nex-detail-fullname {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.85rem; color: #4A6A8A;
        margin-bottom: 14px; line-height: 1.5;
    }
    .nex-req-item {
        display: flex; gap: 10px;
        align-items: flex-start; padding: 7px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.85rem; color: #A0B4C8;
    }
    .nex-req-item:last-child { border-bottom: none; }
    .nex-req-bullet {
        color: #00FFB2; font-size: 0.65rem;
        margin-top: 4px; flex-shrink: 0;
    }
    .nex-section-mini {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem; color: #00FFB2;
        letter-spacing: 2px; text-transform: uppercase;
        margin: 14px 0 6px 0;
    }
    .nex-applies-text {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.85rem; color: #4A6A8A;
        line-height: 1.6;
    }
    .nex-ai-box {
        background: rgba(0,255,178,0.02);
        border: 1px solid rgba(0,255,178,0.1);
        border-left: 3px solid #00FFB2;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px; margin-top: 12px;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.88rem; color: #A0B4C8;
        line-height: 1.7;
    }
    .nex-filter-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem; color: #1E3A5F;
        letter-spacing: 2px; text-transform: uppercase;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    total = len(STANDARDS_DB)
    active = sum(1 for v in STANDARDS_DB.values() if v["status"] == "Active")

    st.markdown(f"""
    <div class='nex-lib-hero'>
        <div style='font-family:JetBrains Mono,monospace;
        font-size:0.68rem; color:#00FFB2;
        letter-spacing:3px; margin-bottom:12px;'>
        ◈ NEXBIM STANDARDS LIBRARY</div>
        <div class='nex-lib-title'>
            BIM + Construction <span>Standards</span>
        </div>
        <p class='nex-lib-sub'>
            {total} international standards covering BIM, structural,
            MEP, green building, legal, and Indian codes.
            All searchable and AI-queryable.
        </p>
        <div class='nex-lib-stats'>
            <div class='nex-lib-stat'>{total} Standards</div>
            <div class='nex-lib-stat'>{active} Active</div>
            <div class='nex-lib-stat'>{len(CATEGORIES)} Categories</div>
            <div class='nex-lib-stat'>{len(REGIONS)} Regions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns([3, 2, 2])
    with col_f1:
        search_query = st.text_input(
            "Search",
            placeholder="Search by name, category, or keyword...",
            label_visibility="collapsed",
            key="std_search"
        )
    with col_f2:
        cat_filter = st.selectbox(
            "Category",
            ["All Categories"] + CATEGORIES,
            label_visibility="collapsed",
            key="std_cat"
        )
    with col_f3:
        region_filter = st.selectbox(
            "Region",
            ["All Regions"] + REGIONS,
            label_visibility="collapsed",
            key="std_region"
        )

    filtered = {}
    for std_id, std_data in STANDARDS_DB.items():
        if cat_filter != "All Categories" and \
                std_data["category"] != cat_filter:
            continue
        if region_filter != "All Regions" and \
                std_data["region"] != region_filter:
            continue
        if search_query:
            searchable = (
                std_id.lower() +
                std_data["full_name"].lower() +
                std_data["description"].lower() +
                std_data["category"].lower() +
                " ".join(std_data["key_requirements"]).lower()
            )
            if search_query.lower() not in searchable:
                continue
        filtered[std_id] = std_data

    st.markdown(f"""
    <div class='nex-filter-label'>
    Showing {len(filtered)} of {total} standards
    </div>
    """, unsafe_allow_html=True)

    if not filtered:
        st.markdown("""
        <div style='text-align:center; padding:40px;
        color:#1E3A5F; font-family:Space Grotesk,sans-serif;'>
            No standards found. Try a different search or filter.
        </div>
        """, unsafe_allow_html=True)
        return

    selected_std = st.selectbox(
        "Select a standard to explore",
        ["— Select a standard to explore in detail —"] +
        list(filtered.keys()),
        label_visibility="collapsed",
        key="std_select"
    )

    if selected_std != "— Select a standard to explore in detail —":
        std = STANDARDS_DB[selected_std]
        status_tag = "nex-tag-active" if std["status"] == "Active" \
            else "nex-tag-super"

        req_html = "".join([
            f"<div class='nex-req-item'>"
            f"<span class='nex-req-bullet'>◆</span>{req}</div>"
            for req in std["key_requirements"]
        ])

        st.markdown(f"""
        <div class='nex-detail-card'>
            <div class='nex-detail-title'>{selected_std}</div>
            <div class='nex-detail-fullname'>{std['full_name']}</div>
            <div style='font-family:Space Grotesk,sans-serif;
            font-size:0.9rem; color:#A0B4C8;
            margin-bottom:14px; line-height:1.6;'>
            {std['description']}</div>
            <div class='nex-std-tags' style='margin-bottom:16px;'>
                <span class='nex-tag nex-tag-cat'>{std['category']}</span>
                <span class='nex-tag nex-tag-region'>{std['region']}</span>
                <span class='nex-tag nex-tag-year'>{std['year']}</span>
                <span class='nex-tag {status_tag}'>{std['status']}</span>
            </div>
            <div class='nex-section-mini'>Key Requirements</div>
            {req_html}
            <div class='nex-section-mini' style='color:#00D4FF;'>
            Applies To</div>
            <div class='nex-applies-text'>
            {' &nbsp;·&nbsp; '.join(std['applies_to'])}</div>
            <div class='nex-section-mini' style='color:#FFD93D;'>
            Related Standards</div>
            <div class='nex-applies-text'>
            {' &nbsp;·&nbsp; '.join(std['related_standards'])}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='nex-section-mini'>Ask AI About This Standard</div>
        """, unsafe_allow_html=True)

        ai_q = st.text_input(
            "AI Question",
            placeholder=f"Ask anything about {selected_std}...",
            label_visibility="collapsed",
            key="std_ai_q"
        )

        if st.button("Ask NexBIM AI →", key="std_ai_btn"):
            if ai_q:
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                with st.spinner(""):
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{
                            "role": "user",
                            "content": f"""You are NexBIM, an expert BIM
consultant with deep knowledge of international construction standards.

Answer this question about {selected_std}:
Full name: {std['full_name']}
Description: {std['description']}
Key Requirements: {', '.join(std['key_requirements'])}

Question: {ai_q}

Give a detailed, practical, and accurate answer with real examples
relevant to construction and BIM projects."""
                        }],
                        max_tokens=1000
                    )
                answer = resp.choices[0].message.content
                st.markdown(f"""
                <div class='nex-ai-box'>
                {answer.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Please type a question first.")

    st.markdown("""
    <div style='margin-top:28px;'>
    <div class='nex-section-mini'>All Standards</div>
    </div>
    """, unsafe_allow_html=True)

    for std_id, std_data in filtered.items():
        status_tag = "nex-tag-active" if std_data["status"] == "Active" \
            else "nex-tag-super"
        st.markdown(f"""
        <div class='nex-std-card'>
            <div class='nex-std-id'>{std_id}</div>
            <div class='nex-std-name'>
                {std_data['full_name'][:65]}
                {'...' if len(std_data['full_name']) > 65 else ''}
            </div>
            <div class='nex-std-desc'>
                {std_data['description'][:110]}...
            </div>
            <div class='nex-std-tags'>
                <span class='nex-tag nex-tag-cat'>
                {std_data['category']}</span>
                <span class='nex-tag nex-tag-region'>
                {std_data['region']}</span>
                <span class='nex-tag nex-tag-year'>
                {std_data['year']}</span>
                <span class='nex-tag {status_tag}'>
                {std_data['status']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; margin-top:20px;
    font-family:JetBrains Mono,monospace;
    font-size:0.6rem; color:#0E1E30; letter-spacing:1px;'>
        NEXBIM STANDARDS LIBRARY · 50+ STANDARDS ·
        BUILT BY DEVENDRA GUPTA
    </div>
    """, unsafe_allow_html=True)