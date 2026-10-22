#!/usr/bin/env python3
"""
Build the AndroidUse UI-label corpus from shipped APKs + Android platform
resource tables.

Output: TSV, one row per (label, source, resource name):

    <label>\\t<source_id>\\t<resource_name>

source_id is one of:
    apk:<partition>/<path inside the system image>/<App>.apk
    sdk:<platform>/data/res/values[-ar]/strings.xml

Only two locale buckets are kept: the default bucket (English source
strings) and every Arabic configuration.
"""
import io
import os
import sys
import xml.etree.ElementTree as ET
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from arsc import parse_arsc, arsc_from_apk

SDK = os.environ.get("ANDROID_SDK", r"D:\Android\Sdk")
APK_ROOT = os.environ.get("ANDROIDUSE_APK_ROOT", r"D:\tmp\opencode\apks")
PLATFORMS = ["android-29", "android-30", "android-31", "android-33", "android-34",
             "android-35", "android-36"]
BUCKETS = ["values", "values-ar"]


def is_arabic(locale):
    return locale == "ar" or locale.startswith("ar-")


def from_apks():
    rows = []
    stats = collections.Counter()
    apks = []
    for dirpath, dirnames, filenames in os.walk(APK_ROOT):
        for fn in sorted(filenames):
            if fn.lower().endswith(".apk"):
                apks.append(os.path.join(dirpath, fn))
    apks.sort()
    for apk in apks:
        rel = os.path.relpath(apk, APK_ROOT).replace("\\", "/")
        source_id = "apk:" + rel
        try:
            data = arsc_from_apk(apk)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("SKIP %s (%s)\n" % (rel, exc))
            continue
        if data is None:
            sys.stderr.write("SKIP %s (no resources.arsc)\n" % rel)
            continue
        try:
            res = parse_arsc(data, only_type="string")
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("SKIP %s (parse: %s)\n" % (rel, exc))
            continue
        n = 0
        for pkg, tname, ename, locale, value in res:
            if value is None:
                continue
            if locale != "" and not is_arabic(locale):
                continue
            rows.append((value, source_id, ename))
            n += 1
        stats[source_id] = n
        sys.stderr.write("%-95s %7d\n" % (source_id, n))
    return rows, stats


def from_platform():
    rows = []
    for platform in PLATFORMS:
        for bucket in BUCKETS:
            p = os.path.join(SDK, "platforms", platform, "data", "res", bucket, "strings.xml")
            if not os.path.isfile(p):
                continue
            source_id = "sdk:%s/data/res/%s/strings.xml" % (platform, bucket)
            try:
                tree = ET.parse(p)
            except ET.ParseError as exc:
                sys.stderr.write("SKIP %s (%s)\n" %p, exc)
                continue
            for el in tree.getroot():
                if el.tag != "string":
                    continue
                name = el.get("name")
                if name is None:
                    continue
                text = "".join(el.itertext())
                rows.append((text, source_id, name))
    return rows


def main():
    out_path = sys.argv[1]
    rows, stats = from_apks()
    rows += from_platform()
    clean = []
    for label, source, name in rows:
        t = label.replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()
        if not t:
            continue
        clean.append((t, source, name))
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for label, source, name in clean:
            f.write("%s\t%s\t%s\n" % (label, source, name))
    labels = set(r[0] for r in clean)
    print("rows      :", len(clean))
    print("distinct  :", len(labels))
    print("apk count :", len(stats))


if __name__ == "__main__":
    main()
