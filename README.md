---
sdk: docker
title: Resume Rank Checker Pro
emoji: 📄
colorFrom: blue
colorTo: indigo
app_port: 7860
---

# Resume Rank Checker Pro

A FastAPI-based resume scoring API that analyzes how well a resume matches a job description. Hosted on Hugging Face Spaces.

**🔗 Live API:** https://roshfr-resume-v2.hf.space  
**📖 Swagger Docs:** https://roshfr-resume-v2.hf.space/docs

---

## How It Works

Send a resume PDF along with job details to the `/score-resume` endpoint and receive a 0–100 match score with a full breakdown and improvement tips.

---

## API Endpoint

### `POST /score-resume`

**Inputs (multipart/form-data)**

| Field | Type | Description |
|---|---|---|
| `file` | PDF file | Candidate's resume |
| `company_name` | string | Target company name |
| `role` | string | Job role / title |
| `desc` | string | Job description text |
| `tech` | string | Comma-separated required skills (e.g. `Python,Docker,FastAPI`) |
| `min_cgpa` | float | Minimum CGPA required (use `0.0` if not applicable) |
| `eligibility` | string | Any other eligibility criteria (optional) |

**Output (JSON)**

| Field | Description |
|---|---|
| `resume_score` | Overall score out of 100 |
| `score_label` | `Strong Match` / `Moderate Match` / `Needs Improvement` |
| `detected_cgpa` | CGPA extracted from resume |
| `cgpa_warning` | Warning if CGPA is below the required threshold |
| `match_details` | Quick summary of each scoring component |
| `score_breakdown` | Detailed scores — keyword match (30), semantic match (30), experience (25), achievements (15) |
| `tips` | Personalized suggestions to improve the resume for the target role |

---

## Scoring Breakdown

| Component | Max Score | Method |
|---|---|---|
| Keyword Match | 30 | Checks required skills with synonym resolution |
| Semantic Match | 30 | Qwen3-Embedding-0.6B cosine similarity |
| Experience | 25 | Action verbs, work context, date ranges |
| Achievements | 15 | Hackathons, certifications, coding platforms |

---

## Tech Stack

- **FastAPI** — REST API framework  
- **pdfplumber** — PDF text extraction  
- **Qwen3-Embedding-0.6B** — Semantic similarity via sentence-transformers  
- **PyTorch** — Model inference  
- **Docker** — Containerized deployment on Hugging Face Spaces
