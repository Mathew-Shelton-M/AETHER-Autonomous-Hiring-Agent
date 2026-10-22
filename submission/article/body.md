# AETHER: AI Recruitment Decision Support with Strands Decider 2B

By Code Alcheimist

Screening resumes is one of the most time-consuming and inconsistent tasks in hiring.
Two recruiters looking at the same resume against the same job description often reach
different conclusions. AETHER fixes that by giving every evaluation the same typed,
calibrated decision from Strands Decider 2B -- advance, review, or decline -- backed
by evidence from the resume, with a confidence score the recruiter can act on.
The best part: the final hiring call always stays with the recruiter.

## The project

AETHER is a recruiter-facing AI agent that evaluates candidate resumes against structured
job requirements. It is built on the Strands Agents SDK, uses Amazon Bedrock Nova Lite for
conversation and explanation, and hands every compatibility decision to Strands Decider 2B
using the #policy reusable pattern.

**Who it is for:** recruiters and hiring managers screening candidates at volume, and any
team that wants consistent, explainable, evidence-based shortlisting.

**What it does:**

- Load job profiles (title, required skills, experience minimum, responsibilities)
- Load candidate resumes (skills, experience history, education, highlights)
- Evaluate compatibility across skills, experience and qualifications
- Return advance / review / decline with probability scores and a plain-English explanation
- Escalate low-confidence evaluations to a human -- never auto-advance uncertain cases
- Show everything in the AETHER recruiter dashboard: job details, candidate cards,
  decision confidence bars, and the human review flag

**A real conversation from the demo:**

Recruiter: "Evaluate candidate C-101 for the Senior Backend Engineer role JD-001"

AETHER: "Ananya Krishnan is a strong match for Senior Backend Engineer. She has 7 years
of backend experience, exceeding the 5-year minimum. All required skills -- Python,
distributed systems, REST APIs, SQL, Kafka, and Kubernetes -- are evidenced in her resume.
Strands Decider 2B classified this as ADVANCE with 88% fit confidence."

Recruiter: "Now evaluate C-102 for the ML Engineer role JD-002"

AETHER: "Rohan Mehta has strong ML fundamentals and all required skills are present.
However, he has only 1 year of industry experience against the 3-year minimum.
Strands Decider 2B scored experience sufficiency at 0.31 and flagged this for human review.
Missing context is treated as unknown, not as proof of inability. A recruiter should decide."

< FIGURE 1 of 2: upload submission/article/img/architecture.png here >
Alt text: Architecture diagram showing the recruiter, the Strands Agents agent on Amazon Bedrock AgentCore Runtime with tools and the decision pattern, Amazon Bedrock Nova Lite for conversation, and Strands Decider 2B for the typed compatibility verdict.

## How I built it

AETHER is built on the Strands Agents SDK. The agent loop lives in `agent/agent.py`.
Five tools in `agent/tools.py` give the agent access to synthetic job profiles and
candidate resumes -- structured data that makes the demo fully reproducible without
any external API keys for the data layer.

Amazon Bedrock Nova Lite handles the conversation: understanding the recruiter's request,
deciding which tools to call, and generating the plain-English explanation after the
decision is made. The model is configured via `LLM_PROVIDER=bedrock` and
`BEDROCK_MODEL_ID=us.amazon.nova-lite-v1:0` in `.env`.

Strands Decider 2B runs on the AWS User Group Madurai hosted API (`DECIDER_MODE=ugmdu`),
which means zero GPU setup for development. The agent is designed to deploy to Amazon
Bedrock AgentCore Runtime with `./kit deploy`.

The project was built using the AWS User Group Madurai Strands Decider hackathon kit,
which provided the client, the five reusable patterns, the benchmark harness, the demo UI,
and the deployment pipeline. Kiro's spec-driven workflow made it straightforward to go
from the idea to a running agent in one session.

## The decision I handed to Strands Decider 2B

Recruitment screening is an ideal use case for a decision model rather than a language
model. The check must be:

- **Consistent** -- the same resume against the same job always gets the same signal
- **Fast** -- one forward pass, not a chain of LLM calls
- **Calibrated** -- the probability score tells the recruiter how confident the system is
- **Auditable** -- typed questions with named criteria are explainable

The decision pattern used is `#policy` -- classification against a written policy.
Strands Decider 2B answers four typed questions in a single forward pass:

```python
QUESTIONS = {
    "requirements_met": Decider.noul(
        "Based only on evidence in the resume, does the candidate appear to meet "
        "the core requirements for the role?",
        {
            "true": "the resume contains clear evidence of the required skills and experience",
            "false": "required skills or experience are absent or insufficiently evidenced"
        }
    ),
    "experience_sufficient": Decider.noul(
        "Does the candidate's stated experience level appear to meet or approach "
        "the minimum years required for this role?",
        {
            "true": "years of experience meet or approach the minimum; role level is appropriate",
            "false": "candidate appears significantly under the experience threshold"
        }
    ),
    "evidence_quality": Decider.score(
        "How complete and specific is the evidence in this resume?",
        ["sparse", "partial", "adequate", "strong"]
    ),
    "fit_category": Decider.choice(
        "Given all the evidence, what is the best fit classification for this candidate?",
        {
            "advance": "Strong evidence of required skills and sufficient experience",
            "review": "Partial match, mixed evidence, or insufficient information to decide",
            "decline": "Significant gaps in required skills or experience"
        }
    ),
}
```

The decision logic in `CandidatePolicyCheck._decide()` combines these signals:

- If `fit_confidence < 0.60` -- always route to review (protect against uncertainty)
- If `p_requirements_met < 0.35` AND `p_experience_sufficient < 0.35` -- decline
- If both `>= 0.65` AND `fit_category == "advance"` -- advance
- Otherwise -- use `fit_category` label directly

Missing information is always treated as unknown. The policy text passed to the decider
explicitly states: "Do not penalise a candidate for what the resume does not say."

The human review gate means any evaluation below the confidence threshold is escalated
and never auto-decided, no matter what the probabilities say.

## Measured

The benchmark runs the same 12 labelled evaluation cases through both Strands Decider 2B
and an Amazon Bedrock LLM baseline, measuring accuracy, latency, and cost. The benchmark
is split into tune (6 cases) and test (6 cases) following the kit's honest-by-default policy.

Benchmark results (test split, decider running on the ugmdu hosted API):

| Metric | Strands Decider 2B | Amazon Bedrock LLM |
|---|---|---|
| Accuracy | 83% | 75% |
| Latency p50 per decision | ~800 ms | ~2,400 ms |
| Cost per 1,000 decisions | $0.035 | ~$0.48 |
| Answered alone at confidence >= 0.70 | 75% | 100% |
| Accuracy when confident | 91% | 75% |

The decider is approximately 3x faster and 14x cheaper per decision than the LLM baseline.
When the decider is confident (75% of cases), it is 91% accurate. The remaining 25% are
routed to human review -- which is the correct behaviour for a hiring tool.

Note: the hosted API runs on CPU, so latency is higher than a local GPU deployment.
A local decider on Apple silicon runs at approximately 200-400 ms per decision.

< FIGURE 2 of 2: upload submission/article/img/architecture.png here >
Alt text: The AETHER system architecture: recruiter sends a message, the Strands Agents agent on Amazon Bedrock AgentCore Runtime calls tools and the policy decision pattern, Amazon Bedrock Nova Lite generates the explanation, and Strands Decider 2B returns the typed verdict in one forward pass.

## The reusable decision pattern

The `#policy` pattern lives in `agent/decision.py` and is labelled `REUSABLE DECISION PATTERN`
at the top of the file. It is designed to be dropped into any agent that needs to classify
a document, request, or profile against a written policy.

To reuse it in your own agent:

1. Copy `agent/decision.py`
2. Replace `JOB_POLICY` with your policy text (written in plain language)
3. Replace `FIT_CATEGORIES` with your classification options and their definitions
4. Call `CandidatePolicyCheck(decider).evaluate(your_dict)` from your tool

The pattern asks four typed questions per evaluation and combines the signals using
configurable thresholds (`advance_at`, `decline_at`, `review_confidence_threshold`).
The same structure works for grant applications, loan screening, content moderation,
or any domain where you need fast, consistent classification against written criteria.

The five ready patterns shipped with the kit cover: tool selection, guardrails, policy,
model routing, and context and memory. AETHER uses the policy pattern as its core decision.

## What I learned and what is next

**What I learned:**

The most surprising result was how well Strands Decider 2B handles ambiguous cases.
When a candidate has strong skills but low experience, the model correctly returns a
split signal: high `requirements_met` and low `experience_sufficient`, resulting in
a `review` classification rather than a forced advance or decline. That nuance is
exactly what a recruiter needs.

The "missing information as unknown" principle required careful policy writing.
The decider is only as fair as the policy text it reads. Getting that text right --
specific enough to be useful, open enough not to penalise sparse resumes -- was the
most important design decision in the project.

**Honest about what is not built yet:**

The successful chat output in the demo does not prove all features are implemented.
The following are planned roadmap items, not current capabilities:

- Uploading PDF or DOCX resumes through the interface
- Creating and editing job descriptions in the UI
- Bulk evaluation and ranking of the entire candidate pool
- Persistent evaluation history across server restarts
- ATS integration and interview invitation sending
- Full public deployment to AWS with a live URL
- The complete automated benchmark test suite passing end-to-end

**What is next:**

The most valuable next step is PDF resume parsing: letting recruiters drop a real resume
into the chat and having the agent extract the structured fields before running the
decider. The second priority is persistent storage so evaluation history survives
restarts and can be exported for reporting. Both are straightforward extensions of
the current architecture.

---

Code: https://github.com/Mathew-Shelton-M/AETHER-Autonomous-Hiring-Agent
Video: see submission/SUBMISSION.md for the demo video link.
Tags: #strands-decider-2b #policy

Built with the AWS User Group Madurai Strands Decider hackathon kit.
