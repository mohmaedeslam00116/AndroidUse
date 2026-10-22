import json, os, sys, struct

src = r"D:\Android\Sdk\system-images\android-30\google_apis\x86_64\system.img"
outdir = r"D:\tmp\opencode\parts"
os.makedirs(outdir, exist_ok=True)
parts = json.load(open(r"D:\tmp\opencode\partitions.json"))
f = open(src, "rb")
for p in parts:
    out = os.path.join(outdir, p["name"] + ".img")
    if os.path.exists(out) and os.path.getsize(out) == p["size"]:
        print("skip", out)
        continue
    f.seek(p["offset"])
    remaining = p["size"]
    with open(out, "wb") as o:
        while remaining > 0:
            chunk = f.read(min(1 << 22, remaining))
            if not chunk:
                break
            o.write(chunk)
            remaining -= len(chunk)
    print("wrote", out, os.path.getsize(out))
    # report head magic
    with open(out, "rb") as o:
        head = o.read(0x440)
    magic_sparse = struct.unpack("<I", head[0:4])[0] if len(head) >= 4 else 0
    magic_ext4 = struct.unpack("<H", head[0x438:0x43A])[0] if len(head) >= 0x43A else 0
    print("   head=%s sparse_magic=%08x ext4_magic_at_438=%04x" % (head[:16].hex(), magic_sparse, magic_ext4))
