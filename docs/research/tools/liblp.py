import struct, sys, os, json
sys.stdout.reconfigure(encoding="utf-8")

SUPER_OFF = 0x200000
path = r"D:\Android\Sdk\system-images\android-30\google_apis\x86_64\system.img"
f = open(path, "rb")

hdr_base = SUPER_OFF + 0x3000
f.seek(hdr_base)
h = f.read(128)
magic, major, minor, header_size = struct.unpack("<IHHI", h[0:12])
tables_size = struct.unpack("<I", h[44:48])[0]
parts = struct.unpack("<III", h[80:92])
extents = struct.unpack("<III", h[92:104])
groups = struct.unpack("<III", h[104:116])
bdevs = struct.unpack("<III", h[116:128])
print("header @0x%x magic=%08x v%d.%d header_size=%d tables_size=%d" % (hdr_base, magic, major, minor, header_size, tables_size))

tbl_base = hdr_base + header_size
f.seek(tbl_base)
blob = f.read(tables_size)
po, pn, ps = parts
eo, en, es = extents
ext_blob = blob[eo:eo + en * es]

out = []
for i in range(pn):
    e = blob[po + i * ps: po + (i + 1) * ps]
    name = e[0:36].split(b"\0")[0].decode("utf-8", "replace")
    attrs, first_extent, num_extents, group = struct.unpack("<IIII", e[36:52])
    print("part %-16s attrs=%d first_extent=%d num_extents=%d" % (name, attrs, first_extent, num_extents))
    for j in range(num_extents):
        ex = ext_blob[(first_extent + j) * es:(first_extent + j + 1) * es]
        num_sectors, target_type = struct.unpack("<QI", ex[0:12])
        target_data, = struct.unpack("<Q", ex[12:20])
        target_source, = struct.unpack("<I", ex[20:24])
        off = SUPER_OFF + target_data * 512
        print("    ext %d: sectors=%-10d (%.2f MB) type=%d data=%d src=%d file_off=0x%x" %
              (j, num_sectors, num_sectors * 512 / 1048576, target_type, target_data, target_source, off))
        out.append({"name": name, "offset": off, "size": num_sectors * 512, "type": target_type})

with open(r"D:\tmp\opencode\partitions.json", "w") as jf:
    json.dump(out, jf, indent=1)
print("wrote partitions.json")
