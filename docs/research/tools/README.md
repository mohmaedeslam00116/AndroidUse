# Corpus tooling

The scripts that produced `docs/research/label-corpus.txt` and the numbers in
`docs/research/label-corpus.md`.  They are committed so the corpus can be
rebuilt and challenged rather than taken on trust.

Everything runs on Windows with Python 3.12 and, for the ext4 step, WSL2
(Ubuntu) with `e2fsprogs` installed.  No emulator is used and no AVD is
created - the system image is only read.

## 1. Split the system image

`system.img` (API 30, `google_apis`, x86_64) is a GPT disk image holding a
dynamic-partition `super` partition.

```sh
python gpt.py                      # lists the GPT partitions
python liblp.py                    # lists the logical partitions inside `super`
python extract_parts.py            # writes system/system_ext/product/vendor ext4 images
```

`extract_parts.py` writes to `D:/tmp/opencode/parts/*.img` by default.

## 2. Pull the APKs out of the ext4 images

```sh
bash extract_apks.sh               # needs debugfs (e2fsprogs) on PATH
```

It uses `debugfs -R "rdump ..."` and writes to `D:/tmp/opencode/apks/`.
Note the layout difference: the `system` partition is "system-as-root", so
its apps live under `/system/app`, `/system/priv-app` and `/system/framework`;
`system_ext` and `product` have their apps at the root.

## 3. Read the resource tables

```sh
python build_corpus.py D:/tmp/opencode/corpus.tsv
```

`arsc.py` is a direct reader of the binary resource table format
(`ResTable_header`, `ResStringPool`, `ResTable_package`, `ResTable_type`,
`ResTable_entry`, `Res_value`).  Only the `string` type is kept, and only the
default and the Arabic configurations.  The SDK platform tables
(`platforms/android-*/data/res/values{,-ar}/strings.xml`) are read as plain
XML and appended.

## 4. Measure

```sh
python final_analysis.py D:/ai/kiloprojct/docs/research/label-corpus.txt out.json
python buttons.py       D:/ai/kiloprojct/docs/research/label-corpus.txt
python nonword.py       D:/ai/kiloprojct/docs/research/label-corpus.txt
python arvariants.py    D:/ai/kiloprojct/docs/research/label-corpus.txt
```

* `final_analysis.py` produces the per-entry tables (substring / whole-word /
  exact hit counts, the false-positive counts and the plausible-positive
  ratios) and the orthography census.
* `buttons.py` lists the button-shaped captions and whether the current
  `sendWords` / `paymentWords` catch them.
* `nonword.py` inventories the labels that are not ordinary words.
* `arvariants.py` counts the real Arabic spelling variants of each Arabic
  entry.
* `analyze.py` holds the shared matching-strategy definitions
  (`whole_word`, `is_short`) that the others import.

## Notes

* `whole_word` treats a character as a word character if it is an ASCII
  letter, a digit, an underscore, **or** a character in the Arabic blocks
  (U+0600-U+06FF, U+0750-U+077F, U+08A0-U+08FF, U+FB50-U+FDFF,
  U+FE70-U+FEFF).  This is Java's `\b` with `UNICODE_CHARACTER_CLASS`, not
  Java's default ASCII-only `\b`.
* `analyze.py` and `final_analysis.py` read the two word lists straight out of
  `protocol/src/main/kotlin/ai/androiduse/protocol/CapabilityResolver.kt` so
  the measurement cannot drift from the shipped list.
* The corpus file uses `##` at the start of a line for comments; no corpus
  label begins with `##`.
