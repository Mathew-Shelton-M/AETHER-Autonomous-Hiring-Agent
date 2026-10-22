# Use case

AETHER — Adaptive Evaluation and Talent Hiring Engine for Recruiters.

- **Pitch:** a recruiter-facing AI that evaluates candidate resumes against job requirements and
  decides whether to advance, flag for human review, or decline — without inventing evidence.
- **Who it is for:** recruiters and hiring managers screening candidates at volume; any team
  that needs consistent, explainable, bias-aware shortlisting.
- **Features:**
  - load job profiles and candidate resumes (synthetic data ships with the kit; bring your own);
  - evaluate compatibility across skills, experience, qualifications and culture alignment;
  - every evaluation decision made by Strands Decider 2B: advance / review / decline with a
    confidence score and a plain-English explanation;
  - missing evidence treated as unknown, never as proof of absence;
  - human review gate: evaluations below confidence threshold are escalated, never auto-advanced;
  - AETHER recruiter dashboard: job panel, candidate cards, decision confidence bar, explanation;
  - deployed on Amazon Bedrock AgentCore Runtime.
- **The decision handed to Strands Decider 2B:** does this candidate's resume meet the job's
  requirements, fall into a review band, or show significant evidence gaps? (`#policy`)
- **Why a decision model:** the check must be consistent, fast and auditable across hundreds of
  candidates; a typed probability lets the recruiter set their own confidence threshold.
- **Amazon Bedrock:** the conversation, resume parsing and explanation generation (Amazon Nova Lite).

Built with the AWS User Group Madurai Strands Decider hackathon kit.
