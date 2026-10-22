# ADR-0009: The Screen Fingerprint answers "did the screen change?"; the Screen Set answers "is the Agent repeating itself?"

- Status: Accepted
- Date: 2026-10-22

## Context

The **Screen Fingerprint** is load-bearing in three places, and two of them
want different things from it.

- **Outcome classification.** #4 (TB-3) returns `unchanged` instead of `ok`
  when the fingerprint does not move. This needs *equality*.
- **Loop detection.** ADR-0006 has the Relay compare consecutive Screen
  Fingerprints and treat "5 consecutive near-identical screens (Jaccard ≥ 0.95)"
  as a stall. This needs *similarity*.
- **Element Index invalidation.** #8 (TB-7) refuses to act on a stale index.
  This needs neither: `CONTEXT.md` already says a new Perception invalidates
  every index it produced.

A hash cannot be Jaccard-compared. Our own tickets therefore defined the
Screen Fingerprint incompatibly:

- `CONTEXT.md` calls it "a short hash over the salient contents of a
  Perception (visible text, element geometry, foreground package)".
- #2 (TB-1) briefs it as "a Screen Fingerprint over the visible text, the
  element geometry and the foreground package" - tree only, no frame.
- #3 (TB-2) makes it an acceptance criterion that "the fingerprint changes on
  a **pixel-only** screen change".

A pixel-only change - a video playing, a canvas-drawn view, an animated
surface with no accessibility nodes - changes neither the tree nor the
foreground package, so a tree-only fingerprint cannot detect it. Under #2's
definition #3's criterion is unsatisfiable, and worse, a canvas screen is
permanently "unchanged": the Agent is told its tap did nothing when it did
something.

ADR-0006's Jaccard had a second, quieter problem: the Jaccard set was never
defined in any document. Not the elements of the set, and not the
fingerprint's own composition. `Perception.fingerprint` was just `String?`
(`Perception.kt:66`).

Two facts make the resolution cheap:

- **The frame is captured and JPEG-encoded every Step.** ADR-0002 makes
  MediaProjection the primary pixel channel "on every supported API level",
  and spec section 5.3 sends a frame per step. A pixel digest is therefore
  not a new capture - it is a downscale and a hash over an image that already
  exists.
- **The tree is the only channel that is never absent.** The frame can be
  missing: ADR-0002 records that on Android 14+ the MediaProjection consent
  token is single-use, and spec section 5.3 says that without consent the
  frame is omitted and the run continues tree-only.

## Decision

There are **two artifacts**, with one job each.

### 1. The Screen Fingerprint - equality, carried on the wire

`Perception.fingerprint` stays a `String?`. Its value is composite and
self-describing:

```
v1;tree=<h>;pkg=<p>;px=<d>
```

| Part | Meaning |
| --- | --- |
| `v1` | the format version, so a future format is a new value, not a silent change |
| `tree=<h>` | a hash over the Perception's **text lines** (see the Screen Set below) |
| `pkg=<p>` | the foreground package |
| `px=<d>` | the perceptual digest of the frame, or `none` when the Perception has no frame |

The Device Agent compares two fingerprints **part by part**. A part is
compared only when both sides carry it; "the screen changed" means any
comparable part differs. `tree` and `pkg` are compared by equality, `px` by
Hamming distance. A missing frame therefore needs no special case: the `px`
part is simply not comparable, and the tree parts still are.

### 2. The Screen Set - similarity, derived on both ends

The **Screen Set** of a Perception is the canonical set of its salient text
lines, plus one distinguished package token:

- for every indexed element, its `text` and its `contentDescription`, each
  non-empty, normalised (lower-cased, diacritics and tatweel stripped, alef
  and yeh and teh-marbuta unified) and taken as a whole line;
- plus the token `pkg:<foregroundPackage>`.

It is a **set**, not a multiset, and it contains no geometry, no class and no
resource id. It is derived from the **tree alone**, so the Relay computes it
from the tree it already receives on every Perception. Nothing new crosses the
wire, and `Perception` gains no field.

The word "salient" is dropped on purpose. It was never defined, and the tree
is already filtered to interactive nodes, so the set is every visible line in
the tree with no further selection.

### 3. The pixel digest

`px=<d>` is a 64-bit **dHash** over a downscaled greyscale frame, computed on
the device **from the same frame instance that is sent**. Two frames differ
when more than **3 of the 64 bits** differ.

The frame is hashed rather than compared, because a pixel comparison is
relative to the previous capture while a fingerprint is an absolute value
carried per Perception. Only an absolute value can be compared between two
consecutive Perceptions.

The digest is computed from the frame that is sent, so **the Overlay must be
hidden or excluded before that capture**. ADR-0002 already requires this for
the frame; it is now part of the fingerprint's contract too, because a capture
that caught the Overlay would change the digest on every Step.

### 4. The shared functions

The Screen Set derivation, the text normalisation, and the fingerprint
parse-and-compare live in `:protocol` as pure functions over
`List<UiElement>` and `String`. `:protocol` is a plain JVM module, so this is
possible, and the point is that the device and the Relay **cannot** compute
different Screen Sets from the same tree.

The dHash *computation* needs a decoded bitmap and stays device-side. Only its
result travels.

## Consequences

**Good**

- #3's pixel-only criterion becomes satisfiable, and it is satisfiable
  cheaply: the frame is already captured and encoded every Step.
- ADR-0006's "near-identical" becomes computable, from data the Relay already
  has. No wire change, no change to `Perception`, no new `Outcome`.
- A screen that changes only in pixels is reported as changed, so the Agent
  is no longer told its tap did nothing when it did something.
- A screen whose tree is static (a video, a stuck animation) yields a
  Jaccard of 1.0, so the stall detector still fires on it.
- An app switch changes the Screen Set, because the package token is in it.

**Bad, and accepted**

- `unchanged` fires less often than a tree-only fingerprint would allow. That
  is the honest reading: a blinking cursor or a spinner *is* a change. The
  Agent re-perceives either way, so the cost is a lost hint, not a lost fact.
- Two thresholds are not calibrated against real captures: the Hamming
  threshold of 3 and ADR-0006's Jaccard of 0.95. No device is available to the
  maintainer, so both are named constants and their calibration is recorded
  as not locally verifiable.
- A fixed Jaccard threshold on a set of variable size is not scale-invariant:
  one changed line out of twenty scores the same as ten out of two hundred.
  ADR-0006's 0.95 is kept as written; retuning it belongs to the budget work,
  not to this decision.
- `:protocol` gains functions, not only types. The contract suite must prove
  that the device and the Relay derive the same Screen Set from the same tree.
- The fingerprint string is a format, and a format is a promise. `v1` is the
  escape hatch, but a reader that has not been taught `v2` must reject it
  rather than guess.

**Neutral**

- The Element Index is invalidated by a new Perception, not by the
  fingerprint. This ADR does not change #8 (TB-7).
- The fingerprint is computed on the device, so it costs the device a
  downscale and a hash per Step. The frame was being produced anyway.

## Alternatives considered

**One hash over the tree only** - today's definition. Rejected: it cannot
satisfy #3's pixel-only criterion, and a canvas or video screen is then
permanently "unchanged".

**One artifact carrying both the hash and the set.** Rejected: it changes
`Perception.fingerprint`'s type, changes the wire, and makes #2 and #3
re-shape a protocol that the contract suite already pins.

**Detect the stall on the device.** Rejected: the Relay sees the Agent's tool
calls and the device does not. "You appear to be repeating yourself" is a
statement about the Agent's behaviour, not only about a screen. The device's
budget subset stays a step and duration cap (ADR-0006).

**Compare pixels directly instead of hashing them.** Rejected: a pixel
comparison is relative to the previous capture, while a fingerprint is an
absolute value carried per Perception.

**Fold the frame in only when the tree is empty.** Rejected: the fingerprint's
composition would change mid-Run, making two fingerprints incomparable across
the switch, and it does not cover a screen with a static tree over a moving
picture.

**Hash the tree and the frame into one digest.** Rejected: when the frame is
absent the digest means something different, so a comparison across that
boundary is meaningless. Keeping the parts separate makes the missing part
simply not comparable.

**Let the stall detector also read the Agent's action sequence.** Not decided
here; it is recorded as fog on the wayfinder map.

## Related

- [ADR-0002](0002-mediaprojection-primary-perception.md) - the frame is
  captured every Step, which is what makes the pixel digest cheap.
- [ADR-0006](0006-run-budgets.md) - loop detection, amended to compare Screen
  Sets.
