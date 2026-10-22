"""Generate cover.png and img/architecture.png for the article using Pillow only."""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ART  = ROOT / "submission" / "article"
IMG  = ART / "img"
ART.mkdir(parents=True, exist_ok=True)
IMG.mkdir(parents=True, exist_ok=True)

BG     = (10, 16, 34)
ORANGE = (255, 153, 0)
BRAND  = (99, 102, 241)
GREEN  = (52, 211, 153)
RED    = (248, 113, 113)
AMBER  = (251, 191, 36)
BLUE   = (96, 165, 250)
MUTED  = (42, 58, 94)
WHITE  = (228, 234, 246)
SURF   = (18, 26, 52)

# ── helpers ───────────────────────────────────────────────────────────────────
def _font(size: int, bold: bool = False):
    from PIL import ImageFont
    candidates = (
        ["C:/Windows/Fonts/arialbd.ttf"] if bold else
        ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"]
    )
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


# ── cover (1200×675, text-free per Builder Center rules) ─────────────────────
def make_cover() -> None:
    W, H = 1200, 675
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)

    # grid
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=(20, 30, 55), width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=(20, 30, 55), width=1)

    # orange glow top-right
    for r in range(300, 0, -6):
        t = 1 - r / 300
        c = tuple(min(255, int(BG[i] + (ORANGE[i] - BG[i]) * t * 0.55)) for i in range(3))
        d.ellipse([W - r - 180, -r // 2, W - 180 + r, r], fill=c)

    # resume card (left)
    d.rounded_rectangle([90, 230, 340, 445], radius=18, fill=SURF, outline=BLUE, width=3)
    for i, (ow, col) in enumerate([(200, BLUE), (160, MUTED), (180, MUTED), (140, MUTED)]):
        d.rounded_rectangle([120, 265 + i * 42, 120 + ow, 279 + i * 42], radius=5, fill=col)

    # arrow left → decider
    d.line([(342, 337), (514, 337)], fill=AMBER, width=4)
    d.polygon([(514, 327), (514, 347), (530, 337)], fill=AMBER)

    # decider circle
    cx, cy = 614, 337
    for r, alpha in [(110, 40), (90, 80)]:
        c = tuple(min(255, int(BG[i] + (ORANGE[i] - BG[i]) * alpha / 255)) for i in range(3))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    d.ellipse([cx - 80, cy - 80, cx + 80, cy + 80], fill=ORANGE)
    d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=WHITE)

    # arrows decider → outcome cards
    arrow_data = [
        (cy - 40, 190, GREEN),
        (cy,      337, AMBER),
        (cy + 40, 484, RED),
    ]
    for start_y, end_y, col in arrow_data:
        d.line([(cx + 82, start_y), (850, end_y)], fill=col, width=4)
        d.polygon([(846, end_y - 8), (846, end_y + 8), (862, end_y)], fill=col)

    # outcome cards
    for oy, col in [(155, GREEN), (303, AMBER), (451, RED)]:
        d.rounded_rectangle([860, oy, 1150, oy + 68], radius=14, fill=SURF, outline=col, width=3)
        d.rounded_rectangle([896, oy + 20, 896 + 110, oy + 36], radius=5, fill=col)
        d.rounded_rectangle([896, oy + 44, 896 + 80,  oy + 56], radius=4, fill=MUTED)

    out = ART / "cover.png"
    img.save(str(out))
    print(f"[images] cover saved: {out}")


# ── architecture (1200×620) ───────────────────────────────────────────────────
def make_architecture() -> None:
    W, H = 1200, 620
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d   = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], fill=(248, 250, 252))

    boxes = [
        # (x, y, w, h, title, subtitle, border_colour, bg_colour)
        (30,  255, 155, 110, "Recruiter",       "chat / API",               (148,163,184), (241,245,249)),
        (248, 90,  504, 440, "Agent (Strands Agents)",
                                                "Amazon Bedrock AgentCore Runtime", (255,153,0),   (255,247,237)),
        (278, 175, 200, 100, "Tools",            "agent/tools.py",           (99,102,241),  (238,242,255)),
        (498, 175, 220, 100, "Decision #policy", "agent/decision.py",        (255,153,0),   (255,247,237)),
        (278, 310, 444, 100, "Agent loop",       "model call -> decision -> tool call -> reply",
                                                                              (34,197,94),   (240,253,244)),
        (800, 90,  360, 160, "Amazon Bedrock",   "Nova Lite: conversation\nand explanation",
                                                                              (124,58,237),  (245,243,255)),
        (800, 310, 360, 190, "Strands Decider 2B","#policy pattern\nOne forward pass:\nadvance / review / decline",
                                                                              (255,153,0),   (255,250,235)),
    ]

    for bx, by, bw, bh, title, sub, border, bg in boxes:
        d.rounded_rectangle([bx, by, bx+bw, by+bh], radius=12, fill=bg, outline=border, width=2)
        d.text((bx+14, by+12), title, font=_font(17, bold=True), fill=(15,23,42))
        for li, line in enumerate(sub.split("\n")):
            d.text((bx+14, by+36+li*19), line, font=_font(14), fill=(71,85,105))

    # arrows
    arrows = [
        (185, 310, 248, 310, (148,163,184)),   # user -> agent
        (752, 245, 800, 200, (124,58,237)),     # agent -> bedrock
        (752, 360, 800, 405, (255,153,0)),      # agent -> decider
    ]
    for x1,y1,x2,y2,col in arrows:
        d.line([(x1,y1),(x2,y2)], fill=col, width=3)
        dx, dy = x2-x1, y2-y1
        length = (dx**2+dy**2)**0.5
        ux, uy = dx/length, dy/length
        px, py = -uy*7, ux*7
        d.polygon([
            (int(x2-ux*14+px), int(y2-uy*14+py)),
            (int(x2-ux*14-px), int(y2-uy*14-py)),
            (x2, y2)
        ], fill=col)

    # credit
    d.text((30, H-30), "Built with the AWS User Group Madurai Strands Decider hackathon kit",
           font=_font(13), fill=(100,116,139))

    out = IMG / "architecture.png"
    img.save(str(out))
    print(f"[images] architecture saved: {out}")


if __name__ == "__main__":
    make_cover()
    make_architecture()
    print("[images] done.")
