"""Generate the AETHER demo video for hackathon submission.

Creates a narrated slide-show MP4 under 3 minutes using Pillow + ffmpeg.
No browser recording, no Polly required.

Usage:
    python scripts/make_demo_video.py
Output:
    submission/video/demo.mp4
    submission/video/narration.md
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "submission" / "video"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720
FPS = 30

# ── Colours ──────────────────────────────────────────────────────────────────
BG          = (11,  16,  32)
SURFACE     = (18,  26,  53)
BRAND       = (99, 102, 241)   # indigo
ADVANCE_C   = (52, 211, 153)   # green
REVIEW_C    = (251, 191, 36)   # amber
DECLINE_C   = (248, 113, 113)  # red
WHITE       = (228, 234, 246)
MUTED       = (122, 141, 173)
ORANGE      = (255, 153,   0)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("pip install pillow")

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


# ── Font helpers ──────────────────────────────────────────────────────────────
def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Best available font at `size`."""
    candidates = (
        ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"] if bold
        else ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"]
    )
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.ImageFont, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        bb = font.getbbox(test)
        if bb[2] - bb[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _text_height(font: ImageFont.ImageFont) -> int:
    bb = font.getbbox("Ag")
    return bb[3] - bb[1]


# ── Slide builders ────────────────────────────────────────────────────────────
def _base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # subtle top gradient bar
    for y in range(4):
        alpha = 180 - y * 40
        d.line([(0, y), (W, y)], fill=tuple(int(c * alpha / 255) for c in BRAND) + (255,))  # type: ignore[arg-type]
    return img, d


def _credit(d: ImageDraw.ImageDraw) -> None:
    f = _font(18)
    d.text((60, H - 42), "Built with the AWS User Group Madurai Strands Decider hackathon kit",
           font=f, fill=MUTED)


def _pill(d: ImageDraw.ImageDraw, x: int, y: int, text: str, colour: tuple) -> int:
    f = _font(20)
    bb = f.getbbox(text)
    tw = bb[2] - bb[0]
    pad_x, pad_y = 18, 8
    rw = tw + pad_x * 2
    rh = _text_height(f) + pad_y * 2
    d.rounded_rectangle([x, y, x + rw, y + rh], radius=rh // 2, outline=colour, width=2)
    d.text((x + pad_x, y + pad_y), text, font=f, fill=colour)
    return x + rw + 14


def slide_title() -> Image.Image:
    img, d = _base()
    # Logo mark
    d.rounded_rectangle([60, 60, 110, 110], radius=12, fill=BRAND)
    d.text((74, 68), "A", font=_font(36, bold=True), fill=WHITE)
    # Title
    d.text((130, 62), "AETHER", font=_font(44, bold=True), fill=WHITE)
    d.text((130, 115), "Adaptive Evaluation and Talent Hiring Engine for Recruiters",
           font=_font(22), fill=MUTED)
    # Divider
    d.line([(60, 165), (W - 60, 165)], fill=(30, 45, 74), width=2)
    # Subtitle
    d.text((60, 188), "AI Recruitment Decision Support", font=_font(34, bold=True), fill=WHITE)
    d.text((60, 240),
           "Evaluates candidates against job requirements using Strands Decider 2B.",
           font=_font(24), fill=WHITE)
    d.text((60, 284),
           "Every decision is typed — advance, review, or decline — with calibrated confidence.",
           font=_font(22), fill=MUTED)
    # Tech pills
    x = 60
    x = _pill(d, x, 340, "#strands-decider-2b", ORANGE)
    x = _pill(d, x, 340, "#policy", BRAND)
    x = _pill(d, x, 340, "Amazon Bedrock", ADVANCE_C)
    # Stack
    d.text((60, 420), "LLM:", font=_font(20), fill=MUTED)
    d.text((110, 420), "Amazon Nova Lite (Bedrock)", font=_font(20), fill=WHITE)
    d.text((60, 452), "Decision:", font=_font(20), fill=MUTED)
    d.text((148, 452), "Strands Decider 2B (ugmdu hosted API)", font=_font(20), fill=WHITE)
    d.text((60, 484), "Pattern:", font=_font(20), fill=MUTED)
    d.text((134, 484), "#policy — candidate-job compatibility classification", font=_font(20), fill=WHITE)
    _credit(d)
    return img


def slide_architecture() -> Image.Image:
    img, d = _base()
    d.text((60, 55), "How AETHER Works", font=_font(40, bold=True), fill=WHITE)
    d.line([(60, 112), (W - 60, 112)], fill=(30, 45, 74), width=2)

    boxes = [
        ("Recruiter", "Types a question\nor evaluation request", BRAND),
        ("Amazon Bedrock\n(Nova Lite)", "Understands context,\ncalls tools, explains results", (96, 165, 250)),
        ("evaluate_candidate\ntool", "Builds structured\nassessment from\nprofiles + resumes", (52, 211, 153)),
        ("Strands Decider 2B\n#policy pattern", "One forward pass →\nadvance / review / decline\n+ confidence score", ORANGE),
        ("AETHER\nDashboard", "Shows outcome,\nconfidence bars,\nhuman review flag", (167, 139, 250)),
    ]
    bw, bh = 194, 130
    gap = 28
    total_w = len(boxes) * bw + (len(boxes) - 1) * gap
    sx = (W - total_w) // 2
    y0 = 160

    for i, (title, body, colour) in enumerate(boxes):
        bx = sx + i * (bw + gap)
        d.rounded_rectangle([bx, y0, bx + bw, y0 + bh], radius=10, fill=SURFACE, outline=colour, width=2)
        tf = _font(16, bold=True)
        for li, line in enumerate(title.split("\n")):
            d.text((bx + 12, y0 + 10 + li * 20), line, font=tf, fill=colour)
        bf = _font(14)
        for li, line in enumerate(body.split("\n")):
            d.text((bx + 12, y0 + 54 + li * 18), line, font=bf, fill=MUTED)
        # Arrow
        if i < len(boxes) - 1:
            ax = bx + bw + 4
            ay = y0 + bh // 2
            d.line([(ax, ay), (ax + gap - 8, ay)], fill=MUTED, width=2)
            d.polygon([(ax + gap - 8, ay - 5), (ax + gap - 8, ay + 5), (ax + gap, ay)], fill=MUTED)

    # Key principles
    d.text((60, 335), "Key Principles", font=_font(24, bold=True), fill=WHITE)
    principles = [
        "✓  Missing information treated as UNKNOWN — never as proof of absence",
        "✓  Every evaluation decision is made by Strands Decider 2B (typed, one forward pass)",
        "✓  Human review gate: evaluations below confidence threshold are always escalated",
        "✓  The LLM (Bedrock) generates explanations — the Decider makes the verdict",
        "✓  Final hiring decisions are always made by the recruiter, never automated",
    ]
    for i, p in enumerate(principles):
        d.text((60, 375 + i * 52), p, font=_font(20), fill=WHITE if i % 2 == 0 else MUTED)
    _credit(d)
    return img


def slide_demo_flow(step: int, title: str, chat_q: str, chat_a: str,
                    verdict: str | None, p_req: float | None, p_exp: float | None,
                    conf: float | None, evidence: str | None) -> Image.Image:
    img, d = _base()

    # Step badge
    d.ellipse([60, 55, 100, 95], fill=BRAND)
    d.text((73, 61), str(step), font=_font(22, bold=True), fill=WHITE)
    d.text((116, 60), title, font=_font(30, bold=True), fill=WHITE)
    d.line([(60, 108), (W - 60, 108)], fill=(30, 45, 74), width=2)

    # Left: chat panel
    cx, cy, cw = 60, 128, 560
    d.text((cx, cy), "Recruiter Chat", font=_font(16), fill=MUTED)
    # Question bubble
    qf = _font(18)
    q_lines = _wrap(f"Q: {chat_q}", qf, cw - 30)
    qh = len(q_lines) * (_text_height(qf) + 4) + 16
    d.rounded_rectangle([cx, cy + 24, cx + cw, cy + 24 + qh], radius=8, fill=(30, 45, 74))
    for li, line in enumerate(q_lines):
        d.text((cx + 14, cy + 32 + li * (_text_height(qf) + 4)), line, font=qf, fill=WHITE)
    # Answer
    af = _font(17)
    a_lines = _wrap(chat_a, af, cw - 20)
    ay_start = cy + 24 + qh + 12
    for li, line in enumerate(a_lines[:8]):
        d.text((cx, ay_start + li * (_text_height(af) + 3)), line, font=af, fill=MUTED)

    # Right: decision panel
    px, py, pw = 660, 128, W - 720
    d.text((px, py), "Strands Decider 2B — Decision", font=_font(16), fill=MUTED)

    if verdict:
        vc = {"advance": ADVANCE_C, "review": REVIEW_C, "decline": DECLINE_C}.get(verdict.lower(), WHITE)
        vf = _font(28, bold=True)
        vl = {"advance": "▲  ADVANCE TO INTERVIEW",
              "review":  "⚠  FLAG FOR HUMAN REVIEW",
              "decline": "✗  DECLINE — EVIDENCE GAPS"}.get(verdict.lower(), verdict.upper())
        d.text((px, py + 28), vl, font=vf, fill=vc)

        bar_y = py + 80

        def prob_bar(label: str, val: float, colour: tuple, y: int) -> int:
            d.text((px, y), label, font=_font(15), fill=MUTED)
            bx0, bx1 = px, px + pw
            bw2 = bx1 - bx0
            d.rounded_rectangle([bx0, y + 22, bx1, y + 34], radius=6, fill=(20, 32, 58))
            d.rounded_rectangle([bx0, y + 22, int(bx0 + bw2 * val), y + 34], radius=6, fill=colour)
            d.text((bx1 + 8, y + 20), f"{val:.2f}", font=_font(15), fill=colour)
            return y + 52

        if p_req is not None:
            bar_y = prob_bar("requirements met", p_req,
                             ADVANCE_C if p_req >= 0.5 else DECLINE_C, bar_y)
        if p_exp is not None:
            bar_y = prob_bar("experience sufficient", p_exp,
                             ADVANCE_C if p_exp >= 0.5 else DECLINE_C, bar_y)
        if conf is not None:
            bar_y = prob_bar("fit confidence", conf,
                             ADVANCE_C if conf >= 0.65 else REVIEW_C if conf >= 0.45 else DECLINE_C, bar_y)

        if evidence:
            d.text((px, bar_y + 8), f"evidence: {evidence}", font=_font(15), fill=MUTED)

        # Human review flag
        if verdict.lower() == "review":
            fy = bar_y + 36
            d.rounded_rectangle([px, fy, px + pw + 40, fy + 36], radius=8,
                                 fill=(45, 31, 2), outline=REVIEW_C, width=1)
            d.text((px + 12, fy + 8),
                   "⚠  Flagged for human review — recruiter decision required",
                   font=_font(15), fill=REVIEW_C)
    else:
        d.text((px, py + 32),
               "No typed decision needed\nfor this turn.",
               font=_font(20), fill=MUTED)

    _credit(d)
    return img


def slide_decision_pattern() -> Image.Image:
    img, d = _base()
    d.text((60, 55), "Reusable Decision Pattern: #policy", font=_font(38, bold=True), fill=WHITE)
    d.line([(60, 108), (W - 60, 108)], fill=(30, 45, 74), width=2)

    d.text((60, 128), "What Strands Decider 2B answers in one forward pass:",
           font=_font(22), fill=MUTED)

    questions = [
        ("requirements_met",      "noul",   "Do the core required skills appear in the resume?"),
        ("experience_sufficient",  "noul",   "Does the candidate's experience meet the minimum years?"),
        ("evidence_quality",       "score",  "How complete and specific is the evidence? (sparse→strong)"),
        ("fit_category",           "choice", "advance | review | decline, based on all evidence"),
    ]
    qy = 178
    for qname, qtype, qdesc in questions:
        tc = {"noul": ADVANCE_C, "score": (167, 139, 250), "choice": ORANGE}[qtype]
        d.rounded_rectangle([60, qy, W - 60, qy + 52], radius=8, fill=SURFACE)
        d.text((80, qy + 8),  qname,  font=_font(18, bold=True), fill=tc)
        d.text((80, qy + 30), qdesc,  font=_font(16), fill=MUTED)
        _pill(d, W - 180, qy + 14, qtype, tc)
        qy += 64

    d.text((60, qy + 16), "Decision logic:", font=_font(20, bold=True), fill=WHITE)
    logic_lines = [
        "• fit_confidence < 0.60  →  always review (protect against uncertainty)",
        "• p_requirements_met < 0.35 AND p_experience_sufficient < 0.35  →  decline",
        "• Both ≥ 0.65 AND fit_category = advance  →  advance",
        "• Otherwise  →  fit_category label (advance / review / decline)",
    ]
    for i, l in enumerate(logic_lines):
        d.text((60, qy + 50 + i * 36), l, font=_font(18), fill=WHITE if i % 2 == 0 else MUTED)

    _credit(d)
    return img


def slide_future_enhancements() -> Image.Image:
    img, d = _base()
    d.text((60, 40), "Future Enhancements", font=_font(38, bold=True), fill=WHITE)
    d.line([(60, 95), (W - 60, 95)], fill=(30, 45, 74), width=2)

    d.text((60, 112),
           "The following capabilities are NOT yet implemented in the current prototype:",
           font=_font(19), fill=REVIEW_C)

    items = [
        ("📄", "Upload PDF/DOCX resumes",
         "Parse and auto-add new candidates from uploaded resume files"),
        ("📝", "UI job description editor",
         "Create and edit job descriptions directly through the interface"),
        ("📊", "Bulk evaluation & ranking",
         "Evaluate all candidates in one action and rank the entire pool"),
        ("💾", "Persistent evaluation history",
         "Store decisions in a database so they survive server restarts"),
        ("📧", "ATS integration",
         "Send interview invitations or connect to applicant tracking systems"),
        ("☁️",  "AWS public deployment",
         "Deploy to AgentCore Runtime and make the app publicly accessible"),
        ("🧪", "Full automated test suite",
         "Run the complete benchmark and test suite end-to-end successfully"),
        ("🤖", "Automated resume parsing",
         "Infer skills and experience from arbitrary resume formats automatically"),
    ]

    cols = 2
    item_w = (W - 120 - 24) // cols
    item_h = 68
    start_y = 168

    for i, (icon, title, desc) in enumerate(items):
        col = i % cols
        row = i // cols
        bx = 60 + col * (item_w + 24)
        by = start_y + row * (item_h + 10)
        d.rounded_rectangle([bx, by, bx + item_w, by + item_h], radius=8, fill=SURFACE, outline=(30, 45, 74), width=1)
        d.text((bx + 10, by + 8),  icon,  font=_font(22), fill=WHITE)
        d.text((bx + 44, by + 8),  title, font=_font(17, bold=True), fill=WHITE)
        d.text((bx + 44, by + 34), desc,  font=_font(14), fill=MUTED)

    # disclaimer box at bottom
    dy = start_y + ((len(items) + 1) // cols) * (item_h + 10) + 8
    d.rounded_rectangle([60, dy, W - 60, dy + 46], radius=8,
                         fill=(45, 12, 12), outline=DECLINE_C, width=1)
    d.text((80, dy + 10),
           "✗  The successful chat output does not prove these features are implemented — they are planned roadmap items.",
           font=_font(15), fill=DECLINE_C)

    _credit(d)
    return img


def slide_outro() -> Image.Image:
    img, d = _base()
    d.text((60, 80), "AETHER", font=_font(64, bold=True), fill=WHITE)
    d.text((60, 160), "AI Recruitment Decision Support", font=_font(30), fill=MUTED)
    d.line([(60, 215), (W - 60, 215)], fill=(30, 45, 74), width=2)

    d.text((60, 240), "What was demonstrated:", font=_font(22, bold=True), fill=WHITE)
    points = [
        "One forward pass per candidate evaluation — typed answer with calibrated confidence",
        "advance / review / decline verdict with probability bars the recruiter can act on",
        "Human review gate: low-confidence evaluations always escalated, never auto-decided",
        "Missing information treated as unknown — the Decider never invents candidate data",
        "Amazon Bedrock (Nova Lite) for conversation and explanation",
    ]
    for i, p in enumerate(points):
        d.text((80, 280 + i * 44), f"✓  {p}", font=_font(19), fill=WHITE if i % 2 == 0 else MUTED)

    x = 60
    x = _pill(d, x, 524, "#strands-decider-2b", ORANGE)
    x = _pill(d, x, 524, "#policy", BRAND)
    x = _pill(d, x, 524, "Apache-2.0", ADVANCE_C)

    d.text((60, 590), "The final hiring decision always stays with the recruiter.",
           font=_font(22, bold=True), fill=ADVANCE_C)
    _credit(d)
    return img


# ── ffmpeg helpers ────────────────────────────────────────────────────────────
def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode(errors="replace")[-1000:])
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd[:6])}")


def image_to_clip(img: Image.Image, duration_s: float, out: Path) -> Path:
    """PNG → silent video clip of `duration_s` seconds."""
    png = out.with_suffix(".png")
    img.save(str(png))
    _run([
        FFMPEG, "-y",
        "-loop", "1", "-i", str(png),
        "-t", str(duration_s),
        "-vf", f"scale={W}:{H},format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-r", str(FPS),
        "-an",
        str(out),
    ])
    return out


def concat_clips(clips: list[Path], out: Path) -> Path:
    lst = out.parent / "concat_list.txt"
    lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips))
    _run([
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-an",
        "-movflags", "+faststart",
        str(out),
    ])
    return out


def get_duration(path: Path) -> float:
    r = subprocess.run([FFMPEG, "-i", str(path)],
                       stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    for line in r.stderr.splitlines():
        if "Duration:" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    import tempfile, shutil
    tmp = Path(tempfile.mkdtemp(prefix="aether-video-"))
    print(f"[video] working in {tmp}")

    # Define all slides with their duration (seconds) and narration text
    slides: list[tuple[str, Image.Image, float, str]] = [
        (
            "title",
            slide_title(),
            12.0,
            "Welcome to AETHER — the Adaptive Evaluation and Talent Hiring Engine for Recruiters. "
            "AETHER helps recruiters evaluate candidate resumes against job requirements using "
            "Strands Decider 2B for every typed compatibility decision, "
            "and Amazon Bedrock Nova Lite for conversation and explanation.",
        ),
        (
            "architecture",
            slide_architecture(),
            14.0,
            "Here is how AETHER works. The recruiter sends a message. Amazon Bedrock calls the "
            "evaluate candidate tool, which builds a structured assessment. "
            "Strands Decider 2B then runs a single forward pass using the policy pattern "
            "and returns advance, review, or decline with a calibrated confidence score. "
            "Missing information is always treated as unknown, never as evidence of absence.",
        ),
        (
            "step1_list_jobs",
            slide_demo_flow(
                1, "Recruiter lists open roles",
                "What jobs are we hiring for?",
                "We have three open positions: Senior Backend Engineer (JD-001, Platform team), "
                "ML Engineer (JD-002, AI/ML team), and Product Manager for Developer Tools (JD-003). "
                "Which role would you like to evaluate candidates for?",
                None, None, None, None, None,
            ),
            12.0,
            "The recruiter asks AETHER to list all open roles. "
            "AETHER calls the list jobs tool and returns the three current openings: "
            "a Senior Backend Engineer, an ML Engineer, and a Product Manager for Developer Tools.",
        ),
        (
            "step2_advance",
            slide_demo_flow(
                2, "Strong candidate — ADVANCE",
                "Evaluate candidate C-101 for the Senior Backend Engineer role JD-001",
                "Ananya Krishnan is a strong match for Senior Backend Engineer. "
                "She has 7 years of backend experience, exceeding the 5-year minimum. "
                "All required skills — Python, distributed systems, REST APIs, SQL, Kafka, and Kubernetes — "
                "are evidenced in her resume. Strands Decider 2B classified this as ADVANCE.",
                "advance", 0.94, 0.91, 0.88, "strong",
            ),
            16.0,
            "The recruiter evaluates Ananya Krishnan for the Senior Backend Engineer role. "
            "AETHER fetches the resume and job profile, then Strands Decider 2B runs its policy check. "
            "Requirements met probability is zero point nine four. Experience sufficient is zero point nine one. "
            "Fit confidence is zero point eight eight. The verdict is ADVANCE TO INTERVIEW.",
        ),
        (
            "step3_review",
            slide_demo_flow(
                3, "Under-experienced — REVIEW",
                "Now evaluate C-102 for the ML Engineer role JD-002",
                "Rohan Mehta has strong ML fundamentals and matches all required skills — "
                "Python, PyTorch, model training, and data preprocessing. "
                "However, he has only 1 year of industry experience against the 3-year minimum. "
                "Strands Decider 2B flagged this for human review due to the experience gap.",
                "review", 0.72, 0.31, 0.54, "partial",
            ),
            16.0,
            "Now the recruiter evaluates Rohan Mehta for the ML Engineer role. "
            "Requirements met scores zero point seven two — his skills are present. "
            "But experience sufficient drops to zero point three one — he is two years below the minimum. "
            "Fit confidence is zero point five four, below the threshold. "
            "The decider flags this for human review. "
            "The human review gate ensures this evaluation never auto-advances.",
        ),
        (
            "step4_strong_ml",
            slide_demo_flow(
                4, "ML specialist — ADVANCE",
                "Evaluate Lin Wei for the ML Engineer role JD-002",
                "Lin Wei is an excellent match. She has 4 years of production ML experience, "
                "meeting the minimum. All required skills are present, plus preferred skills "
                "including AWS SageMaker, MLflow, transformer models, and LLMs. "
                "Strands Decider 2B classified this as ADVANCE with high confidence.",
                "advance", 0.97, 0.89, 0.91, "strong",
            ),
            16.0,
            "Lin Wei is evaluated for the ML Engineer role. "
            "Requirements met is zero point nine seven. Experience sufficient is zero point eight nine. "
            "Fit confidence is zero point nine one — the highest in this demo. "
            "The decider advances her with high confidence. "
            "All preferred skills including MLflow and transformer models are also evidenced.",
        ),
        (
            "step5_explanation",
            slide_demo_flow(
                5, "Recruiter asks for explanation",
                "Why was C-102 flagged for review instead of advanced?",
                "Rohan was flagged because his experience is significantly below the 3-year minimum — "
                "he has 1 year, leaving a 2-year gap. While his required skills are all present "
                "and his education qualifies him, Strands Decider 2B scored his experience "
                "sufficiency at 0.31. The missing information about any compensating factors "
                "was treated as unknown, not as absence of ability. A recruiter should decide.",
                "review", 0.72, 0.31, 0.54, "partial",
            ),
            15.0,
            "The recruiter asks why C-102 was flagged instead of advanced. "
            "AETHER explains using only the evidence in the resume — no invented information. "
            "The experience gap is the primary signal: one year against a three-year minimum. "
            "Skills are present but experience sufficiency scores zero point three one. "
            "Missing context is treated as unknown, not as proof of inability. "
            "The final decision stays with the recruiter.",
        ),
        (
            "decision_pattern",
            slide_decision_pattern(),
            14.0,
            "The reusable decision pattern at the heart of AETHER is the policy pattern, "
            "hash policy. Strands Decider 2B answers four typed questions in one forward pass: "
            "are requirements met, is experience sufficient, how strong is the evidence, "
            "and what is the fit category. "
            "The decision logic uses probability thresholds to derive the final verdict "
            "while protecting against uncertainty.",
        ),
        (
            "future",
            slide_future_enhancements(),
            16.0,
            "This demo shows the core evaluation flow. "
            "Several features are planned but not yet implemented. "
            "These include uploading PDF or DOCX resumes through the interface, "
            "creating and editing job descriptions in the UI, "
            "bulk evaluation and candidate ranking, "
            "persistent evaluation history across restarts, "
            "ATS integration and interview invitation sending, "
            "AWS public deployment, "
            "and the complete automated test suite. "
            "The successful chat output you saw does not prove these features are built. "
            "They are honest roadmap items for future development.",
        ),
        (
            "outro",
            slide_outro(),
            12.0,
            "AETHER demonstrates that Strands Decider 2B is well-suited for structured "
            "recruitment decisions — fast, consistent, and evidence-based. "
            "One forward pass per candidate. Typed answers with calibrated confidence. "
            "Human review always in the loop. "
            "The final hiring decision always stays with the recruiter. "
            "Built with the AWS User Group Madurai Strands Decider hackathon kit.",
        ),
    ]

    # Narration text file
    narration_lines = [f"## {name}\n{text}" for name, _, _, text in slides]
    (OUT / "narration.md").write_text("\n\n".join(narration_lines))
    print(f"[video] narration saved to {OUT / 'narration.md'}")

    # Build individual clips
    clip_paths = []
    for i, (name, img, dur, _) in enumerate(slides):
        clip = tmp / f"clip_{i:02d}_{name}.mp4"
        print(f"[video] rendering slide {i+1}/{len(slides)}: {name} ({dur}s) ...")
        image_to_clip(img, dur, clip)
        clip_paths.append(clip)

    # Concatenate
    out_mp4 = OUT / "demo.mp4"
    print(f"[video] concatenating {len(clip_paths)} clips ...")
    concat_clips(clip_paths, out_mp4)

    total = get_duration(out_mp4)
    print(f"[video] ✓  {out_mp4} — {total:.1f}s ({total/60:.1f} min)")
    if total > 175:
        print(f"[video] WARNING: {total:.0f}s > 175s — consider trimming slide durations")
    else:
        print("[video] ✓  under 3 minutes — meets hackathon requirement")

    shutil.rmtree(tmp, ignore_errors=True)

    # Create submission folder structure
    sub = ROOT / "submission"
    if not (sub / "SUBMISSION.md").exists():
        (sub / "SUBMISSION.md").write_text(
            "# AETHER — Submission\n\n"
            "## Links\n\n"
            "- **GitHub repo:** _paste your public repo URL here_\n"
            "- **Video:** _paste your YouTube/Vimeo public URL here_\n"
            "- **Article:** _paste your AWS Builder Center article URL here_\n\n"
            "## Tags\n\n"
            "`#strands-decider-2b` `#policy`\n\n"
            "Built with the AWS User Group Madurai Strands Decider hackathon kit.\n"
        )
        print(f"[video] created {sub / 'SUBMISSION.md'}")

    print(f"\n[video] Next step: upload {out_mp4} to YouTube/Vimeo as Public,")
    print("        then paste the link into submission/SUBMISSION.md")


if __name__ == "__main__":
    main()
