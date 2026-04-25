from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import torch
import re
import json
from sentence_transformers import SentenceTransformer, util

# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(title="Resume Rank Checker Pro", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Load Config (synonyms + scoring lists only) ─────────────────────────────

try:
    with open("resume_config.json", "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
    TECH_SYNONYMS = CONFIG["tech_synonyms"]
    print(f"[INFO] ✅ Loaded config from resume_config.json")
except FileNotFoundError:
    print("[ERROR] ❌ resume_config.json not found!")
    CONFIG = TECH_SYNONYMS = {}
except json.JSONDecodeError as e:
    print(f"[ERROR] ❌ Invalid JSON: {e}")
    CONFIG = TECH_SYNONYMS = {}

# ─── Device + Model ───────────────────────────────────────────────────────────

if torch.cuda.is_available():
    device = "cuda"
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"[INFO] GPU: {torch.cuda.get_device_name(0)} ({vram_gb:.1f} GB VRAM)")
    if vram_gb < 5:
        torch.cuda.set_per_process_memory_fraction(0.85)
    model_kwargs = {"torch_dtype": torch.float16}
else:
    device = "cpu"
    model_kwargs = {}
    print("[WARN] Running on CPU.")

print(f"[INFO] Loading Qwen3-Embedding-0.6B on {device}...")
model = SentenceTransformer(
    "Qwen/Qwen3-Embedding-0.6B",
    device=device,
    model_kwargs=model_kwargs,
    trust_remote_code=True,
)
print("[INFO] Model ready.")

# ─── Scoring Helpers ──────────────────────────────────────────────────────────

def resolve_synonyms(skill: str, resume_lower: str) -> bool:
    skill_low = skill.lower().strip()
    if skill_low in resume_lower:
        return True
    for key, aliases in TECH_SYNONYMS.items():
        if skill_low == key or skill_low in aliases:
            if key in resume_lower or any(a in resume_lower for a in aliases):
                return True
    return False

def normalize_cgpa(val: float) -> float:
    if 0.1 <= val <= 5.0:
        return round((val / 4.0) * 10, 2)
    return val

def extract_text_pro(file) -> tuple[str, float]:
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + " "
    patterns = [
        r'(?i)(?:cgpa|gpa|aggregate|avg|percentage)\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,2})?)',
        r'(?i)(\d{1,2}\.\d{1,2})\s*/\s*10',
        r'(?i)(\d{2,3}(?:\.\d{1,2})?)\s*%',
    ]
    all_found = []
    for pat in patterns:
        for m in re.findall(pat, text):
            val = float(m)
            if val > 10: val /= 10
            all_found.append(val)
    detected = normalize_cgpa(max(all_found)) if all_found else 0.0
    return text.strip(), detected

def calculate_keyword_score(resume_text: str, required_skills: list) -> tuple[int, list, list]:
    text_low = resume_text.lower()
    required = list(dict.fromkeys(required_skills))
    found, missing = [], []
    for skill in required:
        (found if resolve_synonyms(skill, text_low) else missing).append(skill)
    score = round((len(found) / len(required)) * 30) if required else 0
    return score, found, missing

EXP_ACTIVE_VERBS = CONFIG.get("exp_verbs", [])
EXP_CONTEXT = CONFIG.get("exp_context", [])
EXP_DURATION = CONFIG.get("exp_duration_patterns", [])

def calculate_experience_score(resume_text: str) -> tuple[int, str, list]:
    tl = resume_text.lower()
    signals = []
    verbs = [v for v in EXP_ACTIVE_VERBS if v in tl]
    verb_score = min(len(verbs) * 2, 10)
    if verbs: signals.append(f"Action verbs: {', '.join(verbs[:5])}")
    ctx = [w for w in EXP_CONTEXT if w in tl]
    ctx_score = min(len(ctx) * 2, 10)
    if ctx: signals.append(f"Work context: {', '.join(ctx[:4])}")
    dur_count = sum(len(re.findall(p, tl)) for p in EXP_DURATION)
    dur_score = min(dur_count * 2, 5)
    if dur_count: signals.append(f"Date ranges: {dur_count}")
    total = verb_score + ctx_score + dur_score
    label = "Strong experience" if total >= 18 else "Moderate experience" if total >= 10 else "Limited experience"
    return total, label, signals

ACH_HIGH = CONFIG.get("ach_high", [])
ACH_MID = CONFIG.get("ach_mid", [])
ACH_LOW = CONFIG.get("ach_low", [])

def calculate_achievement_score(resume_text: str) -> tuple[int, str, list]:
    tl = resume_text.lower()
    signals = []
    hi = [k for k in ACH_HIGH if k in tl]
    mid = [k for k in ACH_MID if k in tl]
    lo = [k for k in ACH_LOW if k in tl]
    total = min(len(hi)*4 + len(mid)*2 + len(lo)*1, 15)
    if hi: signals.append(f"High-value: {', '.join(hi[:4])}")
    if mid: signals.append(f"Platforms/certs: {', '.join(mid[:4])}")
    if lo: signals.append(f"Other: {', '.join(lo[:4])}")
    label = "Excellent achievements" if total >= 11 else "Good achievements" if total >= 6 else "Few achievements listed"
    return total, label, signals

def generate_tips(total, missing, company_name, tech_skills, roles, min_cgpa, exp_score, ach_score, detected_cgpa, sim) -> list:
    tips = []
    if total < 35:
        tips.append(f"Major gaps. Target '{roles.split('/')[0].strip()}' role at {company_name}.")
    elif total < 55:
        tips.append(f"Moderate match. Add Technical Skills section with {', '.join(tech_skills[:3])}.")
    elif total < 75:
        tips.append("Good match. Use exact JD keywords for ATS.")
    else:
        tips.append(f"Strong match! Quantify achievements with numbers (e.g. 'Reduced latency 30% using {tech_skills[0]}').")

    if missing:
        tips.append(f"Missing skills: {', '.join(missing[:4])}. Add a small project to justify.")
    if sim < 0.45:
        tips.append(f"Language mismatch. Mirror {company_name}'s exact terms.")
    if exp_score < 8:
        tips.append(f"Add internships using {tech_skills[0]} to boost experience score.")
    if ach_score < 5:
        tips.append("Participate in SIH, LeetCode, Kaggle — they heavily boost your score.")

    if min_cgpa == 0.0:
        tips.append(f"{company_name} is skills-only. Focus on coding performance.")
    elif detected_cgpa > 0 and detected_cgpa < min_cgpa:
        tips.append(f"CGPA alert: {detected_cgpa} < {min_cgpa} required.")
    return tips

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Resume Rank Checker Pro v3.0", "swagger": "http://localhost:8000/docs"}

@app.post("/score-resume")
async def score_resume(
    file: UploadFile,
    company_name: str = Form(...),
    role: str = Form(...),
    desc: str = Form(...),
    tech: str = Form(..., description="Comma-separated list of required skills, e.g. 'Python,FastAPI,Docker'"),
    min_cgpa: float = Form(0.0),
    eligibility: str = Form(""),
):
    # Parse tech skills from comma-separated string
    tech_skills = [s.strip() for s in tech.split(",") if s.strip()]
    if not tech_skills:
        raise HTTPException(400, "At least one tech skill is required.")

    resume_text, detected_cgpa = extract_text_pro(file.file)

    if len(resume_text.strip()) < 50:
        raise HTTPException(422, "Could not extract text from PDF.")

    kw_score, found_skills, missing_skills = calculate_keyword_score(resume_text, tech_skills)

    queries = [
        f"Represent this resume for job matching: {resume_text[:2500]}",
        f"Represent this job description and required technical skills: {desc} Skills: {', '.join(tech_skills)}"
    ]
    embeddings = model.encode(queries, convert_to_tensor=True)
    sim = util.cos_sim(embeddings[0], embeddings[1]).item()
    semantic_score = round(max(0.0, (sim - 0.10) / 0.80) * 30)
    del embeddings
    if device == "cuda":
        torch.cuda.empty_cache()

    exp_score, exp_label, exp_signals = calculate_experience_score(resume_text)
    ach_score, ach_label, ach_signals = calculate_achievement_score(resume_text)

    total_score = min(kw_score + semantic_score + exp_score + ach_score, 100)

    tips = generate_tips(
        total_score, missing_skills, company_name, tech_skills,
        role, min_cgpa, exp_score, ach_score, detected_cgpa, sim
    )

    return {
        "company": company_name,
        "role": role,
        "resume_score": total_score,
        "score_label": "Strong Match" if total_score >= 75 else "Moderate Match" if total_score >= 50 else "Needs Improvement",
        "detected_cgpa": round(detected_cgpa, 2),
        "eligibility": eligibility,
        "cgpa_warning": f"Detected CGPA ({detected_cgpa}) below required {min_cgpa}" if min_cgpa > 0 and detected_cgpa > 0 and detected_cgpa < min_cgpa else None,
        "match_details": {
            "keyword_match": f"{kw_score}/30 ({len(found_skills)}/{len(tech_skills)} skills)",
            "semantic_similarity": f"{round(sim * 100, 2)}%",
            "experience_score": f"{exp_score}/25 — {exp_label}",
            "achievement_score": f"{ach_score}/15 — {ach_label}",
        },
        "score_breakdown": {
            "keyword_match": {"score": kw_score, "max": 30, "found": found_skills, "missing": missing_skills},
            "semantic_match": {"score": semantic_score, "max": 30, "raw_cosine": round(sim, 4)},
            "experience": {"score": exp_score, "max": 25, "label": exp_label, "signals": exp_signals},
            "achievements": {"score": ach_score, "max": 15, "label": ach_label, "signals": ach_signals},
        },
        "tips": tips if tips else ["Excellent match!"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)