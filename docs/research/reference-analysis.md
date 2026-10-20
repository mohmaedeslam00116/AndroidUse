# Reference analysis: ClosePaw, CellClaw, android-agent

Analysis performed 2026-10-20 as the input to AndroidUse's design. Three
upstream projects were read in full and two of their **shipped release APKs**
were inspected with REA (JADX headless provider 0.7.1).

Artefacts used:

| Artefact | Identity | How it was read |
| --- | --- | --- |
| `imoonkey/closepaw` @ `75dae26` | Apache-2.0 source, `NOTICE` disclaims the proprietary Leap SDK | full source read |
| `imoonkey/closepaw` v0.1.0 release APK | `ai.closepaw`, 147 038 316 B, minSdk 31, targetSdk 36, 13 541 classes | **REA `inspect_android_package`** |
| `frido22/cellclaw` @ master | Kotlin, **no LICENSE file** (README claims MIT) | full source read |
| `Fox-Islam/android-agent` @ `2026-09-13` | Kotlin, **no LICENSE file** | full source read |
| `Fox-Islam/android-agent` v1.1.0 release APK | `com.foxislam.androidagent`, 3 214 416 B, minSdk 30, targetSdk 35, 3 659 classes | **REA `inspect_android_package`, `search_android_classes`, `inspect_android_class`** |

> **Licence caution.** Only ClosePaw ships a licence file (Apache-2.0, with the
> proprietary-SDK carve-out in its `NOTICE`). CellClaw and android-agent have
> no `LICENSE`, `COPYING` or `NOTICE` file at all. Nothing from those two
> projects may be copied into AndroidUse. This analysis reads them for design
> comparison only.

---

## 1. What each project actually is

### ClosePaw (`imoonkey/closepaw`)

The most mature of the three, and the closest to what we want in shape.

- **Loop**: on-device, inside the `AccessibilityService`, with a per-turn
  pipeline of PERCEPTION → PLANNING → EXECUTION.
- **Perception**: accessibility node tree as the *default* channel; an
  `AccessibilityService.takeScreenshot` path exists but is gated to API 30+
  and is **off by default** (`PerceptionConfig.AccessibilityOnly` is the
  runtime default). Long edge ≤ 1024 px, JPEG q70.
- **Actions**: 10 `UIAction` variants, each mapping to exactly one Android
  API call, plus a fallback chain per action
  (`NODE_CLICK → GESTURE_TAP`, `A11Y_SCROLL → GESTURE_SWIPE`).
- **Typing**: `ACTION_SET_TEXT` only. No clipboard, no IME injection.
- **Tool surface**: one `mobile_action` tool with a flat parameter set, plus
  `open_app`, `system_button`, `complete_task`, `write_todos`, `scratchpad`,
  `ask_user`, `shell`, `termux_shell`, `activate_skill`, `delegate_task`,
  `browser_script`.
- **Security**: genuinely strong. A bundled 35-package `BLOCKED` list for
  banking/finance/auth, refused as an *absolute floor* that no user override
  can lift; four independent masking layers; `FLAG_SECURE` handling; password
  fields replaced with `[password]`; `allowBackup="false"`; cleartext allowed
  only for `127.0.0.1`.
- **Background**: a virtual display created through Shizuku
  (`IDisplayManager.createVirtualDisplay`) with `MotionEvent` injection via
  `InputEvent.setDisplayId()` and a shell fallback. It is a substantial
  subsystem with a lifecycle arbiter, IME juggling and task cleanup.
- **Testing**: 2 057 JVM unit tests, 111 instrumented, 120 pytest evals, and
  57+ documented prompt-tuning rounds. The unit layer is the strongest of the
  three.
- **Weakness that matters to us**: the production loop has **no turn cap and
  no wall-clock cap** — the project's own docs say so.

### CellClaw (`frido22/cellclaw`)

- **Loop**: on-device in the app process; inference direct to Anthropic /
  OpenAI / Gemini / OpenRouter.
- **Perception**: accessibility tree only, plus `takeScreenshot` on API 30+
  (`screencap` shell on API 26-29, which does not work for a normal app).
- **The decisive gap**: the screenshot is **never given to the model as an
  image**. `screen.capture` returns a file path; the model must then call
  `vision.analyze`, which makes a *second* cloud call and returns **text**.
  The loop is text-only.
- **Actions**: 34 flat tools, including `script.exec` (arbitrary shell) and
  `file.read`/`write`/`list` with absolute paths and no sandbox.
- **Approval**: a 3-tier autonomy policy per tool, surfaced in four places
  (chat card, approvals screen, notification action, overlay bubble).
- **Serious defects**: the persisted autonomy profile is **never restored at
  startup**, so a "Cautious" user silently gets `FULL_AUTO` after a restart;
  the AccessibilityService command channel is an **exported broadcast**, so any
  app can drive taps and typing; `BiometricGate` is dead code that the README
  advertises; the unit tests are red on arrival (they assert superseded model
  IDs) and the instrumented tests do not compile; there is no CI.
- **No Arabic, no RTL, no STT/TTS in the codebase.**

### android-agent (`Fox-Islam/android-agent`)

- **Loop**: on-device inside the AccessibilityService; OpenRouter
  `/chat/completions` over HTTP with SSE; MCP **client** support.
- **Perception**: accessibility tree as the primary channel, plus
  `takeScreenshot` (API 30+ — its `minSdk` is 30 for exactly this reason).
  Long edge ≤ 1100 px, JPEG q70, **at most 2 images retained in context**,
  with a 1 s sleep between captures to dodge
  `ERROR_TAKE_SCREENSHOT_INTERVAL_TIME_SHORT`.
- **Actions**: 25 tools plus a Lua scripting escape hatch.
- **The best idea in any of the three**: a single **control-plane gate**
  (`ToolPipeline`) that every route to the device passes through, including
  sub-steps of a batch and every action inside a Lua script. Capability is
  *withheld* in plan mode (the tool list itself is reduced), rather than
  requested in a prompt.
- **Also excellent**: an append-only event log with projections, so the
  transcript and the model messages derive from one source and cannot drift;
  and a **stub-model eval harness** (`eval/stub_model.py`) that makes
  compaction, retry and refusal paths testable with no API key.
- **Weakness**: `while (true)` with **no step cap and no cost cap**; failure
  detection by English substring matching; `type_text` via `ACTION_SET_TEXT`
  only; global cleartext permitted; no licence file.

---

## 2. What REA added that the source did not

REA was used on the two **shipped** release APKs, which is exactly the case it
is for: the released binary is the artefact users actually install.

**Manifest and permission facts, observed rather than inferred:**

| | ClosePaw v0.1.0 | android-agent v1.1.0 |
| --- | --- | --- |
| package | `ai.closepaw` | `com.foxislam.androidagent` |
| minSdk / targetSdk | **31** / 36 | **30** / 35 |
| classes / resources | 13 541 / 251 | 3 659 / 77 |
| permissions | `INTERNET`, `SYSTEM_ALERT_WINDOW`, `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, **`com.termux.permission.RUN_COMMAND`**, **`moe.shizuku.manager.permission.API_V23`**, `RECORD_AUDIO` | `INTERNET`, `POST_NOTIFICATIONS`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_SPECIAL_USE`, `SYSTEM_ALERT_WINDOW` |
| foreground service | **none** | `specialUse` + `PROPERTY_SPECIAL_USE_FGS_SUBTYPE` |
| `<queries>` | Termux, speech recognition | LAUNCHER intent only |

Two facts came only from the released binary and materially change the design:

1. **ClosePaw ships no foreground service at all.** Its agent loop lives
   inside the AccessibilityService, which is a bound system service, so it
   survives the Activity being closed with no FGS declaration. This is a
   simpler answer than an FGS, and it is available to us too.
2. **ClosePaw's release binary really does carry the Termux and Shizuku
   permissions**, confirming that the shell-adjacent surface is in the shipped
   product, not just in the source tree. We are declining that surface
   (ADR-0008), and this is the evidence that the decision costs something
   real.

**A negative result worth recording.** `inspect_android_class` on
`com.foxislam.androidagent.control.ControlService` in the shipped v1.1.0 APK
returns methods named `a`–`h` and fields named `f5101h`–`f5109g`: the
release is **R8-obfuscated**. A class census of all 3 659 classes shows the
application's own code reduced to single-letter packages (`A`, `A0`, `B`,
`G0`, `J`, …). So for both references, the *shipped binary* is authoritative
for the manifest and the *source tree* is authoritative for the logic; REA
cannot read the logic of an obfuscated release. This is also a fact about our
own release engineering: readable names in debug builds are worth having.

---

## 3. Gap analysis: what AndroidUse should take, and what it should not

| Decision | ClosePaw | CellClaw | android-agent | **AndroidUse** | Source |
| --- | --- | --- | --- | --- | --- |
| Where the Agent loop runs | device | device | device | **Relay (cloud)** | ADR-0001 |
| Model key on device | yes | yes | yes | **no** | ADR-0001 |
| Pixel channel | `takeScreenshot` (API 30+, off by default) | **none reaches the model** | `takeScreenshot` (API 30+) | **MediaProjection, all API levels** | ADR-0002 |
| minSdk | 31 | 26 (unusable below 30) | 30 | **29** | requirement |
| Action surface | 1 tool + 12 siblings | 34 tools | 25 tools + Lua | **1 tool, discriminated union** | ADR-0004 |
| Approval axis | app package | tool | tool + regex | **Capability** | ADR-0003 |
| Approval enforced on device | yes | yes (but **not persisted**) | yes | **yes, authoritative, persisted** | ADR-0003 |
| Step / time / spend caps | **none** | **none** | **none** | **all three, both ends** | ADR-0006 |
| Failure signalling | typed `ActionResult` | JSON blob | **English substring match** | **typed `Outcome`** | ADR-0004 |
| Shell / arbitrary file IO | `shell`, `termux_shell` | `script.exec`, absolute-path file tools | Lua scripts | **none** | ADR-0008 |
| Cross-app command channel | n/a (in-process) | **exported broadcast** | in-process | **app-private bound service** | ADR-0005 |
| Arabic / RTL | none | none | none | **first-class** | ADR-0007 |
| Tests | 2 057 unit + 111 instr. + 120 eval | 15 unit, **red**, instr. **won't compile** | 10 unit + eval harness | to be built on the eval-harness idea | — |

### What we take

- **ClosePaw**: the one-API-per-action discipline; the node-identity guard
  before a click; the layered `BLOCKED`-app masking idea, generalised into
  Capabilities; `FLAG_SECURE` and password-field handling; the
  `ACTION_SET_TEXT` read-back verification.
- **CellClaw**: the provider-agnostic content-block abstraction; the
  cross-process `ResultReceiver` idea (rebuilt as a bound service); the
  four-surface approval UX redundancy; the Android Keystore key handling
  (we use it for the *device token*, not a model key).
- **android-agent**: the single control-plane gate that every route to the
  device passes through; *withholding* capability by reducing the tool list
  instead of instructing the model; the append-only event log with
  projections; the stub-model eval harness; the system prompt's discipline
  ("do not assume an action worked", and an explicit stop rule for
  irreversible-sounding steps).

### What we refuse

- ClosePaw's Shizuku virtual-display subsystem. It buys background execution
  we do not need, at a large complexity cost, and it requires a per-device
  setup step.
- CellClaw's `script.exec`, absolute-path file tools, and exported command
  broadcast.
- android-agent's global cleartext, alpha crypto dependency, and English
  failure detection.
- Every reference's absent budget.

---

## 4. Open questions carried forward

1. **Play Store viability.** All three use AccessibilityService to drive other
   apps, which is exactly what Google's Accessibility API policy restricts. The
   references respond by shipping outside Play (ClosePaw via a closed testing
   group; the others via GitHub releases). AndroidUse needs a distribution
   decision before v1: sideload-first, or Play with a disclosure that
   Accessibility is the core function.
2. **MediaProjection consent churn.** On Android 14+ the consent token is
   single-use, so a Run interrupted by a process death needs re-consent. How
   that surfaces without feeling broken is an open UX question.
3. **Arabic model quality.** Arabic screen text in an accessibility tree is
   harder for models to ground on than Latin text. This needs measuring, not
   assuming, and the eval harness (ADR-0004's sibling work) is the place to
   measure it.
4. **Relay operating cost.** ADR-0001 moves the token cost to us. The spend
   cap in ADR-0006 bounds a single Run; the business model that bounds the
   Relay is not decided.
