#!/usr/bin/env python3
"""
Measure what the CapabilityResolver word lists do to the real label corpus.

Matching strategies modelled:
  substring  - exactly what CapabilityResolver does today:
               label.lowercase().contains(entry)   (entry used verbatim)
  word       - the entry occurs as a whole token in label.lowercase()
  exact      - label.trim().lowercase() == entry.lower()

Whole-token definition: the characters immediately before and after the match
must not be word characters, where word characters are ASCII letters, digits,
underscore, or any character in the Arabic blocks (U+0600-U+06FF, U+0750-U+077F,
U+08A0-U+08FF, U+FB50-U+FDFF, U+FE70-U+FEFF).  This is the Unicode-aware
behaviour of Java's \\b with UNICODE_CHARACTER_CLASS, not Java's default
ASCII-only \\b.
"""
import io
import os
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

KOTLIN = os.environ.get("ANDROIDUSE_CAPABILITY_RESOLVER",
                        r"D:\ai\kiloprojct\protocol\src\main\kotlin\ai\androiduse\protocol\CapabilityResolver.kt")

ARABIC_BLOCKS = ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),
                 (0xFB50, 0xFDFF), (0xFE70, 0xFEFF))

# Near-variants of each entry that express the same intent but are not the
# entry itself.  Used to measure which true positives an entry MISSES.
VARIANTS = {
    "send": [r"\bsends?\b", r"\bsending\b", r"\bsent\b", r"\bsender\b", r"\bresend\b",
             r"\bsend now\b", r"\bsend message\b", r"\bsend messages\b"],
    "submit": [r"\bsubmits?\b", r"\bsubmitting\b", r"\bsubmitted\b", r"\bsubmission\b"],
    "post": [r"\bposts?\b", r"\bposting\b", r"\bposted\b", r"\bpost now\b"],
    "publish": [r"\bpublish\b", r"\bpublishes\b", r"\bpublishing\b", r"\bpublished\b"],
    "share": [r"\bshares?\b", r"\bsharing\b", r"\bshared\b", r"\bshare via\b"],
    "send message": [r"\bsend\b", r"\bsend now\b", r"\bsend messages?\b", r"\bsending\b"],
    "place order": [r"\border now\b", r"\bplace order\b", r"\border\b", r"\bbuy now\b"],
    "continue": [r"\bcontinues?\b", r"\bcontinuing\b", r"\bcontinued\b", r"\bnext\b"],
    "done": [r"\bdone\b", r"\bfinish\b", r"\bfinished\b", r"\bcomplete\b", r"\bcompleted\b"],
    "ok": [r"\bok\b", r"\bokay\b", r"\ball right\b", r"\bgot it\b", r"\bconfirm\b"],
    "yes": [r"\byes\b", r"\byeah\b", r"\byep\b"],
    "agree": [r"\bagrees?\b", r"\bagreeing\b", r"\bagreed\b", r"\baccept\b", r"\baccept terms\b"],
    "confirm": [r"\bconfirms?\b", r"\bconfirming\b", r"\bconfirmed\b", r"\bconfirm\b"],
    "pay": [r"\bpay\b", r"\bpays\b", r"\bpaid\b", r"\bpaying\b", r"\bpayment\b"],
    "payment": [r"\bpayments?\b", r"\bpay\b", r"\bpaid\b", r"\bpaying\b"],
    "buy": [r"\bbuys?\b", r"\bbought\b", r"\bbuy now\b", r"\bpurchase\b"],
    "purchase": [r"\bpurchases?\b", r"\bpurchased\b", r"\bpurchasing\b", r"\bbuy\b"],
    "checkout": [r"\bcheckout\b", r"\bcheck out\b", r"\bbuy now\b", r"\bpurchase\b"],
    "subscribe": [r"\bsubscribes?\b", r"\bsubscribed\b", r"\bsubscribing\b",
                  r"\bsubscription\b", r"\bsubscriptions\b"],
    "order now": [r"\border now\b", r"\bbuy now\b", r"\bplace order\b"],
    "confirm payment": [r"\bconfirm payment\b", r"\bpay now\b", r"\bcomplete payment\b"],
    "دفع": [r"دفع", r"ادفع", r"الدفع", r"سداد", r"ادفع الآن", r"إتمام الدفع"],
    "ادفع": [r"ادفع", r"دفع", r"ادفع الآن", r"الدفع"],
    "buy": [r"\bbuy\b", r"\bbuys\b", r"\bbought\b", r"\bbuy now\b"],
    "اشتر": [r"اشتر", r"اشتري", r"الشراء", r"شراء", r"شراء now"],
    "اشتري": [r"اشتري", r"اشتر", r"الشراء", r"شراء"],
}

# Arabic send/confirm family
AR_SEND = [r"إرسال", r"إرسال\w*", r"أرسل\w*", r"ارسل\w*", r"إرسال\w*", r"مشاركة", r"مشاركه",
           r"الإرسال", r"إرسال\w*"]
AR_PAY = [r"دفع", r"ادفع", r"الدفع", r"اشتر\w*", r"الشراء", r"شراء", r"شراء\w*",
          r"اشتراك", r"الشراء"]


def is_word_char(ch):
    if ch is None:
        return False
    if ch == "_" or ch.isalnum():
        return True
    o = ord(ch)
    for lo, hi in ARABIC_BLOCKS:
        if lo <= o <= hi:
            return True
    return False


def read_kotlin_lists(path):
    text = io.open(path, encoding="utf-8").read()
    lists = {}
    for name in ("sendWords", "paymentWords"):
        m = re.search(r"val\s+" + name + r"\s*:\s*List<String>\s*=\s*listOf\((.*?)\n\s*\)",
                      text, re.S)
        if not m:
            raise SystemExit("could not find " + name)
        body = re.sub(r"//[^\n]*", "", m.group(1))
        lists[name] = re.findall(r'"([^"]*)"', body)
    return lists


def read_corpus(path):
    rows = []
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("##"):
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                rows.append((parts[0], parts[1], "\t".join(parts[2:])))
            elif len(parts) == 2:
                rows.append((parts[0], parts[1], ""))
            else:
                rows.append((parts[0], "", ""))
    return rows


def whole_word(label, entry):
    e = entry.lower()
    if not e:
        return False
    start = 0
    while True:
        i = label.find(e, start)
        if i < 0:
            return False
        j = i + len(e)
        before = label[i - 1] if i > 0 else None
        after = label[j] if j < len(label) else None
        if not is_word_char(before) and not is_word_char(after):
            return True
        start = i + 1


def is_short(label):
    """A 'button-label-like' label: at most 4 words and 40 characters."""
    return len(label) <= 40 and len(label.split()) <= 4


def main():
    corpus_path = sys.argv[1]
    out_path = sys.argv[2]
    rows = read_corpus(corpus_path)
    lists = read_kotlin_lists(KOTLIN)

    prov = {}
    for label, src, name in rows:
        prov.setdefault(label, []).append((src, name))
    labels = list(prov.keys())
    lowered = {lab: lab.lower() for lab in labels}

    subsets = {
        "all": labels,
        "short": [l for l in labels if is_short(l)],
    }

    result = {
        "corpus_rows": len(rows),
        "corpus_distinct_labels": len(labels),
        "subset_sizes": {k: len(v) for k, v in subsets.items()},
        "lists": {},
    }

    for listname, entries in lists.items():
        per_entry = []
        for entry in entries:
            el = entry.lower()
            rec = {"entry": entry, "lower": el}
            for sname, slabels in subsets.items():
                low = {l: lowered[l] for l in slabels}
                sub = [l for l in slabels if entry in low[l]]
                sub_ci = [l for l in slabels if el in low[l]]
                ww = [l for l in slabels if whole_word(low[l], entry)]
                ex = [l for l in slabels if low[l].strip() == el]
                wwset = set(ww)
                inner = [l for l in sub if l not in wwset]
                rec[sname] = {
                    "substring": len(sub),
                    "substring_ci": len(sub_ci),
                    "whole_word": len(ww),
                    "exact": len(ex),
                    "inner_only": len(inner),
                    "sub_examples": sub[:15],
                    "inner_examples": inner[:15],
                    "ww_examples": ww[:15],
                    "exact_examples": ex[:15],
                    "dead_as_implemented": len(sub) == 0 and len(sub_ci) > 0,
                }
            # true positives this entry misses: variants of the same concept
            variants = VARIANTS.get(entry)
            if variants:
                pat = re.compile("|".join(variants), re.IGNORECASE)
                concept = [l for l in labels if pat.search(l)]
                missed = [l for l in concept if not whole_word(lowered[l], entry)]
                rec["variants_total"] = len(concept)
                rec["variants_missed"] = len(missed)
                rec["variant_miss_examples"] = sorted(missed)[:15]
            else:
                rec["variants_total"] = None
                rec["variants_missed"] = None
                rec["variant_miss_examples"] = []
            per_entry.append(rec)
        result["lists"][listname] = per_entry

    with io.open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print("corpus rows      :", result["corpus_rows"])
    print("distinct labels  :", result["corpus_distinct_labels"])
    print("short labels     :", result["subset_sizes"]["short"])
    for listname in lists:
        print("---", listname, "---")
        print("%-16s %7s %7s %7s %7s %7s %7s  %s" %
              ("entry", "sub", "subci", "word", "exact", "inner", "missed", "flags"))
        for e in result["lists"][listname]:
            a = e["all"]
            flags = []
            if a["dead_as_implemented"]:
                flags.append("DEAD-AS-IMPLEMENTED")
            if e["variants_missed"]:
                flags.append("misses-variants")
            print("%-16s %7d %7d %7d %7d %7d %7s  %s" %
                  (e["entry"], a["substring"], a["substring_ci"], a["whole_word"],
                   a["exact"], a["inner_only"],
                   ("%d/%d" % (e["variants_missed"], e["variants_total"]))
                   if e["variants_total"] is not None else "-",
                   " ".join(flags)))


if __name__ == "__main__":
    main()


