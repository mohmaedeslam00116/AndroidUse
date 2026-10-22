#!/usr/bin/env python3
"""For each Arabic list entry, count the real spelling variants present."""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
CORPUS = sys.argv[1]
BIDI_RE = re.compile("[\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069]")


def main():
    rows = []
    with io.open(CORPUS, encoding="utf-8") as f:
        for line in f:
            if not line or line.startswith("##"):
                continue
            p = line.rstrip("\n").split("\t")
            rows.append((p[0], p[1] if len(p) > 1 else "", p[2] if len(p) > 2 else ""))
    labels = sorted(set(r[0] for r in rows))
    low = {l: BIDI_RE.sub("", l).lower() for l in labels}

    groups = {
        "send / إرسال": [
            ("إرسال", "masculine noun: 'the sending' (canonical)"),
            ("إرسالها", "feminine object suffix"),
            ("إرسال رسالة", "'send a message'"),
            ("إرسال الرسالة", "'the message'"),
            ("أرسل", "imperfect: 'he sent' / imperative 'send!'"),
            ("أرسلها", "imperfect + object suffix"),
            ("ارسل", "no hamza"),
            ("إرسل", "wrong hamza (the list's spelling)"),
            ("إرسال", "with fatha/tashkeel"),
            ("الارسال", "with definite article"),
        ],
        "share / مشاركة": [
            ("مشاركة", "teh-marbuta"),
            ("مشاركه", "heh (Egyptian)"),
            ("المشاركة", "with definite article"),
            ("مشاركة", ""),
        ],
        "confirm / تأكيد": [
            ("تأكيد", "canonical"),
            ("تاكيد", "no hamza"),
            ("التأكيد", "with definite article"),
            ("تأكيدًا", "with tanween"),
        ],
        "agree / موافق": [
            ("موافق", "bare"),
            ("موافقة", "teh-marbuta"),
            ("موافقتك", "2nd person suffix"),
            ("أوافق", "alef-hamza-above"),
            ("الموافقة", "article + teh-marbuta"),
        ],
        "yes / نعم": [
            ("نعم", "canonical"),
            ("نعمًا", "with tanween"),
            ("نعم،", "with comma"),
        ],
        "continue / متابعة": [
            ("متابعة", "canonical"),
            ("المتابعة", "article"),
            ("متابعة", "shadda"),
        ],
        "done / تم": [
            ("تم", "bare"),
            ("تمّ", "with shadda"),
            ("تم.", "with period"),
            ("تم؟", "with question mark"),
        ],
        "complete / إتمام": [
            ("إتمام", "canonical"),
            ("أتمام", "wrong hamza"),
            ("إتمامًا", "with tanween"),
        ],
        "pay / دفع": [
            ("دفع", "noun"),
            ("ادفع", "imperative 'pay!'"),
            ("الدفع", "with definite article"),
            ("دفع", "with shadda"),
            ("سداد", "'settlement'"),
            ("دفع electronic", ""),
        ],
        "buy / شراء": [
            ("شراء", "canonical noun"),
            ("الشراء", "with definite article"),
            ("اشتر", "past 'he bought'"),
            ("اشتري", "imperative 'buy!'"),
            ("اشترِ", "with kasra"),
            ("شراء", "transliteration with alif"),
        ],
    }

    for group, variants in groups.items():
        print("=== %s ===" % group)
        for form, note in variants:
            hits = [l for l in labels if form in low[l]]
            ww = [l for l in labels if re.search(
                r"(?<![؀-ۿ])(?:%s)(?![؀-ۿ])" % re.escape(form), low[l])]
            print("  %-16s %-40s labels=%-6d whole-word=%d" % (form, note, len(hits), len(ww)))
        print()


if __name__ == "__main__":
    main()


