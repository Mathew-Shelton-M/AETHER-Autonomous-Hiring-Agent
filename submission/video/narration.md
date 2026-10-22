## title
Welcome to AETHER — the Adaptive Evaluation and Talent Hiring Engine for Recruiters. AETHER helps recruiters evaluate candidate resumes against job requirements using Strands Decider 2B for every typed compatibility decision, and Amazon Bedrock Nova Lite for conversation and explanation.

## architecture
Here is how AETHER works. The recruiter sends a message. Amazon Bedrock calls the evaluate candidate tool, which builds a structured assessment. Strands Decider 2B then runs a single forward pass using the policy pattern and returns advance, review, or decline with a calibrated confidence score. Missing information is always treated as unknown, never as evidence of absence.

## step1_list_jobs
The recruiter asks AETHER to list all open roles. AETHER calls the list jobs tool and returns the three current openings: a Senior Backend Engineer, an ML Engineer, and a Product Manager for Developer Tools.

## step2_advance
The recruiter evaluates Ananya Krishnan for the Senior Backend Engineer role. AETHER fetches the resume and job profile, then Strands Decider 2B runs its policy check. Requirements met probability is zero point nine four. Experience sufficient is zero point nine one. Fit confidence is zero point eight eight. The verdict is ADVANCE TO INTERVIEW.

## step3_review
Now the recruiter evaluates Rohan Mehta for the ML Engineer role. Requirements met scores zero point seven two — his skills are present. But experience sufficient drops to zero point three one — he is two years below the minimum. Fit confidence is zero point five four, below the threshold. The decider flags this for human review. The human review gate ensures this evaluation never auto-advances.

## step4_strong_ml
Lin Wei is evaluated for the ML Engineer role. Requirements met is zero point nine seven. Experience sufficient is zero point eight nine. Fit confidence is zero point nine one — the highest in this demo. The decider advances her with high confidence. All preferred skills including MLflow and transformer models are also evidenced.

## step5_explanation
The recruiter asks why C-102 was flagged instead of advanced. AETHER explains using only the evidence in the resume — no invented information. The experience gap is the primary signal: one year against a three-year minimum. Skills are present but experience sufficiency scores zero point three one. Missing context is treated as unknown, not as proof of inability. The final decision stays with the recruiter.

## decision_pattern
The reusable decision pattern at the heart of AETHER is the policy pattern, hash policy. Strands Decider 2B answers four typed questions in one forward pass: are requirements met, is experience sufficient, how strong is the evidence, and what is the fit category. The decision logic uses probability thresholds to derive the final verdict while protecting against uncertainty.

## future
This demo shows the core evaluation flow. Several features are planned but not yet implemented. These include uploading PDF or DOCX resumes through the interface, creating and editing job descriptions in the UI, bulk evaluation and candidate ranking, persistent evaluation history across restarts, ATS integration and interview invitation sending, AWS public deployment, and the complete automated test suite. The successful chat output you saw does not prove these features are built. They are honest roadmap items for future development.

## outro
AETHER demonstrates that Strands Decider 2B is well-suited for structured recruitment decisions — fast, consistent, and evidence-based. One forward pass per candidate. Typed answers with calibrated confidence. Human review always in the loop. The final hiring decision always stays with the recruiter. Built with the AWS User Group Madurai Strands Decider hackathon kit.