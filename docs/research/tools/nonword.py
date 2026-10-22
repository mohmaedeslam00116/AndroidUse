#!/usr/bin/env python3
"""Inventory of corpus labels that are not ordinary words."""
import io
import os
import re
import sys
import unicodedata
import collections

sys.stdout.reconfigure(encoding="utf-8")
CORPUS = sys.argv[1]
AR_RE = re.compile(r"[\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufeff]")
LAT_RE = re.compile(r"[A-Za-z]")
FMT_RE = re.compile(r"%(?:\d+\$)?[-#+ 0,(]*\d*(?:\.\d+)?[a-zA-Z%]|%%")
BIDI_RE = re.compile("[\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069]")


def main():
    rows = []
    with io.open(CORPUS, encoding="utf-8") as f:
        for line in f:
            if not line or line.startswith("##"):
                continue
            p = line.rstrip("\n").split("\t")
            rows.append((p[0], p[1] if len(p) > 1 else "", p[2] if len(p) > 2 else ""))

    print("=== A. labels with no letters at all (glyph / punctuation) ===")
    n = 0
    ex = []
    for label, src, name in rows:
        s = FMT_RE.sub("", label)
        if s and not any(unicodedata.category(ch).startswith("L") for ch in s):
            n += 1
            if len(ex) < 30:
                ex.append((label, src, name))
    print("count:", n)
    for label, src, name in ex:
        print("   %-22r %s | %s" % (label[:20], src.replace("apk:", ""), name))

    print()
    print("=== B. labels that are a resource-id / localisation key shipped as a value ===")
    n = 0
    ex = []
    for label, src, name in rows:
        if re.fullmatch(r"[a-z][a-z0-9]*(_[a-z0-9]+)+", label):
            n += 1
            if len(ex) < 25:
                ex.append((label, src, name))
    print("count:", n)
    for label, src, name in ex:
        print("   %-42s %s | %s" % (label, src.replace("apk:", ""), name))

    print()
    print("=== C. mixed-script labels (Latin letters next to Arabic, format specifiers removed) ===")
    n = 0
    ex = []
    for label, src, name in rows:
        s = FMT_RE.sub("", label)
        if AR_RE.search(s) and LAT_RE.search(s):
            n += 1
            if len(ex) < 25:
                ex.append((label, src, name))
    print("count:", n)
    for label, src, name in ex:
        print("   %-58s %s | %s" % (label[:56], src.replace("apk:", ""), name))

    print()
    print("=== D. labels that look like an icon / affordance name ===")
    pat = re.compile(r"^(ic[_ ]|.*\b(arrow|chevron|back arrow|icon)\b)", re.I)
    n = 0
    ex = []
    for label, src, name in rows:
        if pat.search(label):
            n += 1
            if len(ex) < 25:
                ex.append((label, src, name))
    print("count:", n)
    for label, src, name in ex:
        print("   %-40s %s | %s" % (label[:38], src.replace("apk:", ""), name))

    print()
    print("=== E. labels naming a send/pay affordance but not the action ===")
    pat = re.compile(r"(send|pay|buy|purchase|share|submit|post)\b", re.I)
    n = 0
    ex = []
    for label, src, name in rows:
        if pat.search(label) and not pat.fullmatch(label):
            n += 1
            if len(ex) < 30:
                ex.append((label, src, name))
    print("count:", n)
    for label, src, name in ex:
        print("   %-52s %s | %s" % (label[:50], src.replace("apk:", ""), name))

    print()
    print("=== F. bidi control characters in labels ===")
    tot = sum(1 for label, _, _ in rows if BIDI_RE.search(label))
    ar = sum(1 for label, _, _ in rows
             if BIDI_RE.search(label) and AR_RE.search(FMT_RE.sub("", label)))
    print("labels containing a bidi control char:", tot, " of which Arabic:", ar)
    for label, src, name in rows:
        if BIDI_RE.search(label) and AR_RE.search(FMT_RE.sub("", label)):
            print("   %r  %s | %s" % (label[:50], src.replace("apk:", ""), name))
            break

    print()
    print("=== G. digit forms ===")
    ascii_digit = sum(1 for label, _, _ in rows if re.search(r"[0-9]", label))
    ar_digit = sum(1 for label, _, _ in rows
                   if re.search(r"[\u0660-\u0669\u06f0-\u06f9]", label))
    print("labels with ASCII digits   :", ascii_digit)
    print("labels with Arabic-Indic digits:", ar_digit)


if __name__ == "__main__":
    main()


