import streamlit as st
import requests
import json

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Resume Rank Checker",
    page_icon="📄",
    layout="centered",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

h1, h2, h3 { font-family: 'Sora', sans-serif !important; }

.hero-title {
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.2rem;
}

.hero-sub {
    text-align: center;
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 2rem;
    font-weight: 300;
}

.card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 2rem;
    backdrop-filter: blur(10px);
}

.score-ring {
    text-align: center;
    margin: 1.5rem 0;
}

.score-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 4rem;
    font-weight: 600;
    line-height: 1;
}

.score-strong  { color: #34d399; }
.score-moderate { color: #fbbf24; }
.score-weak    { color: #f87171; }

.score-label-badge {
    display: inline-block;
    padding: 0.3rem 1rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-top: 0.5rem;
}

.badge-strong   { background: rgba(52,211,153,0.2); color: #34d399; border: 1px solid #34d399; }
.badge-moderate { background: rgba(251,191,36,0.2);  color: #fbbf24; border: 1px solid #fbbf24; }
.badge-weak     { background: rgba(248,113,113,0.2); color: #f87171; border: 1px solid #f87171; }

.metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    font-size: 0.9rem;
    color: #cbd5e1;
}

.metric-val {
    font-family: 'JetBrains Mono', monospace;
    color: #a78bfa;
    font-weight: 600;
}

.tip-item {
    background: rgba(96,165,250,0.08);
    border-left: 3px solid #60a5fa;
    border-radius: 0 8px 8px 0;
    padding: 0.6rem 0.9rem;
    margin: 0.4rem 0;
    font-size: 0.88rem;
    color: #cbd5e1;
}

.warn-box {
    background: rgba(251,191,36,0.1);
    border: 1px solid rgba(251,191,36,0.4);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    color: #fbbf24;
    font-size: 0.88rem;
    margin-bottom: 1rem;
}

.pill {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0.15rem;
}

.pill-found   { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.4); }
.pill-missing { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.4); }

.stSelectbox label, .stFileUploader label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

div[data-testid="stFileUploader"] {
    border: 2px dashed rgba(167,139,250,0.4) !important;
    border-radius: 12px !important;
    background: rgba(167,139,250,0.05) !important;
}

.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.75rem;
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: opacity 0.2s;
    margin-top: 0.5rem;
}
.stButton > button:hover { opacity: 0.88; }

.section-title {
    color: #94a3b8;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 1.2rem 0 0.6rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Company Data (hidden from user) ─────────────────────────────────────────

COMPANY_DATA = {
    "Acsia Technologies": { "roles": ["Embedded Software Engineer", "Android Framework Engineer", "Cybersecurity Engineer"], "desc": "Develops automotive infotainment and ADAS software. Roles include AOSP/HAL/Sepolicy, C++17/20 on Yocto Linux, LIN protocol embedded systems, and automotive cybersecurity with QNX and Secure Boot.", "tech": ["Embedded C", "C++", "Linux", "RTOS", "AOSP", "Yocto", "CMake", "QNX", "Cryptography", "Microcontrollers"], "min_cgpa": 7.0, "eligibility": "70% or 7.0 CGPA; No active backlogs" },
    "Asimov Robotics": { "roles": ["Robotics Software Engineer", "Computer Vision Engineer", "Data Science Intern"], "desc": "Algorithms for autonomous navigation, computer vision, robotic control using ROS1/ROS2, SLAM, motion planning, sensor fusion with LiDAR/IMU.", "tech": ["Python", "C++", "ROS", "OpenCV", "SLAM", "AI", "ML", "Sensor Fusion", "Deep Learning"], "min_cgpa": 7.0, "eligibility": "7.0+ CGPA; Strong project portfolio in Robotics/AI" },
    "CareStack": { "roles": ["Senior Engineer", "Site Reliability Engineer", "Product Engineer"], "desc": "Cloud-based SaaS platform for dental practice management using .NET Core, Angular 2+, SQL Server with high code quality and refactoring.", "tech": ["C#", ".NET Core", "Angular", "React", "SQL Server", "OOPS", "Web APIs", "Cloud Infrastructure"], "min_cgpa": 7.0, "eligibility": "7.0+ CGPA; Computer Science/IT background" },
    "Cognizant": { "roles": ["Analyst Trainee GenC", "Prompt Engineer", "Stibo MDM Developer"], "desc": "Software development, testing, data analytics for global clients. GenC: Data Analytics, Software Testing, SQL, SDLC. Also Prompt Engineers for LLM fine-tuning.", "tech": ["Java", "Python", "SQL", "HTML", "CSS", "Data Analytics", "Software Testing", "SDLC"], "min_cgpa": 6.0, "eligibility": "60% or 6.0 CGPA; All branches eligible" },
    "E.Y (Ernst & Young)": { "roles": ["Technology Consultant", "SAP GRC Architect", "ServiceNow Staff"], "desc": "Digital transformation, tech risk assessment, enterprise solutions. SAP GRC risk consulting, regulatory policy, US tax analysis, and ServiceNow TechOps.", "tech": ["Data Analytics", "SQL", "Python", "PowerBI", "Cybersecurity", "Cloud", "SAP GRC", "ServiceNow"], "min_cgpa": 7.0, "eligibility": "70% or 7.0 CGPA; Excellent communication skills" },
    "ENVESTNET": { "roles": ["Senior Salesforce Developer", "Associate Lead Engineer", "Senior Architect"], "desc": "High-performance financial software and wealth management tools. Salesforce LWC/Apex, .NET/Java Springboot for quantitative wealth tools, high-throughput fintech systems.", "tech": ["Java", "Spring Boot", "Data Structures", "Algorithms", "Microservices", "SQL", ".NET", "Salesforce", "Angular"], "min_cgpa": 7.0, "eligibility": "7.0+ CGPA; Strong problem-solving skills" },
    "Equifax": { "roles": ["Software Engineer Java", "Site Reliability Engineer", "UI Developer", "Quality Engineer"], "desc": "Large-scale data systems and credit reporting tools. SRE cloud ops, Java SpringBoot microservices on GCP/AWS, Angular 17 UI, Selenium/Cucumber QA.", "tech": ["Java", "Python", "SQL", "Big Data", "Spring Boot", "GCP", "AWS", "Angular", "Selenium", "CI/CD"], "min_cgpa": 7.0, "eligibility": "7.0+ CGPA; B.Tech CS/IT/ECE preferred" },
    "Experion Technologies": { "roles": ["Lead Developer", "BI Architect", "Project Manager", "UX Designer"], "desc": "Custom software for retail and healthcare clients. ASP.NET Core, Angular, SQL Server, Azure. Power BI/Tableau for BI. Agile/Scrum project management.", "tech": ["React", "Node.js", ".NET", "Python", "Power BI", "Tableau", "Azure", "Agile", "CI/CD", "Angular"], "min_cgpa": 6.5, "eligibility": "6.5+ CGPA; Good understanding of SDLC" },
    "Guidehouse": { "roles": ["Senior Associate Revenue Cycle", "Solutions Architect", "Financial Compliance"], "desc": "Technology consulting for public sector and healthcare. Epic EHR expertise, revenue cycle streamlining, healthcare cost estimation and financial modeling.", "tech": ["SQL", "Cloud Computing", "AWS", "Azure", "Data Visualization", "Epic EHR", "Financial Modeling"], "min_cgpa": 6.5, "eligibility": "6.5+ CGPA; Strong documentation skills" },
    "H&R Block": { "roles": ["Sr Software Engineer", "UI Developer", "Tax Professional"], "desc": "Financial and tax software. GitHub Enterprise administration, Azure DevOps, Angular 10+, TypeScript, Node.js with Agile Scrum.", "tech": ["C#", ".NET", "Java", "Angular", "TypeScript", "Node.js", "GitHub", "Azure DevOps", "SQL", "Python"], "min_cgpa": 7.0, "eligibility": "7.0+ CGPA; CS/IT/ECE branches" },
    "HostDime": { "roles": ["Deployment Technician", "System Technician"], "desc": "Global Tier IV data center infrastructure. Server decommissioning, hardware upgrades, monitoring, troubleshooting.", "tech": ["Linux", "Unix", "Networking", "TCP/IP", "DNS", "Apache", "Nginx", "Hardware"], "min_cgpa": 6.0, "eligibility": "6.0+ CGPA; Interest in infrastructure and networking" },
    "IBM": { "roles": ["Consulting Associate", "Software Engineer (Fresher)", "Security Specialist"], "desc": "Cloud transformation with Red Hat/IBM. Fresher SWE: Full Stack, Java 8, Python, REST APIs, Microservices, CI/CD, AI-powered cloud-native solutions. SOC security.", "tech": ["Java", "Python", "C++", "Cloud", "DBMS", "REST APIs", "Microservices", "CI/CD", "Security"], "min_cgpa": 6.5, "eligibility": "6.5+ CGPA; No active backlogs" },
    "InApp": { "roles": ["MERN Stack Developer", "Tech Lead Python", "Data Warehouse Expert"], "desc": "Web and mobile apps for international clients. MERN stack, AI-enabled Python cloud engineering, scalable data transformation with dbt.", "tech": ["Java", "Python", "JavaScript", "MongoDB", "React", "Node.js", "OOPS", "DBMS", "Cloud"], "min_cgpa": 6.5, "eligibility": "6.5+ CGPA; Strong coding fundamentals" },
    "Infosys": { "roles": ["Systems Engineer", "Data Analyst", "Rust Developer", "Java SpringBoot Developer"], "desc": "End-to-end IT services for global business. Fresher data analytics with Pentaho/Python/ML, Rust for entertainment backends, Java SpringBoot enterprise apps.", "tech": ["Java", "Python", "C#", "DBMS", "Machine Learning", "Data Analytics", "Spring Boot"], "min_cgpa": 6.0, "eligibility": "60% in 10th/12th/B.Tech; All branches" },
    "Litmus7": { "roles": ["UI Architect", "OMS Lead", "Python API Developer", "NI Quality Engineer"], "desc": "Scalable e-commerce and retail technology. React/TypeScript UI architecture, Blue Yonder/Manhattan OMS with Java Springboot on AWS/Azure, AI-driven QA.", "tech": ["Java", "Spring", "Data Structures", "Algorithms", "React", "TypeScript", "Python", "AWS", "Azure"], "min_cgpa": 7.0, "eligibility": "7.0+ CGPA; Problem-solving focus" },
    "Mitsogo": { "roles": ["Lead Windows Developer", "Endpoint System Engineer", "UI/UX Design Lead"], "desc": "Enterprise mobility and endpoint management (Hexnode). Windows system/kernel-level C++ for security products.", "tech": ["C", "C++", "Java", "Advanced Data Structures", "Algorithms", "Operating Systems", "Windows", "Security"], "min_cgpa": 0.0, "eligibility": "No strict CGPA; Heavily dependent on coding performance" },
    "Nissan Digital": { "roles": ["Software Engineer II", "Senior Python Engineer", "Senior Business Analyst"], "desc": "Automotive digital transformation — IoT, connected cars, electrification. Intelligent automation, cloud-native AI solutions, global delivery.", "tech": ["Java", "Python", "Cloud Computing", "AI", "ML", "Data Science", "IoT", "Automation"], "min_cgpa": 7.0, "eligibility": "7.0+ CGPA; Passion for automotive tech" },
    "Qspiders": { "roles": ["Trainee Engineer", "Quality Analyst", "Test Automation Lead", "BFSI Trainer"], "desc": "Software testing (manual and automation). QA tests, test plan design, defect management, BFSI training for banking/financial content.", "tech": ["Manual Testing", "Selenium", "Java", "Python", "SQL", "Test Automation", "Excel"], "min_cgpa": 6.0, "eligibility": "6.0+ CGPA; Open to all engineering branches" },
    "Quantiphi": { "roles": ["ML Architect", "Agentic AI Program Manager", "ML Engineer"], "desc": "AI-driven solutions, data pipelines, ML models. Agentic AI with RAG and multinode decision models, domain adaptive ML engineering.", "tech": ["Python", "SQL", "Machine Learning", "Deep Learning", "Hadoop", "Spark", "RAG", "LLM", "Big Data"], "min_cgpa": 7.0, "eligibility": "7.0+ CGPA; Strong mathematical background" },
    "Reflections Info Systems": { "roles": ["Senior .NET Developer", "SharePoint Lead", "Salesforce QA", "Delivery Manager"], "desc": "Digital solutions across modern platforms. .NET Core 6/8, Microservices, Azure Functions, Clean Architecture, DDD, CQRS. SharePoint SPFx, Power Automate.", "tech": ["Java", "JavaScript", "Angular", "React", ".NET Core", "Azure", "SharePoint", "Salesforce", "Microservices"], "min_cgpa": 6.5, "eligibility": "6.5+ CGPA; Strong logic skills" },
    "SIB (South Indian Bank)": { "roles": ["IT Officer", "Junior Officer Business Promotion", "Probationary Officer CMA"], "desc": "Banking software management, cybersecurity, digital infrastructure. Retail sales, internal audit, cost management.", "tech": ["Aptitude", "Networking", "DBMS", "Banking Software", "Cybersecurity", "Financial Services"], "min_cgpa": 6.0, "eligibility": "60% throughout; B.Tech CS/IT/ECE/EEE" },
    "Simplogics": { "roles": ["Lead Java Developer", "Lead React JS Developer", "Database Administrator"], "desc": "Custom web and enterprise application development. Java delivery focus, React enterprise UI architecture, database infrastructure management.", "tech": ["JavaScript", "HTML", "CSS", "Node.js", "Python", "Java", "React", "OOPS", "SQL"], "min_cgpa": 6.5, "eligibility": "6.5+ CGPA; Portfolio of web projects preferred" },
    "Speridian Technologies": { "roles": ["Manual Testing Lead", "Snowflake Developer", "Angular Developer", "Product Designer"], "desc": "Digital transformation and CRM enterprise modernization. Manual testing QA lead, Snowflake + Azure Data Factory, Angular development.", "tech": ["Java", "JavaScript", "Oracle", "SQL", "Angular", "Snowflake", "Azure Data Factory", "Manual Testing"], "min_cgpa": 6.5, "eligibility": "6.5+ CGPA; Strong communication" },
    "Suntec": { "roles": ["Associate Inside Sales", "Technical Trainer"], "desc": "Revenue management and billing software for banking, telecom, and travel. B2B lead generation, technical training for banking products.", "tech": ["Java", "C++", "Data Structures", "SQL", "Problem-solving", "Banking Domain", "Communication"], "min_cgpa": 7.0, "eligibility": "7.0+ CGPA; CS/IT branches" },
    "Taomish": { "roles": ["Software Engineer III", "Senior QA Engineer", "Support Manager"], "desc": "SaaS products for supply chain and commodity management. Java/Spring-Boot/Angular with Docker, CI/CD, AWS/GCP. Manual QA for ERP and financial domains.", "tech": ["Java", "Python", "OOPS", "Spring Boot", "Angular", "Docker", "CI/CD", "AWS", "Manual Testing"], "min_cgpa": 6.5, "eligibility": "6.5+ CGPA; Strong analytical skills" },
    "U.S.T": { "roles": ["Lead II Python", "SAP S/4HANA Lead", "Business Analyst", "SOC Analyst"], "desc": "Digital solutions for retail, healthcare, financial clients. Python backend, SAP ABAP/CDS/OData, healthcare payer analytics, frontline SOC threat detection.", "tech": ["Java", "Python", "SQL", "Cloud Computing", "DevOps", "SAP", "ABAP", "Cybersecurity"], "min_cgpa": 6.0, "eligibility": "60% or 6.0 CGPA; All engineering branches" },
    "Wipro": { "roles": ["Project Engineer", "Cybersecurity Analyst", "DevOps Engineer"], "desc": "Software development, infrastructure, digital transformation. Palo Alto Networks firewall/security, DevOps automation, retail banking support.", "tech": ["Java", "Python", "Aptitude", "Cloud", "Networking", "DevOps", "CI/CD", "Security", "Firewall"], "min_cgpa": 6.0, "eligibility": "60% or 6.0 CGPA; No active backlogs" },
    "Zoho": { "roles": ["Member Technical Staff", "Technical Support Engineer", "Zoho Consultant"], "desc": "Core SaaS module development, technical support (Zoho Desk/One, night shift, international voice), Zoho Books accounting workflows.", "tech": ["C", "C++", "Java", "Advanced Data Structures", "Algorithms", "System Design", "Zoho Books"], "min_cgpa": 0.0, "eligibility": "No strict CGPA; Purely based on coding and logic" },
}

API_URL = "https://roshfr-resume-v2.hf.space"

# ─── UI ───────────────────────────────────────────────────────────────────────

st.markdown('<div class="hero-title">📄 Resume Rank Checker</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Upload your resume · Pick a company & role · Get your score instantly</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    company_name = st.selectbox(
        "🏢 Company",
        options=sorted(COMPANY_DATA.keys()),
        index=None,
        placeholder="Select a company...",
    )

    role = None
    if company_name:
        role = st.selectbox(
            "💼 Role",
            options=COMPANY_DATA[company_name]["roles"],
            index=None,
            placeholder="Select a role...",
        )

    uploaded_file = st.file_uploader(
        "📎 Upload Resume (PDF)",
        type=["pdf"],
        help="Only PDF files are supported",
    )

    submit = st.button("🚀 Analyse Resume", disabled=not (company_name and role and uploaded_file))

    st.markdown('</div>', unsafe_allow_html=True)

# ─── On Submit ────────────────────────────────────────────────────────────────

if submit and company_name and role and uploaded_file:
    company = COMPANY_DATA[company_name]

    # Build the form data — user never sees this
    payload = {
        "company_name": company_name,
        "role": role,
        "desc": company["desc"],
        "tech": ", ".join(company["tech"]),
        "min_cgpa": str(company["min_cgpa"]),
        "eligibility": company["eligibility"],
    }

    with st.spinner("Analysing your resume…"):
        try:
            response = requests.post(
                f"{API_URL}/score-resume",
                data=payload,
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot reach the API. Make sure the backend is running on port 7860.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"API Error {response.status_code}: {response.text}")
            st.stop()
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.stop()

    # ── Results ──────────────────────────────────────────────────────────────

    score = result["resume_score"]
    label = result["score_label"]

    if score >= 75:
        score_cls, badge_cls = "score-strong", "badge-strong"
    elif score >= 50:
        score_cls, badge_cls = "score-moderate", "badge-moderate"
    else:
        score_cls, badge_cls = "score-weak", "badge-weak"

    st.markdown(f"""
    <div class="card" style="margin-top:1.5rem;">
        <div class="score-ring">
            <div class="score-number {score_cls}">{score}<span style="font-size:1.5rem;opacity:0.6">/100</span></div>
            <div><span class="score-label-badge {badge_cls}">{label}</span></div>
            <div style="color:#64748b;font-size:0.8rem;margin-top:0.4rem;">{company_name} · {role}</div>
        </div>
    """, unsafe_allow_html=True)

    # CGPA warning
    if result.get("cgpa_warning"):
        st.markdown(f'<div class="warn-box">⚠️ {result["cgpa_warning"]}</div>', unsafe_allow_html=True)

    # Score breakdown
    st.markdown('<div class="section-title">Score Breakdown</div>', unsafe_allow_html=True)
    breakdown = result["score_breakdown"]

    def metric_row(label, val):
        st.markdown(f'<div class="metric-row"><span>{label}</span><span class="metric-val">{val}</span></div>', unsafe_allow_html=True)

    metric_row("🔑 Keyword Match",     f"{breakdown['keyword_match']['score']} / 30")
    metric_row("🧠 Semantic Match",    f"{breakdown['semantic_match']['score']} / 30  ({round(breakdown['semantic_match']['raw_cosine']*100,1)}% cosine)")
    metric_row("💼 Experience",        f"{breakdown['experience']['score']} / 25  — {breakdown['experience']['label']}")
    metric_row("🏆 Achievements",      f"{breakdown['achievements']['score']} / 15  — {breakdown['achievements']['label']}")
    if result["detected_cgpa"] > 0:
        metric_row("🎓 Detected CGPA",  str(result["detected_cgpa"]))

    # Skills
    found   = breakdown["keyword_match"].get("found", [])
    missing = breakdown["keyword_match"].get("missing", [])

    if found or missing:
        st.markdown('<div class="section-title">Skills</div>', unsafe_allow_html=True)
        pills = "".join(f'<span class="pill pill-found">✓ {s}</span>' for s in found)
        pills += "".join(f'<span class="pill pill-missing">✗ {s}</span>' for s in missing)
        st.markdown(f'<div style="line-height:2.2">{pills}</div>', unsafe_allow_html=True)

    # Tips
    if result.get("tips"):
        st.markdown('<div class="section-title">💡 Improvement Tips</div>', unsafe_allow_html=True)
        for tip in result["tips"]:
            st.markdown(f'<div class="tip-item">{tip}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)