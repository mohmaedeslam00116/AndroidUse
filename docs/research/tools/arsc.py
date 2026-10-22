#!/usr/bin/env python3
"""
Parse an Android binary resource table (resources.arsc) and emit every
*string* resource value together with the configuration it belongs to.

Format references (primary sources, shipped in the AOSP tree):
  frameworks/base/libs/androidfw/include/androidfw/ResourceTypes.h
  frameworks/base/libs/androidfw/ResourceTypes.cpp

  ResChunk_header      { u16 type; u16 headerSize; u32 size; }
  ResStringPool_header { ResChunk_header header; u32 stringCount; u32 styleCount;
                         u32 flags; u32 stringsStart; u32 stylesStart; }
  ResTable_package     { ResChunk_header header; u32 id; char16_t name[128];
                         u32 typeStrings; u32 lastPublicType; u32 keyStrings;
                         u32 lastPublicKey; u32 typeIdOffset; }
  ResTable_typeSpec    { ResChunk_header header; u8 id; u8 res0; u16 res1;
                         u32 entryCount; u32 flags[entryCount]; }
  ResTable_type        { ResChunk_header header; u8 id; u8 res0; u16 res1;
                         u32 entryCount; u32 entriesStart; ResTable_config config; }
  ResTable_entry       { u16 size; u16 flags; u32 key; }
  Res_value            { u16 size; u8 res0; u8 dataType; u32 data; }

Layout facts confirmed empirically against shipped APKs and cross-checked
with `aapt2 dump resources`:
  * the table's first child chunk is the *global* value string pool; every
    Res_value::TYPE_STRING indexes into it;
  * a package's own string pool holds the resource *entry names*;
  * a package's type string pool holds the resource *type* names;
  * ResTable_config: size at +0, language[2] at +8, country[2] at +10.
"""
import struct
import sys
import zipfile

RES_STRING_POOL_TYPE = 0x0001
RES_TABLE_TYPE = 0x0002
RES_TABLE_PACKAGE_TYPE = 0x0200
RES_TABLE_TYPE_TYPE = 0x0201
RES_TABLE_TYPE_SPEC_TYPE = 0x0202
TYPE_STRING = 0x03
UTF8_FLAG = 1 << 8


class Pool(object):
    def __init__(self, data, start):
        self.data = data
        self.base = start
        (self.type, self.header_size, self.size) = struct.unpack_from("<HHI", data, start)
        (self.string_count, self.style_count, self.flags,
         self.strings_start, self.styles_start) = struct.unpack_from("<IIIII", data, start + 8)
        self.offsets = []
        off = start + self.header_size
        for _ in range(self.string_count):
            self.offsets.append(struct.unpack_from("<I", data, off)[0])
            off += 4
        self._cache = {}

    def utf8(self):
        return bool(self.flags & UTF8_FLAG)

    def get(self, index):
        if index in self._cache:
            return self._cache[index]
        if index < 0 or index >= len(self.offsets):
            return None
        pos = self.base + self.strings_start + self.offsets[index]
        data = self.data
        if self.utf8():
            b = data[pos]
            pos += 1
            if b & 0x80:
                b = ((b & 0x7F) << 8) | data[pos]
                pos += 1
            n = data[pos]
            pos += 1
            if n & 0x80:
                n = ((n & 0x7F) << 8) | data[pos]
                pos += 1
            s = data[pos:pos + n].decode("utf-8", "replace")
        else:
            n = struct.unpack_from("<H", data, pos)[0]
            pos += 2
            if n & 0x8000:
                n = ((n & 0x7FFF) << 16) | struct.unpack_from("<H", data, pos)[0]
                pos += 2
            s = data[pos:pos + n * 2].decode("utf-16-le", "replace")
        self._cache[index] = s
        return s


def parse_config_locale(data, cfg_off):
    """Locale tag of a ResTable_config: '' | 'ar' | 'ar-rSA' | ..."""
    lang = data[cfg_off + 8:cfg_off + 10]
    country = data[cfg_off + 10:cfg_off + 12]
    lang_s = lang.decode("ascii", "replace").strip("\x00")
    country_s = country.decode("ascii", "replace").strip("\x00")
    if not lang_s and not country_s:
        return ""
    tag = lang_s
    if country_s:
        tag += "-r" + country_s
    return tag


class Package(object):
    def __init__(self, data, pos):
        (self.type, self.header_size, self.size) = struct.unpack_from("<HHI", data, pos)
        self.pos = pos
        self.id = struct.unpack_from("<I", data, pos + 8)[0]
        self.name = data[pos + 12:pos + 12 + 256].decode("utf-16-le", "replace").split("\x00")[0]
        self.type_strings_off = struct.unpack_from("<I", data, pos + 268)[0]
        self.key_strings_off = struct.unpack_from("<I", data, pos + 276)[0]
        self.type_id_offset = 0
        if self.header_size >= 288:
            self.type_id_offset = struct.unpack_from("<I", data, pos + 284)[0]
        self.type_pool = Pool(data, pos + self.type_strings_off)
        self.key_pool = Pool(data, pos + self.key_strings_off)

    def type_name(self, type_id):
        # The type string pool is 1-based: type id 1 is pool index 0.
        # Confirmed against `aapt2 dump resources`, which prints
        # "type anim id=01" for a pool whose index 0 is "anim".
        return self.type_pool.get(type_id - 1)


def parse_arsc(data, only_type="string"):
    """Yield (pkg, type_name, entry_name, locale, value) for string resources."""
    (ctype, cheader_size, csize) = struct.unpack_from("<HHI", data, 0)
    if ctype != RES_TABLE_TYPE:
        raise ValueError("not a resource table")
    package_count = struct.unpack_from("<I", data, 8)[0]
    pos = 12
    global_pool = None
    (gtype, ghs, gsize) = struct.unpack_from("<HHI", data, pos)
    if gtype == RES_STRING_POOL_TYPE:
        global_pool = Pool(data, pos)
        pos += gsize

    packages = []
    for _ in range(package_count):
        (ptype, phs, psize) = struct.unpack_from("<HHI", data, pos)
        if ptype != RES_TABLE_PACKAGE_TYPE:
            break
        packages.append(Package(data, pos))
        pos += psize

    # fallback type-name map for shared-library type ids
    fallback = {}
    for p in packages:
        for i in range(p.type_pool.string_count):
            fallback.setdefault(i + 1, p.type_pool.get(i))

    out = []
    for pkg in packages:
        inner = pkg.pos + pkg.header_size
        end = pkg.pos + pkg.size
        while inner < end:
            (itype, iheader_size, isize) = struct.unpack_from("<HHI", data, inner)
            if isize == 0:
                break
            if itype == RES_TABLE_TYPE_TYPE:
                type_id = data[inner + 8]
                entry_count = struct.unpack_from("<I", data, inner + 12)[0]
                entries_start = struct.unpack_from("<I", data, inner + 16)[0]
                locale = parse_config_locale(data, inner + 20)
                if pkg.type_id_offset and type_id < pkg.type_id_offset:
                    tname = fallback.get(type_id)
                else:
                    tname = pkg.type_name(type_id)
                if only_type is not None and tname != only_type:
                    inner += isize
                    continue
                base = inner + entries_start
                offsets_base = inner + iheader_size
                for i in range(entry_count):
                    e = struct.unpack_from("<I", data, offsets_base + i * 4)[0]
                    if e == 0xFFFFFFFF:
                        continue
                    entry_abs = base + e
                    if entry_abs + 16 > len(data):
                        continue
                    (esize, eflags, key) = struct.unpack_from("<HHI", data, entry_abs)
                    if eflags & 0x0001:  # FLAG_COMPLEX
                        continue
                    (vsize, vres0, vtype, vdata) = struct.unpack_from("<HBBi", data, entry_abs + 8)
                    if vtype != TYPE_STRING:
                        continue
                    value = global_pool.get(vdata) if global_pool is not None else None
                    if value is None:
                        value = pkg.key_pool.get(vdata)
                    ename = pkg.key_pool.get(key)
                    out.append((pkg.name, tname, ename, locale, value))
            inner += isize
    return out


def arsc_from_apk(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        cand = [n for n in names if n.endswith("resources.arsc")]
        if not cand:
            return None
        cand.sort(key=lambda n: (n.count("/"), len(n)))
        return z.read(cand[0])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    apk = sys.argv[1]
    data = arsc_from_apk(apk)
    if data is None:
        print("no resources.arsc in", apk)
        return
    rows = parse_arsc(data)
    print("%s : %d string resources" % (apk, len(rows)))
    import collections
    c = collections.Counter(r[3] for r in rows)
    print("locales:", c.most_common(12))
    for r in rows[:10]:
        print("   ", r)


if __name__ == "__main__":
    main()
