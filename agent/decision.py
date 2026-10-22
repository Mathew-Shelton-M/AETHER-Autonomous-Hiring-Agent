"""REUSABLE DECISION PATTERN: candidate-job compatibility policy  (#policy)

What it does
    When the recruiter agent evaluates a candidate, Strands Decider 2B classifies the
    compatibility against a structured job requirements policy:
    - does the candidate meet the core technical requirements?
    - is their experience level sufficient?
    - is there enough evidence to decide, or are key details missing?
    Results map to: advance (strong match), review (human should decide), or decline
    (significant evidence gaps or misalignment with requirements).

    Missing information is treated as unknown, never as proof of lack of ability.
    The recruiter always sees confidence scores and the final call is human-made.

Typed questions
    `requirements_met` (noul): do core requirements appear to be met by the evidence?
    `experience_sufficient` (noul): does the candidate's experience level match the role?
    `evidence_quality` (score): how complete and verifiable is the evidence in the resume?
    `fit_category` (choice): advance | review | decline, based on the overall picture.

Wiring
    `CandidatePolicyCheck` wraps the kit's PolicyCheck pattern. The agent calls
    `evaluate_candidate(job_id, candidate_id)` via tools.py, then this pattern sends the
    result to Strands Decider 2B. The agent formats the explanation using the LLM.

How to reuse it
    Change JOB_POLICY and FIT_CATEGORIES for your domain (job requisition, grant review,
    loan application, etc.). Thresholds live in decide_outcome() below.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from decider_kit import Decider
from decider_kit.patterns.guardrails import render_messages

IS_KIT_EXAMPLE = False  # This is an original agent — not the kit example

PATTERN_TAG = "#policy"

# The policy that defines what a strong candidate looks like.
# Written in plain language so the decider can compare evidence against it.
JOB_POLICY = """
A candidate meets the role's requirements when:
1. They demonstrate the required core skills through direct experience or credible projects.
2. Their total years of relevant experience meets or approaches the stated minimum.
3. Their education or equivalent experience satisfies the stated qualifications.
4. There is enough specific evidence in the resume to make a judgement.

A candidate does NOT meet requirements when:
- Required core skills are absent with no equivalent evidence.
- Experience is significantly below the minimum with no compensating factors.
- The resume is too sparse to evaluate key dimensions.

Missing information should be treated as UNKNOWN, not as absence of ability.
Do not penalise a candidate for what the resume does not say.
"""

FIT_CATEGORIES = {
    "advance": "Strong evidence of required skills and sufficient experience; recommend progressing to interview",
    "review": "Partial match, mixed evidence, or insufficient information to decide without human judgement",
    "decline": "Significant gaps in required skills or experience, with no compensating evidence found",
}

EVIDENCE_LEVELS = ["sparse", "partial", "adequate", "strong"]


# Static QUESTIONS for the benchmark (uses generic field names; build_questions() is used at runtime
# with the actual job context for live evaluations).
QUESTIONS: dict[str, Any] = {
    "requirements_met": Decider.noul(
        "Based only on evidence in the resume, does the candidate appear to meet the core requirements for this role?",
        {"true": "the resume contains clear evidence of the required skills and experience",
         "false": "required skills or experience are absent or insufficiently evidenced"}),
    "experience_sufficient": Decider.noul(
        "Does the candidate's stated experience level appear to meet or approach the minimum years required for this role?",
        {"true": "years of experience meet or approach the minimum; role level appears appropriate",
         "false": "candidate appears significantly under the experience threshold with no compensating evidence"}),
    "evidence_quality": Decider.score(
        "How complete and specific is the evidence in this resume? Consider: named projects, quantified results, named technologies, and role descriptions.",
        EVIDENCE_LEVELS),
    "fit_category": Decider.choice(
        "Given all the evidence, what is the best fit classification for this candidate against the stated job requirements?",
        FIT_CATEGORIES),
}


def build_questions(job_title: str, required_skills: list[str], min_years: int) -> dict[str, Any]:
    skill_list = ", ".join(required_skills)
    return {
        "requirements_met": Decider.noul(
            f"Based only on evidence in the resume, does the candidate appear to meet the core requirements "
            f"for the role: {job_title}? Required skills: {skill_list}.",
            {"true": "the resume contains clear evidence of the required skills and experience",
             "false": "required skills or experience are absent or insufficiently evidenced"}),
        "experience_sufficient": Decider.noul(
            f"Does the candidate's stated experience level ({min_years}+ years required) appear to meet "
            "or approach the minimum for this role?",
            {"true": "years of experience meet or approach the minimum; role level appears appropriate",
             "false": "candidate appears significantly under the experience threshold with no compensating evidence"}),
        "evidence_quality": Decider.score(
            "How complete and specific is the evidence in this resume? Consider: named projects, "
            "quantified results, named technologies, and role descriptions.",
            EVIDENCE_LEVELS),
        "fit_category": Decider.choice(
            f"Given all the evidence, what is the best fit classification for this candidate against the "
            f"job '{job_title}'?",
            FIT_CATEGORIES),
    }


@dataclass
class EvaluationResult:
    outcome: str            # advance | review | decline
    candidate_name: str
    job_title: str
    p_requirements_met: float
    p_experience_sufficient: float
    evidence_quality: str
    evidence_confidence: float
    fit_category: str
    fit_confidence: float
    needs_human_review: bool
    decider_ms: float

    @property
    def outcome_label(self) -> str:
        return {"advance": "Advance to interview",
                "review": "Flag for human review",
                "decline": "Decline — evidence gaps"}[self.outcome]

    def to_log(self) -> dict[str, Any]:
        return {
            "pattern": PATTERN_TAG,
            "candidate": self.candidate_name,
            "job": self.job_title,
            "verdict": self.outcome,
            "p_requirements_met": round(self.p_requirements_met, 3),
            "p_experience_sufficient": round(self.p_experience_sufficient, 3),
            "evidence_quality": self.evidence_quality,
            "fit_category": self.fit_category,
            "fit_confidence": round(self.fit_confidence, 3),
            "needs_human_review": self.needs_human_review,
            "decider_ms": round(self.decider_ms),
        }


class CandidatePolicyCheck:
    """Evaluate a candidate against a job using Strands Decider 2B with the #policy pattern."""

    def __init__(self, decider: Decider, advance_at: float = 0.65, decline_at: float = 0.35,
                 review_confidence_threshold: float = 0.60):
        self.decider = decider
        self.advance_at = advance_at
        self.decline_at = decline_at
        self.review_confidence_threshold = review_confidence_threshold
        self.log: list[dict[str, Any]] = []

    def evaluate(self, assessment: dict[str, Any]) -> EvaluationResult:
        """Run the decider on a candidate assessment dict (from evaluate_candidate tool)."""
        job_title = assessment.get("job_title", "this role")
        candidate_name = assessment.get("candidate_name", "this candidate")
        required_skills = assessment.get("required_skills_matched", []) + assessment.get("required_skills_missing", [])
        min_years = int(assessment.get("experience_years_required", 0))

        # Build the state: everything the decider needs to make a decision
        state = _build_state(assessment, JOB_POLICY)
        questions = build_questions(job_title, required_skills, min_years)
        answers = self.decider.ask(state, questions)

        p_req = answers["requirements_met"].p_yes or 0.0
        p_exp = answers["experience_sufficient"].p_yes or 0.0
        ev_quality = answers["evidence_quality"].label or "partial"
        fit_label = answers["fit_category"].label or "review"
        fit_conf = answers["fit_category"].confidence

        outcome = self._decide(p_req, p_exp, fit_label, fit_conf)
        needs_review = fit_conf < self.review_confidence_threshold or outcome == "review"

        result = EvaluationResult(
            outcome=outcome,
            candidate_name=candidate_name,
            job_title=job_title,
            p_requirements_met=p_req,
            p_experience_sufficient=p_exp,
            evidence_quality=ev_quality,
            evidence_confidence=answers["evidence_quality"].confidence,
            fit_category=fit_label,
            fit_confidence=fit_conf,
            needs_human_review=needs_review,
            decider_ms=self.decider.last_latency_ms or 0.0,
        )
        self.log.append(result.to_log())
        return result

    def _decide(self, p_req: float, p_exp: float, fit_label: str, fit_conf: float) -> str:
        """Combine decider signals into a final outcome.

        The decider's fit_category is the primary signal. p_req and p_exp act as guards:
        if both are clearly negative, decline regardless of fit_category. If confidence is
        low, always fall back to review so a human decides.
        """
        if fit_conf < self.review_confidence_threshold:
            return "review"
        if p_req < self.decline_at and p_exp < self.decline_at:
            return "decline"
        if p_req >= self.advance_at and p_exp >= self.advance_at and fit_label == "advance":
            return "advance"
        if fit_label == "decline" and p_req < self.advance_at:
            return "decline"
        return fit_label if fit_label in ("advance", "review", "decline") else "review"


def _build_state(a: dict[str, Any], policy: str) -> str:
    matched = ", ".join(a.get("required_skills_matched") or []) or "none found"
    missing = ", ".join(a.get("required_skills_missing") or []) or "none"
    preferred = ", ".join(a.get("preferred_skills_matched") or []) or "none"
    highlights = "\n".join(f"  - {h}" for h in (a.get("recent_highlights") or []))
    exp_gap = a.get("experience_gap_years", 0)
    exp_note = f"(meets minimum)" if exp_gap == 0 else f"({exp_gap} year(s) below minimum)"

    return f"""EVALUATION POLICY:
{policy.strip()}

JOB REQUIREMENTS:
  Title: {a.get("job_title", "?")}
  Required experience: {a.get("experience_years_required", "?")} years
  Education required: {a.get("education_required", "?")}

CANDIDATE EVIDENCE FROM RESUME:
  Name: {a.get("candidate_name", "?")}
  Summary: {a.get("candidate_summary", "?")}
  Total experience: {a.get("experience_years_candidate", "?")} years {exp_note}
  Education stated: {a.get("education_stated", "not stated")}
  Required skills matched: {matched}
  Required skills not evidenced: {missing}
  Preferred skills matched: {preferred}
  Recent role highlights:
{highlights or "  (none stated)"}

NOTE: Treat any unstated information as UNKNOWN, not as absence of ability."""
