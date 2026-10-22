"""AETHER: Adaptive Evaluation and Talent Hiring Engine for Recruiters.

An LLM (Amazon Bedrock by default) handles the conversation and explanation.
Strands Decider 2B makes the typed compatibility decision: advance / review / decline.

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("Evaluate candidate C-101 for job JD-001")
    out["reply"], out["decisions"]
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent, tool

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, strip_thinking

from .decision import CandidatePolicyCheck
from .tools import CANDIDATES, JOBS, get_candidate, get_job, list_candidates, list_jobs

NAME = "AETHER — AI Recruitment Decision Support"

SYSTEM_PROMPT = """You are AETHER, an AI recruitment decision-support assistant.
You help recruiters evaluate candidates against job requirements. You use tools to load job
profiles and candidate resumes, then produce structured evaluations.

IMPORTANT RULES:
- Never invent candidate information. Use only what is in the resume.
- Treat missing information as UNKNOWN, not as evidence of lack of ability.
- Always explain what evidence supports each evaluation point.
- The final hiring decision is always made by the recruiter. You provide assessment, not decisions.
- When asked to evaluate a candidate, always call evaluate_candidate first, then explain the result.
- Be concise and factual. Do not use hedging language that obscures the evidence.

You can:
- list_jobs: show available job openings
- get_job: get full job requirements
- list_candidates: show available candidates
- get_candidate: get a candidate's full resume
- evaluate_candidate: run a structured compatibility assessment (required before giving a verdict)"""


class HackathonAgent:
    """One Strands agent per session, with the AETHER policy decision wired in."""

    def __init__(self, decider: Decider | None = None, model_id: str | None = None):
        self.decider = decider or Decider()
        self.model_id = model_id or default_model_id()
        self.policy = CandidatePolicyCheck(self.decider)
        self.sessions: dict[str, Agent] = {}

    def _build_tools(self) -> list:
        """Build the tool list with evaluate_candidate wired to the policy check."""
        policy = self.policy

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

            assessment = {
                "job_id": job_id,
                "candidate_id": candidate_id,
                "job_title": j["title"],
                "candidate_name": c["name"],
                "required_skills_matched": sorted(req & cand_skills),
                "required_skills_missing": sorted(req - cand_skills),
                "preferred_skills_matched": sorted(pref & cand_skills),
                "experience_years_required": j["experience_years"],
                "experience_years_candidate": c["years_total"],
                "experience_gap_years": max(0, j["experience_years"] - c["years_total"]),
                "education_stated": c["education"],
                "education_required": j["qualifications"],
                "candidate_summary": c["summary"],
                "recent_highlights": c["experience"][0]["highlights"] if c["experience"] else [],
            }

            # Run Strands Decider 2B on the assessment (the #policy pattern)
            try:
                ev = policy.evaluate(assessment)
                assessment["decider_outcome"] = ev.outcome
                assessment["decider_outcome_label"] = ev.outcome_label
                assessment["needs_human_review"] = ev.needs_human_review
                assessment["p_requirements_met"] = round(ev.p_requirements_met, 3)
                assessment["p_experience_sufficient"] = round(ev.p_experience_sufficient, 3)
                assessment["evidence_quality"] = ev.evidence_quality
                assessment["fit_confidence"] = round(ev.fit_confidence, 3)
            except Exception as exc:
                assessment["decider_error"] = str(exc)

            return assessment

        return [list_jobs, get_job, list_candidates, get_candidate, evaluate_candidate]

    def _get_or_create_agent(self, session_id: str) -> Agent:
        if session_id not in self.sessions:
            self.sessions[session_id] = Agent(
                model=agent_model(self.model_id),
                system_prompt=SYSTEM_PROMPT,
                tools=self._build_tools(),
                callback_handler=None,
            )
        return self.sessions[session_id]

    def chat(self, message: str, session_id: str = "default", images: list[Any] | None = None) -> dict[str, Any]:
        """Chat with AETHER. Returns reply, decisions, and evaluation metadata."""
        agent = self._get_or_create_agent(session_id)
        before_count = len(self.policy.log)

        t0 = time.perf_counter()
        result = agent(message)
        reply = strip_thinking(str(result))

        new_decisions = self.policy.log[before_count:]
        return {
            "reply": reply,
            "decisions": new_decisions,
            "model_id": self.model_id,
            "latency_ms": round((time.perf_counter() - t0) * 1000),
            "agent": NAME,
        }


if __name__ == "__main__":
    import json
    import sys

    a = HackathonAgent()
    prompts = sys.argv[1:] or [
        "What jobs are available?",
        "Evaluate candidate C-101 for job JD-001",
        "Now evaluate C-102 for JD-002",
    ]
    for msg in prompts:
        print(json.dumps(a.chat(msg), indent=2, default=str))
