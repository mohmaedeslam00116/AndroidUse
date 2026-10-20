# ADR-0002: MediaProjection is the primary pixel channel; the accessibility tree is the structural channel

- Status: Accepted
- Date: 2026-10-20

## Context

AndroidUse targets **Android 10 (API 29) and later**. That single constraint
decides the Perception design, because the two ways to obtain pixels on a
non-rooted device have different floors:

| Mechanism | Floor | Notes |
| --- | --- | --- |
| `AccessibilityService.takeScreenshot()` | **API 30** | Available to any accessibility service; no user consent step |
| `MediaProjection` | API 19 (usable from 21) | Requires an explicit user consent, per session |
| `screencap` via shell | API 29+ | Needs shell privileges; not available to a normal app |

`android-agent` resolves this by setting `minSdk = 30` and dropping API 29
entirely. CellClaw keeps `minSdk = 26` and, on API 26-29, falls back to
running `screencap -p` through `Runtime.exec` — which a normal app cannot
actually do, so that path does not work. ClosePaw sets `minSdk = 31` and uses
`takeScreenshot`, with screenshots off by default and the accessibility tree as
the default channel.

Our requirement is explicitly Android 10+, so **API 29 must work**.

## Decision

**MediaProjection is the primary pixel channel on every supported API level.**
The AccessibilityService tree is the **structural** channel: it supplies
grounding (element indices, text, bounds) and it is the only channel that can
perform an Action.

Rationale:

- It is the only pixel source that works on API 29 for a normal app.
- It captures the *real* display, including system UI, dialogs, and the
  keyboard — the Agent needs to see the dialog it is being asked to dismiss.
- The consent flow is a one-time-per-session user action that we can fold into
  onboarding, whereas the accessibility service is a permanent grant.
- MediaProjection is not rate-limited the way `takeScreenshot` is. ClosePaw and
  android-agent both throttle or sleep between captures (1 s in
  android-agent); with a frame every Step, a 30-Step run would burn 30 s
  sleeping.

The accessibility tree is kept as a *first-class* channel, not a fallback,
because it is strictly better for grounding: it gives the Agent stable
element indices and real text, where a screenshot gives only pixels.

The `takeScreenshot` path is retained as an **optional secondary frame source**
on API 30+, used when the user declines MediaProjection consent and the task
does not need system UI.

## Consequences

**Good**

- API 29 is genuinely supported, not nominally.
- The Agent sees exactly what the user sees, including permission dialogs and
  the IME.
- No sleep-based rate-limit hacks; Step latency is dominated by the Relay
  round-trip, not by capture.

**Bad, and accepted**

- MediaProjection consent is a per-session user grant. On Android 14+ the
  consent token is single-use, so a Run that spans a process death must ask
  again. The Device Agent must detect this and request re-consent rather than
  failing opaquely.
- MediaProjection requires a foreground service with type
  `mediaProjection`. On Android 14+ that service must already be running when
  `getMediaProjection()` is called, so the FGS must be started *before* the
  consent intent. This is a real ordering constraint and it is why our
  permission request order differs from all three references.
- `MediaProjection` captures system UI, so the Overlay must be hidden or
  excluded around captures, or the Agent sees its own status bubble.

**Neutral**

- Frames are ephemeral by default. They are not written to disk unless the user
  opts into a transcript recording.

## Alternatives considered

**`takeScreenshot` only, with `minSdk = 30`.** Rejected: the user explicitly
asked for Android 10+.

**`screencap` through shell on API 29.** Rejected: not executable by a
normal app. CellClaw's version of this does not work.

**Accessibility tree only, no pixels, like CellClaw's default path.** Rejected:
the Agent would be navigating blind, and its "vision" would be a separate
text-only round-trip rather than a real look at the screen. This is the single
biggest architectural difference we are taking from CellClaw.

## Related

- [ADR-0007](0007-arabic-first.md) — the Overlay is also the Approval surface
