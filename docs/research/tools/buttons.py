#!/usr/bin/env python3
"""
Inventory the *button-shaped* labels in the corpus for the send and payment
concepts, and report which of them the current CapabilityResolver lists
actually catch.
"""
import io
import os
import re
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from analyze import read_kotlin_lists, whole_word

CORPUS = sys.argv[1]
KOTLIN = os.environ.get("ANDROIDUSE_CAPABILITY_RESOLVER",
                        r"D:\ai\kiloprojct\protocol\src\main\kotlin\ai\androiduse\protocol\CapabilityResolver.kt")
BIDI_RE = re.compile("[\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069]")


def norm(s):
    s = BIDI_RE.sub("", s).strip()
    s = s.strip(" \t\n\r.,:;!؟?!\"'()[]{}<>«»-–—…*_")
    return s.strip().lower()


# hand-curated concept membership: the label, stripped, IS the concept action
SEND_FORMS = {
    "send", "sends", "send message", "send messages", "send now", "send button",
    "submit", "post", "publish", "share", "share now", "share via",
    "place order", "reply", "forward", "resend", "deliver",
    "إرسال", "أرسل", "إرسل", "إرسال الرسالة", "إرسال رسالة", "إرسالها", "أرسلها",
    "مشاركة", "تأكيد", "موافق", "نعم", "متابعة", "تم", "تمّت", "إتمام",
}
PAY_FORMS = {
    "pay", "pay now", "payment", "payments", "buy", "buy now", "purchase",
    "checkout", "check out", "subscribe", "order now", "confirm payment",
    "دفع", "ادفع", "دفع الآن", "اشتر", "اشتري", "شراء", "الشراء", "شراء now",
    "اشتراك", "إتمام الدفع", "تأكيد الدفع",
}


def main():
    lists = read_kotlin_lists(KOTLIN)
    send_list = lists["sendWords"]
    pay_list = lists["paymentWords"]

    rows = []
    with io.open(CORPUS, encoding="utf-8") as f:
        for line in f:
            if not line or line.startswith("##"):
                continue
            parts = line.rstrip("\n").split("\t")
            label = parts[0]
            src = parts[1] if len(parts) > 1 else ""
            name = parts[2] if len(parts) > 2 else ""
            rows.append((label, src, name))

    byform = collections.defaultdict(list)
    for label, src, name in rows:
        n = norm(label)
        if n in SEND_FORMS or n in PAY_FORMS:
            byform[n].append((label, src, name))

    def caught(label, wordlist):
        low = label.lower()
        hits = [w for w in wordlist if w in low]
        whole = [w for w in wordlist if whole_word(low, w)]
        return hits, whole

    print("=== SEND concept: real button-shaped labels in the corpus ===")
    for form in sorted(byform):
        if form not in SEND_FORMS:
            continue
        label, src, name = byform[form][0]
        hits, whole = caught(label, send_list)
        print("  %-22s sub=%-28s word=%-22s  %s | %s" % (
            repr(form),
            ",".join(hits) if hits else "-",
            ",".join(whole) if whole else "-",
            src.replace("apk:", ""), name))
    print()
    print("=== PAYMENT concept: real button-shaped labels in the corpus ===")
    for form in sorted(byform):
        if form not in PAY_FORMS:
            continue
        label, src, name = byform[form][0]
        hits, whole = caught(label, pay_list)
        print("  %-22s sub=%-28s word=%-22s  %s | %s" % (
            repr(form),
            ",".join(hits) if hits else "-",
            ",".join(whole) if whole else "-",
            src.replace("apk:", ""), name))

    print()
    print("=== counts of each button-shaped form ===")
    for form in sorted(byform):
        if form in SEND_FORMS or form in PAY_FORMS:
            print("  %-24s n=%d" % (repr(form), len(byform[form])))


if __name__ == "__main__":
    main()


