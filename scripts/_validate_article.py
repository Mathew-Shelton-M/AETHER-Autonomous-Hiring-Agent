"""Validate the submission/article/ bundle."""
import re
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
ART    = ROOT / "submission" / "article"
CREDIT = "Built with the AWS User Group Madurai Strands Decider hackathon kit"

body   = (ART / "body.md").read_text(encoding="utf-8")
fields = (ART / "fields.md").read_text(encoding="utf-8")

problems = []

# TODOs
if "TODO" in body:
    problems.append("body.md still has TODO sections")

# title
t = re.search(r"Title.*?:\n(.+)", fields)
if t:
    tl = len(t.group(1).strip())
    print(f"Title length   : {tl} chars  (max 255)")
    if tl > 255:
        problems.append("title > 255 chars")
else:
    problems.append("no title in fields.md")

# description
desc = re.search(r"Description.*?:\n(.+)", fields)
if desc:
    dl = len(desc.group(1).strip())
    print(f"Description    : {dl} chars  (max 512)")
    if dl > 512:
        problems.append("description > 512 chars")
else:
    problems.append("no description in fields.md")

# required tag
if "strands-decider-2b" in fields:
    print("Tag            : strands-decider-2b present")
else:
    problems.append("strands-decider-2b tag missing from fields.md")

# attribution
if CREDIT in body:
    print("Attribution    : present")
else:
    problems.append("attribution line missing from body.md")

# word count
wc = len(body.split())
print(f"Word count     : {wc}")

# figures
figs = re.findall(r"< FIGURE \d+ of \d+: upload (\S+) here >", body)
print(f"Figures cited  : {len(figs)}")
for fig in figs:
    exists = (ROOT / fig).exists()
    print(f"  {fig}: {'OK' if exists else 'MISSING'}")
    if not exists:
        problems.append(f"missing figure file: {fig}")

# non-ASCII
bad = sorted({c for c in body if ord(c) > 127})
if bad:
    problems.append(f"non-ASCII chars: {''.join(bad[:20])}")
    print(f"Non-ASCII      : {bad[:10]}")
else:
    print("Non-ASCII      : none")

# cover image
cover = ART / "cover.png"
print(f"Cover image    : {'OK' if cover.exists() else 'MISSING'}")
if not cover.exists():
    problems.append("cover.png missing")

print()
if problems:
    print("Problems to fix:")
    for p in problems:
        print(f"  - {p}")
else:
    print("Validation PASSED - article is ready for Builder Center")
