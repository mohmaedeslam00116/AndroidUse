import struct, sys
sys.stdout.reconfigure(encoding="utf-8")

p = r"D:\Android\Sdk\system-images\android-30\google_apis\x86_64\system.img"
f = open(p, "rb")

f.seek(0x200)
hdr = f.read(92)
sig = hdr[0:8]
assert sig == b"EFI PART", sig
part_lba, num_entries, entry_size = struct.unpack("<QII", hdr[72:88])
print("GPT: entry_lba=%d num_entries=%d entry_size=%d" % (part_lba, num_entries, entry_size))

f.seek(part_lba * 512)
data = f.read(num_entries * entry_size)
parts = []
for i in range(num_entries):
    e = data[i * entry_size:(i + 1) * entry_size]
    if e[:16] == b"\0" * 16:
        continue
    first, last = struct.unpack("<QQ", e[32:48])
    name = e[56:128].decode("utf-16-le", "replace").split("\0")[0]
    parts.append((name, first, last, (last - first + 1) * 512))
    print("  %-14s first_lba=%-10d last_lba=%-10d size=%.2f MB  offset=0x%x" %
          (name, first, last, (last - first + 1) * 512 / 1048576, first * 512))
