#!/usr/bin/env python3
"""
Final analysis over the AndroidUse label corpus.

Produces every number quoted in docs/research/label-corpus.md.
"""
import io
import json
import os
import re
import sys
import unicodedata
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from analyze import read_kotlin_lists, whole_word, is_short

CORPUS = sys.argv[1]
OUT = sys.argv[2]
KOTLIN = os.environ.get("ANDROIDUSE_CAPABILITY_RESOLVER",
                        r"D:\ai\kiloprojct\protocol\src\main\kotlin\ai\androiduse\protocol\CapabilityResolver.kt")

BIDI_CTRL = "‎‏‪‫‬‭‮⁦⁧⁨⁩"
BIDI_RE = re.compile("[" + BIDI_CTRL + "]")
AR_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
LAT_RE = re.compile(r"[A-Za-z]")

# ---- curated "same concept" variant sets, used to measure missed positives ----
VARIANTS = {
    "send": [r"\bsend\b", r"\bsends\b", r"\bsending\b", r"\bsent\b", r"\bresend\b",
             r"\bsend now\b", r"\bsend message\b", r"\bsend messages\b", r"\bsend button\b",
             r"\bأرسل\b", r"\bإرسال\b", r"\bأرسلها\b", r"\bإرسالها\b", r"\bإرسال رسالة\b"],
    "submit": [r"\bsubmit\b", r"\bsubmits\b", r"\bsubmitting\b", r"\bsubmitted\b"],
    "post": [r"\bpost\b", r"\bposts\b", r"\bposting\b", r"\bposted\b", r"\bpost now\b"],
    "publish": [r"\bpublish\b", r"\bpublishes\b", r"\bpublishing\b", r"\bpublished\b"],
    "share": [r"\bshare\b", r"\bshares\b", r"\bsharing\b", r"\bshared\b", r"\bshare now\b"],
    "send message": [r"\bsend message\b", r"\bsend messages\b", r"\bsend now\b", r"\bsend\b"],
    "place order": [r"\bplace order\b", r"\border now\b", r"\bbuy now\b"],
    "continue": [r"\bcontinue\b", r"\bcontinues\b", r"\bcontinuing\b", r"\bcontinued\b"],
    "done": [r"\bdone\b", r"\bfinish\b", r"\bfinished\b", r"\bcomplete\b", r"\bcompleted\b",
             r"\bتم\b", r"\bتمّت\b", r"\bإتمام\b"],
    "ok": [r"\bok\b", r"\bokay\b", r"\bok\b", r"\bحسنًا\b", r"\bحسنا\b"],
    "yes": [r"\byes\b", r"\byeah\b", r"\byep\b", r"\bنعم\b"],
    "agree": [r"\bagree\b", r"\bagrees\b", r"\bagreed\b", r"\baccept\b", r"\bموافق\b",
              r"\bموافقة\b", r"\bموافقتك\b", r"\bأوافق\b"],
    "confirm": [r"\bconfirm\b", r"\bconfirms\b", r"\bconfirming\b", r"\bconfirmed\b",
                r"\bتأكيد\b", r"\bتأكيد\w*"],
    "إرسال": [r"\bإرسال\b", r"\bإرسال\w*", r"\bأرسل\b", r"\bأرسل\w*", r"\bإرسل\w*",
               r"\bارسال\w*"],
    "أرسل": [r"\bأرسل\b", r"\bأرسل\w*", r"\bإرسال\b", r"\bإرسال\w*"],
    "إرسل": [r"\bإرسل\b", r"\bإرسل\w*", r"\bإرسال\b"],
    "مشاركة": [r"\bمشاركة\b", r"\bمشاركه\b", r"\bمشاركة\w*", r"\bمشارك\w*"],
    "تأكيد": [r"\bتأكيد\b", r"\bتأكيد\w*", r"\bأكّد\b", r"\bإтвер\w*"],
    "موافق": [r"\bموافق\b", r"\bموافقة\b", r"\bموافق\w*", r"\bأوافق\b"],
    "نعم": [r"\bنعم\b", r"\bنعم،\w*"],
    "متابعة": [r"\bمتابعة\b", r"\bمتابعة\w*", r"\bمتابعة\w*"],
    "تم": [r"\bتم\b", r"\bتمّت\b", r"\bتم\b", r"\bإتمام\b", r"\bتمّ\b"],
    "إتمام": [r"\bإتمام\b", r"\bإتمام\w*", r"\bتم\b"],
    "pay": [r"\bpay\b", r"\bpays\b", r"\bpaid\b", r"\bpaying\b", r"\bpay now\b"],
    "payment": [r"\bpayment\b", r"\bpayments\b", r"\bpay\b", r"\bpaid\b"],
    "buy": [r"\bbuy\b", r"\bbuys\b", r"\bbought\b", r"\bbuy now\b"],
    "purchase": [r"\bpurchase\b", r"\bpurchases\b", r"\bpurchased\b", r"\bpurchasing\b"],
    "checkout": [r"\bcheckout\b", r"\bcheck out\b"],
    "subscribe": [r"\bsubscribe\b", r"\bsubscribes\b", r"\bsubscribed\b", r"\bsubscribing\b",
                  r"\bsubscription\b", r"\bsubscriptions\b"],
    "order now": [r"\border now\b", r"\bbuy now\b", r"\bplace order\b"],
    "confirm payment": [r"\bconfirm payment\b", r"\bconfirm payments\b", r"\bpay now\b",
                        r"\bcomplete payment\b"],
    "دفع": [r"دفع", r"ادفع", r"الدفع", r"سداد", r"دفع\w*"],
    "ادفع": [r"ادفع", r"دفع\w*", r"الدفع", r"ادفع\w*"],
    "shop": [r"شراء", r"الشراء", r"شراء\w*", r"الشراء\w*"],
    "اشتر": [r"اشتر\w*", r"الشراء", r"shop\w*", r"شراء\w*"],
    "اشتري": [r"اشتري", r"اشتر\w*", r"shop\w*"],
    "الشراء": [r"الشراء", r"الشراء\w*", r"shop\w*"],
}

FORMS = {
    "alef-hamza-above  أ  U+0623": "أ",
    "alef-hamza-below  إ  U+0625": "إ",
    "alef-madda        آ  U+0622": "آ",
    "alef-wasla        ٱ  U+0671": "ٱ",
    "bare alef         ا  U+0627": "ا",
    "yeh               ي  U+064A": "ي",
    "alef-maksura      ى  U+0649": "ى",
    "farsi yeh         ی  U+06CC": "ی",
    "teh-marbuta       ة  U+0629": "ة",
    "heh               ه  U+0647": "ه",
    "bare hamza        ء  U+0621": "ء",
    "waw-with-hamza    ؤ  U+ؤ": "ؤ",
    "yeh-with-hamza    ئ  U+ئ": "ئ",
    "tatweel           ـ  U+0640": "ـ",
    "fatha             َ  U+064E": "َ",
    "kasra             ِ  U+0650": "ِ",
    "damma             ُ  U+064F": "ُ",
    "sukun             ْ  U+0652": "ْ",
    "shadda            ّ  U+0651": "ّ",
    "arabic-indic 0    ٠  U+0660": "٠",
    "ext. arabic 0     ۰  U+06F0": "۰",
}


def strip_bidi(s):
    return BIDI_RE.sub("", s)


def norm(s):
    """strip bidi marks + surrounding punctuation/whitespace, casefold"""
    s = strip_bidi(s).strip()
    s = s.strip(" \t\n\r.,:;!؟?!\"'()[]{}<>«»-–—…*_")
    return s.strip().lower()


def main():
    rows = []
    prov = {}
    with io.open(CORPUS, encoding="utf-8") as f:
        for line in f:
            if not line or line.startswith("##"):
                continue
            parts = line.rstrip("\n").split("\t")
            label = parts[0]
            src = parts[1] if len(parts) > 1 else ""
            name = parts[2] if len(parts) > 2 else ""
            rows.append((label, src, name))
            prov.setdefault(label, []).append((src, name))

    labels = list(prov.keys())
    low = {l: l.lower() for l in labels}
    lists = read_kotlin_lists(KOTLIN)

    out = {
        "corpus_rows": len(rows),
        "corpus_distinct_labels": len(labels),
        "corpus_short_labels": len([l for l in labels if is_short(l)]),
        "corpus_arabic_labels": len([l for l in labels if AR_RE.search(l)]),
        "corpus_arabic_only_labels": len([l for l in labels
                                          if AR_RE.search(l) and not LAT_RE.search(l)]),
        "corpus_mixed_script_labels": len([l for l in labels
                                           if AR_RE.search(l) and LAT_RE.search(l)]),
        "corpus_bidi_labels": len([l for l in labels if BIDI_RE.search(l)]),
        "corpus_arabic_bidi_labels": len([l for l in labels
                                          if AR_RE.search(l) and BIDI_RE.search(l)]),
        "lists": {},
        "orthography": {},
        "nonword": {},
    }

    # ---- orthography census -------------------------------------------------
    arabic = [l for l in labels if AR_RE.search(l)]
    for name, ch in FORMS.items():
        out["orthography"][name] = {
            "all": sum(1 for l in labels if ch in l),
            "arabic": sum(1 for l in arabic if ch in l),
        }

    # ---- non-word label inventory ------------------------------------------
    glyph_like = [l for l in labels if not LAT_RE.search(l) and not AR_RE.search(l)]
    out["nonword"]["glyph_only"] = {"count": len(glyph_like), "examples": glyph_like[:40]}
    id_like = [l for l in labels if re.match(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$", l)]
    out["nonword"]["snake_case_ids"] = {"count": len(id_like), "examples": id_like[:40]}
    mixed = [l for l in labels if AR_RE.search(l) and LAT_RE.search(l)]
    out["nonword"]["mixed_script"] = {"count": len(mixed), "examples": mixed[:40]}
    empty_like = [l for l in labels if not l.strip()]
    out["nonword"]["blank"] = {"count": len(empty_like)}

    # ---- per-entry tables ---------------------------------------------------
    for listname, entries in lists.items():
        per = []
        short = [l for l in labels if is_short(l)]
        for entry in entries:
            el = entry.lower()
            sub = [l for l in labels if entry in low[l]]
            ww = [l for l in labels if whole_word(low[l], entry)]
            ex = [l for l in labels if norm(low[l]) == el]
            ssub = [l for l in short if entry in low[l]]
            sww = [l for l in short if whole_word(low[l], entry)]
            sex = [l for l in short if norm(low[l]) == el]
            wwset = set(ww)
            inner = [l for l in sub if l not in wwset]
            # precision model: a matched label is a plausible positive iff the
            # entry is a whole word in it AND the label looks like a tap-target
            # label (short).  ex[] labels always qualify.
            anchor = [l for l in ww if is_short(l)]
            plausible_sub = [l for l in sub if l in wwset and is_short(l)]
            variants = VARIANTS.get(entry)
            concept = [l for l in labels if re.search("|".join(variants), l, re.IGNORECASE)] \
                if variants else []
            missed = [l for l in concept if not whole_word(low[l], entry)]
            per.append({
                "entry": entry,
                "substring": len(sub),
                "whole_word": len(ww),
                "exact": len(ex),
                "inner_only": len(inner),
                "plausible_substring": len(plausible_sub),
                "fp_substring": len(sub) - len(plausible_sub),
                "fp_whole_word": len(ww) - len(anchor),
                "precision_substring": (len(plausible_sub) / len(sub)) if sub else None,
                "precision_whole_word": (len(anchor) / len(ww)) if ww else None,
                "concept_total": len(concept),
                "concept_missed": len(missed),
                "short_substring": len(ssub),
                "short_whole_word": len(sww),
                "short_exact": len(sex),
                "sub_examples": sub[:10],
                "inner_examples": inner[:10],
                "ww_examples": ww[:10],
                "ex_examples": ex[:10],
                "missed_examples": sorted(missed, key=len)[:10],
            })
        out["lists"][listname] = per

    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ---- console summary ----------------------------------------------------
    print("rows=%d distinct=%d short=%d arabic=%d arabic-only=%d mixed=%d bidi=%d ar-bidi=%d" % (
        out["corpus_rows"], out["corpus_distinct_labels"], out["corpus_short_labels"],
        out["corpus_arabic_labels"], out["corpus_arabic_only_labels"],
        out["corpus_mixed_script_labels"], out["corpus_bidi_labels"],
        out["corpus_arabic_bidi_labels"],))
    for listname, per in out["lists"].items():
        print("---", listname, "---")
        print("%-15s %5s %5s %5s %6s %6s %6s %8s %8s %8s" %
              ("entry", "sub", "word", "exact", "inner", "FPsub", "FPword",
               "P(sub)", "concept", "missed"))
        for e in per:
            print("%-15s %5d %5d %5d %6d %6d %6d %8s %8d %8d" % (
                e["entry"], e["substring"], e["whole_word"], e["exact"],
                e["inner_only"], e["fp_substring"], e["fp_whole_word"],
                ("%.3f" % e["precision_substring"]) if e["precision_substring"] is not None else "-",
                e["concept_total"], e["concept_missed"]))
    print("--- non-word labels ---")
    for k, v in out["nonword"].items():
        print(" ", k, v["count"], v.get("examples", [])[:6])


if __name__ == "__main__":
    main()


