#!/usr/bin/env python3
"""Check a SPAC 525 draft against Lisaney's academic style rules (the 525 rule).

Usage:
    python check_draft.py draft.txt [--skip-last N] [--max 149]
    python check_draft.py draft.docx

Paragraphs are separated by blank lines (.txt) or are Word paragraphs (.docx).
Short lines without ending punctuation (titles, headings, title page lines)
are treated as headings and skipped. Checking stops at a "References" heading.
--skip-last N excludes the final N paragraphs (e.g. references with no heading).
Exit code 0 when clean, 1 when anything is flagged.
"""
import argparse
import html
import re
import sys
import zipfile

BANNED = [
    "delve", "elevate", "foster", "unlock", "landscape", "underscore",
    "pivotal", "testament", "beacon", "tapestry", "realm", "garner", "vital",
]

AI_WORDS = [
    "intricate", "crucial", "showcase", "enhance", "vibrant", "boast",
    "align with", "seamless", "robust", "multifaceted", "ever-evolving",
    "holistic", "additionally", "moreover", "furthermore", "groundbreaking",
    "cutting-edge", "game-changer", "leverag", "sharpens", "in addition",
    "on the other hand",
]

AI_PHRASES = [
    r"it is (important|worth|crucial|essential) to (note|mention|remember|consider)",
    r"worth (noting|mentioning)", r"in conclusion", r"in summary", r"\bin short\b",
    r"\boverall,", r"\bsimply put\b", r"\bbottom line\b", r"\bbluf\b", r"key takeaway",
    r"plays? an? (key|vital|significant|crucial|important|pivotal) role",
    r"stands? as an?", r"serves? as an?", r"lasting (impact|legacy)",
    r"enduring legacy", r"key turning point", r"watershed moment",
    r"deeply rooted", r"rich (cultural )?(heritage|history|tapestry)",
    r"broader (movement|context|landscape)",
    r"\bnot (just|only|merely) [^.;]{1,60}[,;] (but|it is|it's)",
    r"\bis not (just|only|merely|simply) [^.;]{1,60}\. (it|this|that) is\b",
    r"some (critics|experts|observers|scholars|analysts) (argue|say|suggest|note)",
    r"experts (say|agree|suggest)", r"industry reports", r"observers (note|say)",
    r"no discussion (of [^.]+ )?would be complete",
    r", (highlighting|underscoring|emphasizing|reflecting|ensuring|showcasing|demonstrating) ",
    r"from [a-z ]{3,30} to [a-z ]{3,30}, ",
    r"navigat(e|es|ing) (the|these|this|complex|challenges|uncertainty)",
    r"great (point|post|job|question)", r"i really enjoyed",
    r"this is a (strong|great) (presentation|post)",
    r"i hope this helps", r"\bcertainly!",
]

# Weak opinion openers at the start of a paragraph; "I believe" at any sentence start.
WEAK_OPENER = re.compile(r"^(i believe|i think|i feel|in my opinion)\b")
I_BELIEVE = re.compile(r"(^|[.!?]\s+)i believe\b")

APOS = "['’]"
CONTRACTION = re.compile(
    r"\b\w+" + APOS + r"(t|re|ve|ll|d|m)\b|\b(it|that|there|here|what|who|he|she|let)" + APOS + r"s\b",
    re.IGNORECASE,
)
POSSESSIVE = re.compile(r"\b\w+" + APOS + r"s\b|\b\w+s" + APOS + r"(?=\s)", re.IGNORECASE)
EM_DASH = re.compile("—|–| -- |(?<=\\w)--(?=\\w)")
PAGE_CITE = re.compile(r"\([^()]*\d{4}[a-z]?,\s*(p|pp|para)\.\s*\d", re.IGNORECASE)
COLON = re.compile(r":(?!\d)|(?<!\d):")
MARKDOWN = re.compile(r"\*\*|__|^\s*([-*•]|\d+\.)\s", re.MULTILINE)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def is_heading(par: str) -> bool:
    words = par.split()
    return par.lstrip().startswith("#") or (len(words) < 15 and not par.rstrip().endswith((".", "?", "!", ":", ";")))


def read_paragraphs(path: str) -> list[str]:
    if path.lower().endswith(".docx"):
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        pars = []
        for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.DOTALL):
            p = re.sub(r"<w:tab/>", " ", p)
            text = "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", p, re.DOTALL))
            pars.append(html.unescape(text).strip())
        return [p for p in pars if p]
    text = open(path, encoding="utf-8").read()
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--skip-last", type=int, default=0)
    ap.add_argument("--max", type=int, default=149)
    args = ap.parse_args()

    pars = read_paragraphs(args.file)
    if args.skip_last:
        pars = pars[: -args.skip_last] if args.skip_last < len(pars) else []

    problems = 0
    n = 0
    for par in pars:
        if par.strip().strip("#* ").lower() == "references":
            break
        if is_heading(par):
            continue
        n += 1
        flat = " ".join(par.split())
        low = flat.lower()
        wc = len(flat.split())
        issues = []
        if wc > args.max:
            issues.append(f"length {wc} words (cap is {args.max})")
        if not re.search(r"[.!?]\s+\S", flat):
            issues.append("one-sentence paragraph")
        contractions = {m.group(0) for m in CONTRACTION.finditer(flat)}
        if contractions:
            issues.append("contractions: " + ", ".join(sorted(contractions)))
        poss = {m.group(0) for m in POSSESSIVE.finditer(flat)} - contractions
        if poss:
            issues.append("possessive apostrophes: " + ", ".join(sorted(poss)))
        if EM_DASH.search(flat):
            issues.append("em/en dash or double hyphen")
        banned = [w for w in BANNED if re.search(r"\b" + w + r"\w*", low)]
        if banned:
            issues.append("banned words: " + ", ".join(banned))
        aiw = [w for w in AI_WORDS if re.search(r"\b" + re.escape(w) + r"\w*", low)]
        if aiw:
            issues.append("AI-flavored words: " + ", ".join(aiw))
        hits = [m.group(0) for p in AI_PHRASES for m in [re.search(p, low)] if m]
        if hits:
            issues.append("AI patterns: " + " | ".join(h.strip() for h in hits))
        if WEAK_OPENER.search(low) or I_BELIEVE.search(low):
            issues.append("weak opinion opener (I believe / I think / I feel / In my opinion)")
        if PAGE_CITE.search(flat):
            issues.append("page or paragraph number in an in-text citation")
        if flat.count(";") > 1:
            issues.append(f"{flat.count(';')} semicolons (max 1 per paragraph, ideally 0 in replies)")
        colons = len(COLON.findall(flat))
        if colons > 1:
            issues.append(f"{colons} colons (max 1 per paragraph)")
        if MARKDOWN.search(par) or EMOJI.search(flat):
            issues.append("formatting tell (bold, bullets, or emoji in prose)")

        status = "OK" if not issues else "FIX"
        print(f"Paragraph {n} [{wc} words] {status}: {flat[:70]}...")
        for i in issues:
            print(f"    - {i}")
        problems += bool(issues)

    print(f"\n{n} paragraphs checked, {problems} need fixes.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
