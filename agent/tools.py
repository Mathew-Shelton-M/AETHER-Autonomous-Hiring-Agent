"""AETHER recruitment tools: synthetic job profiles and candidate resumes so the demo runs anywhere.

The recruiter agent uses these to fetch job requirements and candidate data, then hands the
evaluation state to Strands Decider 2B via the decision pattern in decision.py.
"""

from __future__ import annotations

from strands import tool

# ---------------------------------------------------------------------------
# Synthetic job profiles
# ---------------------------------------------------------------------------
JOBS: dict[str, dict] = {
    "JD-001": {
        "title": "Senior Backend Engineer",
        "team": "Platform",
        "location": "Remote (US)",
        "level": "Senior (5+ years)",
        "required_skills": ["Python", "distributed systems", "REST APIs", "SQL"],
        "preferred_skills": ["Kafka", "Kubernetes", "AWS", "Go"],
        "qualifications": "Bachelor's in Computer Science or equivalent experience",
        "experience_years": 5,
        "responsibilities": [
            "Design and operate high-throughput data pipelines",
            "Mentor junior engineers",
            "Own reliability and observability of platform services",
        ],
        "culture": "collaborative, ownership-driven, async-first",
    },
    "JD-002": {
        "title": "ML Engineer",
        "team": "AI/ML",
        "location": "Hybrid (NYC)",
        "level": "Mid-level (3+ years)",
        "required_skills": ["Python", "PyTorch", "model training", "data preprocessing"],
        "preferred_skills": ["AWS SageMaker", "MLflow", "transformer models", "LLMs"],
        "qualifications": "Master's in ML / CS or equivalent work experience",
        "experience_years": 3,
        "responsibilities": [
            "Train and evaluate production ML models",
            "Build feature pipelines with data engineers",
            "Instrument model quality and drift monitoring",
        ],
        "culture": "research-minded, fast iteration, data-driven decisions",
    },
    "JD-003": {
        "title": "Product Manager – Developer Tools",
        "team": "Product",
        "location": "Remote (Global)",
        "level": "Mid-level (3+ years PM experience)",
        "required_skills": ["product strategy", "roadmap planning", "user research", "cross-functional collaboration"],
        "preferred_skills": ["developer tool experience", "API product management", "SQL", "Agile/Scrum"],
        "qualifications": "Bachelor's degree; technical background preferred",
        "experience_years": 3,
        "responsibilities": [
            "Define and prioritise product roadmap for developer tooling",
            "Synthesise customer feedback into actionable requirements",
            "Partner with engineering and design on delivery",
        ],
        "culture": "customer-obsessed, evidence-based, low-ego collaboration",
    },
}

# ---------------------------------------------------------------------------
# Synthetic candidate resumes
# ---------------------------------------------------------------------------
CANDIDATES: dict[str, dict] = {
    "C-101": {
        "name": "Ananya Krishnan",
        "summary": "7 years building backend systems at scale. Led migration of monolith to microservices at a fintech serving 5M users.",
        "skills": ["Python", "Go", "Kafka", "Kubernetes", "PostgreSQL", "REST APIs", "distributed systems", "AWS"],
        "experience": [
            {"role": "Staff Engineer", "company": "FinCore", "years": 3,
             "highlights": ["Owned platform reliability (99.99% SLA)", "Built Kafka-based event pipeline handling 200k events/s", "Mentored a team of 4 engineers"]},
            {"role": "Senior Backend Engineer", "company": "ShopLink", "years": 4,
             "highlights": ["Rewrote order service in Go", "Introduced distributed tracing", "Reduced p95 latency by 40%"]},
        ],
        "education": "B.Tech Computer Science, IIT Madras",
        "years_total": 7,
    },
    "C-102": {
        "name": "Rohan Mehta",
        "summary": "Recent MSc graduate with strong ML fundamentals. 1 year industry internship at a health-tech startup.",
        "skills": ["Python", "PyTorch", "scikit-learn", "data preprocessing", "Jupyter", "Git"],
        "experience": [
            {"role": "ML Intern", "company": "HealthAI", "years": 1,
             "highlights": ["Fine-tuned a BERT model for clinical NER", "Built data validation pipeline in pandas", "Deployed model endpoint on AWS SageMaker (supervised)"]},
        ],
        "education": "MSc Machine Learning, University of Edinburgh",
        "years_total": 1,
    },
    "C-103": {
        "name": "Sofia Reyes",
        "summary": "Product manager with 5 years in B2B SaaS. Recently transitioned from engineering (2 years as software developer).",
        "skills": ["product strategy", "roadmap planning", "user research", "Agile/Scrum", "SQL", "cross-functional collaboration"],
        "experience": [
            {"role": "Product Manager", "company": "DevGrid", "years": 3,
             "highlights": ["Launched API marketplace used by 800+ developers", "Ran quarterly user research cycles", "Drove 35% increase in API adoption"]},
            {"role": "Associate PM", "company": "Toolshed", "years": 2,
             "highlights": ["Owned developer documentation platform", "Coordinated with 3 engineering squads"]},
        ],
        "education": "BSc Software Engineering, Universidad Autónoma de Madrid",
        "years_total": 5,
    },
    "C-104": {
        "name": "James Okafor",
        "summary": "Backend generalist with 4 years of experience, mostly in e-commerce. Comfortable with Python and databases.",
        "skills": ["Python", "Django", "MySQL", "REST APIs", "Redis", "Docker"],
        "experience": [
            {"role": "Backend Developer", "company": "CartZone", "years": 4,
             "highlights": ["Built product catalogue API (Python/Django)", "Optimised slow SQL queries (3× speedup)", "Participated in on-call rotation"]},
        ],
        "education": "BSc Computer Science, University of Lagos",
        "years_total": 4,
    },
    "C-105": {
        "name": "Lin Wei",
        "summary": "ML engineer with 4 years building production recommendation systems. Strong transformer model experience.",
        "skills": ["Python", "PyTorch", "transformer models", "LLMs", "MLflow", "AWS SageMaker", "data preprocessing", "model training"],
        "experience": [
            {"role": "ML Engineer", "company": "RecoSys AI", "years": 4,
             "highlights": ["Trained and deployed BERT-based recommendation model (30M users)", "Built MLflow experiment tracking platform", "Reduced model training cost 25% with mixed-precision training"]},
        ],
        "education": "MSc Computer Science (ML track), Tsinghua University",
        "years_total": 4,
    },
}


@tool
def list_jobs() -> list[dict]:
    """List all available job openings with their id, title, team and level."""
    return [{"job_id": jid, "title": j["title"], "team": j["team"], "level": j["level"],
             "location": j["location"]} for jid, j in JOBS.items()]


@tool
def get_job(job_id: str) -> dict:
    """Get the full job profile for a given job_id, including required skills and responsibilities."""
    j = JOBS.get(job_id.strip().upper())
    return {"job_id": job_id, **j} if j else {"error": f"no job {job_id}"}


@tool
def list_candidates() -> list[dict]:
    """List all candidates with their id, name and summary."""
    return [{"candidate_id": cid, "name": c["name"], "summary": c["summary"],
             "skills_count": len(c["skills"]), "years_total": c["years_total"]}
            for cid, c in CANDIDATES.items()]


@tool
def get_candidate(candidate_id: str) -> dict:
    """Get a candidate's full resume: skills, experience, education and summary."""
    c = CANDIDATES.get(candidate_id.strip().upper())
    return {"candidate_id": candidate_id, **c} if c else {"error": f"no candidate {candidate_id}"}


@tool
def evaluate_candidate(job_id: str, candidate_id: str) -> dict:
    """Evaluate a candidate against a job and return a structured compatibility assessment.

    The agent calls this tool; the decision pattern in decision.py sends the result to
    Strands Decider 2B to decide advance / review / decline.
    """
    j = JOBS.get(job_id.strip().upper())
    c = CANDIDATES.get(candidate_id.strip().upper())
    if not j:
        return {"error": f"no job {job_id}"}
    if not c:
        return {"error": f"no candidate {candidate_id}"}

    req = set(s.lower() for s in j["required_skills"])
    pref = set(s.lower() for s in j["preferred_skills"])
    cand_skills = set(s.lower() for s in c["skills"])

    matched_required = sorted(req & cand_skills)
    missing_required = sorted(req - cand_skills)
    matched_preferred = sorted(pref & cand_skills)
    exp_gap = max(0, j["experience_years"] - c["years_total"])

    return {
        "job_id": job_id,
        "candidate_id": candidate_id,
        "job_title": j["title"],
        "candidate_name": c["name"],
        "required_skills_matched": matched_required,
        "required_skills_missing": missing_required,
        "preferred_skills_matched": matched_preferred,
        "experience_years_required": j["experience_years"],
        "experience_years_candidate": c["years_total"],
        "experience_gap_years": exp_gap,
        "education_stated": c["education"],
        "education_required": j["qualifications"],
        "candidate_summary": c["summary"],
        "recent_highlights": c["experience"][0]["highlights"] if c["experience"] else [],
    }


TOOLS = [list_jobs, get_job, list_candidates, get_candidate, evaluate_candidate]
