# AndroidUse — product and technical specification

- Status: Draft for review
- Version: 0.1.0
- Date: 2026-10-20
- Related: [CONTEXT.md](../../CONTEXT.md),
  [ADRs](../adr/), [reference analysis](../research/reference-analysis.md)

## 1. Problem

People want their phones to do things for them — "find and book this flight",
"reply to the messages from my brother", "turn on dark mode and open the
settings for it" — without doing them by hand. Today that means either
doing it by hand or installing a desktop automation tool tethered to the
phone.

AndroidUse is an Android application that lets a **cloud** AI agent see the
phone's screen and carry out multi-step tasks on it, the way a Computer Use
agent drives a desktop, with **no root** and **no companion PC**.

## 2. Goals and non-goals

**Goals**

- G1. A user submits a goal in Arabic or English; the agent carries it out on
  the phone, across applications, in multiple steps.
- G2. The agent perceives the screen accurately enough to act on real apps,
  including Arabic-labelled ones.
- G3. The agent verifies its own results and recovers when a step fails.
- G4. Sensitive actions require an explicit user approval, and the user can
  always see and stop what the agent is doing.
- G5. The app runs on stock Android 10 (API 29) and later, with no root, no
  Shizuku, and no companion app on a PC.
- G6. The user can see exactly what happened: a transcript of the run, with
  the frames the agent saw.

**Non-goals** (see [CONTEXT.md](../../CONTEXT.md#non-goals) for the full list)

- Rooting, Shizuku, hidden-API input injection, virtual displays.
- An on-device model.
- General-purpose shell execution on the device.
- Reading SMS, contacts, location or camera in v1.

## 3. Personas

**P1 — Delegate (primary).** A person who wants a recurring chore done:
"every evening, tell my mother good night and set a 22:00 alarm". They set up
the task, watch the transcript, and approve the one action they do not want
automated.

**P2 — Assistant.** A person with a one-off multi-app task: "book the cheapest
flight from X to Y tomorrow morning". They watch it happen and intervene when
it goes wrong.

**P3 — Privacy-conscious.** A person who will not put a model key on their
phone, and who will not let an agent read their banking app. They are
comfortable with a server holding the key and with a capability policy that
they can read and change.

## 4. User-facing behaviour

### 4.1 Setup (one-time)

1. Install and open the app.
2. Pair with the Relay: the app shows a code, the user confirms it in the web
   console or by scanning. The device receives a revocable **device token**.
3. Grant the **Accessibility** service. The app explains in the user's
   language what this permits, and links to the system settings page.
4. Grant **MediaProjection** consent for screen capture. The app explains that
   this is how the agent sees the screen, that frames are not stored, and that
   consent is re-required after the app restarts on Android 14+.
5. Optionally grant **Notifications** for run status and approval requests.
6. Choose the default **Capability** policy: *Careful* (ask for anything
   consequential), *Balanced* (ask only for messages/calls/settings), or
   *Trust* (ask only for payments and credential access).

### 4.2 Running a task

1. The user types a goal, or dictates it, in Arabic or English.
2. The app shows a run card: the goal, the elapsed time, the step count, and
   the spend so far.
3. The **Overlay** appears over the current app showing the agent's current
   step in plain language ("Opening Settings", "Tapping 'Dark mode'").
4. The agent works. Each step is appended to the transcript.
5. If the agent needs an action the policy does not allow silently, the
   Overlay raises an **approval** card: what it wants to do, in which app, and
   why. The user allows once, allows for the session, allows for that app,
   or refuses.
6. At the end, the agent reports the result in the user's language, with a
   success or failure, and the transcript remains browsable.

### 4.3 Control

- The Overlay always has a **stop** control that ends the Run immediately.
- The user can **take over**: the agent pauses after the current step and the
  user can use the phone normally; the agent resumes when told.
- The user can **steer**: typing in the app while a Run is in flight injects
  the instruction at the next step boundary rather than queueing it.

## 5. System architecture

```
┌────────────────────────── AndroidUse app (Android 10+) ──────────────────────────┐
│  :app process                                                                     │
│    Compose UI  ·  Overlay  ·  Local Policy store  ·  RelayClient (WebSocket)     │
│         │  bound Messenger, signature-level permission (ADR-0005)                 │
│  :a11y process                                                                    │
│    DeviceAccessibilityService  ·  Frame capture (MediaProjection)  ·  Tree       │
│    Gesture executor  ·  Text typer  ·  Outcome classifier  ·  Budget guard       │
└──────────────────────────────┬───────────────────────────────────────────────────┘
                               │ wss
┌──────────────────────────────▼───────────────────────────────────────────────────┐
│  Relay (server)                                                                   │
│    Session auth  ·  Agent loop  ·  Provider adapters  ·  Budget enforcement      │
│    Approval broker  ·  Compaction  ·  Loop detection  ·  Spend accounting       │
│                                                                                   │
│    ──► Model providers (Anthropic / OpenAI-compatible / …)                        │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Responsibilities

| Component | Owns | Must not |
| --- | --- | --- |
| Relay | model credentials, the Agent loop, budgets, approvals, transcripts | touch the device except through the protocol |
| Device Agent | perception, execution, local policy, approval UI, local budget subset | decide anything, hold model credentials, run shell |
| `:protocol` | the action/observation/event types, generated JSON Schema | contain any Android or server-specific code |

### 5.2 The protocol

Each WebSocket **text** message carries exactly one JSON envelope. There is no
delimiter and no batching: a message that does not contain exactly one envelope
is a protocol violation, not a message to be salvaged. Every message carries a
`type`; the types are defined once in `:protocol` and used by both ends.

The framing is the WebSocket message boundary, because WebSocket is already a
message-framed transport. A newline-delimited format inside it would need a
reader, a writer and a delimiter that neither `:protocol` nor Ktor's
message-based WebSocket plugin has, and it would let the two ends disagree
about how many envelopes a message holds. Nothing in the protocol needs
batching: the Relay sends one `act` at a time, and the device answers with one
`outcome` per action.

A framing violation is fatal. The receiver closes the connection rather than
skipping the message, because the protocol has no `error` message in the
Relay-to-device direction, and a skipped `act` would leave the Agent waiting
forever.

**Authentication.** The device token is **not** a field in any envelope. It is
an HTTP header on the WebSocket upgrade - `Authorization: Bearer <token>` - so
the Relay authenticates the connection before it reads a single message. The
Relay looks the device up by the token and refuses the upgrade if the token is
unknown or revoked. `hello` then identifies the device, and the Relay refuses
the session if `hello`'s device id does not match the token's device.

**The `act` tool's schema does not travel on the device link.** The device
executes Actions; it does not call a model, and the action kinds are already
defined once in `:protocol`. The schema is the Provider-facing description of
the `act` tool, and it is sent in the Provider request, because a provider
requires the tool definition in every request. The Run's language - which
selects the schema's language - travels on `run_start`.

**Device → Relay**

| Type | Payload |
| --- | --- |
| `hello` | device id, app version, the device's language, and the Local Policy the device is enforcing |
| `perception` | frame (JPEG, base64) + tree (elements) + fingerprint + foreground package |
| `outcome` | the typed result of the action just executed |
| `approval_response` | the user's decision for a pending approval |
| `run_state` | step count, elapsed, spend estimate, current status |
| `error` | a device-side failure the Relay should surface |

**Relay → Device**

| Type | Payload |
| --- | --- |
| `run_start` | run id, goal, language, budget, and the Relay's mirror of the Local Policy |
| `act` | one action: kind, target, and kind-specific parameters |
| `approval_request` | what is wanted, in which app, why, and the possible decisions |
| `run_end` | outcome and the final message to show the user |
| `policy_update` | a *narrowing* of the local policy (never a widening) |
| `ping` | liveness |

**Action kinds** (ADR-0004): `screenshot`, `click`, `double_click`,
`long_press`, `drag`, `type`, `scroll`, `press_key`, `open_app`, `list_apps`,
`wait`, `finish`, `ask_user`.

**Target** is exactly one of: `{element_index}` or `{x, y}`.

**Outcomes** (typed, never prose): `ok`, `unchanged`, `stale_element`,
`denied`, `timeout`, `unsupported`, `failed`.

### 5.3 Perception

Per step the Device Agent sends a **frame** (JPEG, long edge ≤ 1280 px,
quality 72) and a **tree** (the interactive nodes of the foreground app, each
with text, content description, resource id, class, bounds and a rendered
index). The frame is what the model "sees"; the tree is what it "grinds"
against.

The tree is produced by the AccessibilityService and is also the channel that
performs actions. The frame is produced by MediaProjection. If MediaProjection
consent is unavailable, the frame is omitted and the run continues tree-only
with a recorded limitation.

### 5.4 Execution

Actions are executed by the AccessibilityService:

| Kind | Mechanism | Fallback chain |
| --- | --- | --- |
| `click` | `performAction(ACTION_CLICK)` on the addressed node | → nearest clickable ancestor → `dispatchGesture` tap at the node centre |
| `double_click` | two taps, 120 ms apart | — |
| `long_press` | `performAction(ACTION_LONG_CLICK)` | → `dispatchGesture` stroke |
| `drag` | `dispatchGesture` path | — |
| `type` | `ACTION_SET_TEXT` | → clipboard paste (`ACTION_PASTE`) → IME `commitText` |
| `scroll` | `performAction(ACTION_SCROLL_*)` | → `dispatchGesture` swipe |
| `press_key` | `performGlobalAction` (back/home/recents) | — |
| `open_app` | `PackageManager.getLaunchIntentForPackage` | → launch intent by label |

Every action is followed by a re-capture and a **Screen Fingerprint**
comparison, producing the typed **Outcome**. A click that changed nothing
returns `unchanged`, not `ok` — the agent must then look again rather than
assume success.

### 5.5 Approval

Per ADR-0003. The Device Agent maps each action kind to a **Capability** via
a sealed hierarchy, consults the **Local Policy**, and either runs, refuses,
or raises an approval request. The Relay is told the policy so it can avoid
proposing refused actions, but the device's copy is authoritative.

### 5.6 Budget

Per ADR-0006. The Relay enforces steps, wall-clock and spend; the device
enforces its own subset plus a per-capability rate limit.

## 6. Functional requirements

| ID | Requirement | Verified by |
| --- | --- | --- |
| FR-1 | The user can submit a goal in Arabic or English, by typing or by dictation. | UI test + unit test on language detection |
| FR-2 | The Relay can see the screen as an image and as a tree, every step. | protocol conformance test |
| FR-3 | The agent can tap, double-tap, long-press, drag, type, scroll, press a system key, launch an app, and wait. | device integration test per action kind |
| FR-4 | Typing works in fields where `ACTION_SET_TEXT` is rejected, via at least one fallback. | device integration test on a known-hard field |
| FR-5 | The agent can carry out a task spanning at least three applications. | end-to-end eval task |
| FR-6 | The agent's result is verified, not assumed: a no-op action is reported as `unchanged`. | unit test on the outcome classifier |
| FR-7 | A failed step is recoverable: the agent sees the outcome and can retry with a different grounding. | end-to-end eval task with a forced failure |
| FR-8 | A capability with an `ask` verdict produces an approval request before the action runs. | policy unit test + UI test |
| FR-9 | A capability with a `deny` verdict is never executed, even if the Relay requests it. | policy unit test, including a hostile-Relay case |
| FR-10 | The user can stop a Run from the Overlay within one second of tapping. | device test |
| FR-11 | The user can take over and resume. | device test |
| FR-12 | The transcript records every step, with the frames the agent saw (opt-in for retention). | transcript snapshot test |
| FR-13 | The Run stops at the budget boundary and tells the user which boundary was reached. | budget unit test |
| FR-14 | The agent's own reasoning and messages are in the user's language. | end-to-end Arabic eval task |
| FR-15 | The device holds no model-provider credential. | manifest + binary inspection test |

## 7. Non-functional requirements

| ID | Requirement |
| --- | --- |
| NFR-1 | Runs on Android 10 (API 29) and later, on a stock device, with no root. |
| NFR-2 | The model API key exists only in the Relay. |
| NFR-3 | No third-party application can drive the AccessibilityService (ADR-0005). |
| NFR-4 | The manifest declares only used permissions; no `QUERY_ALL_PACKAGES`, no SMS/contacts/camera/location in v1. |
| NFR-5 | Cleartext traffic is denied. |
| NFR-6 | A frame is never persisted unless the user opted into transcript recording. |
| NFR-7 | A Step's device-side latency (capture + execute) is under 400 ms at the 95th percentile. |
| NFR-8 | The unit test suite is green in CI on every push, and lint runs. |
| NFR-9 | The eval harness runs against a stub model with no API key, and the pass rate is recorded per task. |

## 8. Acceptance criteria for v1

1. On an API 29 emulator and an API 34 device, a user grants the three
   permissions and runs "open the clock app and set an alarm for 07:00" in
   Arabic; the transcript shows the goal, the steps, and a success message in
   Arabic.
2. A Run that reaches its step budget ends with `budget_exhausted` and names
   the budget.
3. A `message.send` action with the *Careful* policy produces an approval
   card and does not type until the user allows it.
4. A hostile Relay that asks for a `deny`-capability action is refused by the
   device, and the refusal appears in the transcript.
5. `grep` over the release manifest shows only the permissions in NFR-4.
6. The eval harness passes on a stub model with at least 4 scripted tasks.

## 9. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Play Store rejects an Accessibility-driven automation app | distribution blocked | sideload-first distribution; Play submission only with a policy-compliant framing; the core-function disclosure is a product decision (see research §4) |
| Model grounding on Arabic screens is weak | core promise fails | measure it with the eval harness before building more; the tree channel carries real Arabic text, which is the mitigation |
| MediaProjection consent churn on Android 14+ | interrupted Runs | detect the single-use token expiry and re-request consent explicitly |
| Relay cost scales with usage | unit economics | per-Run spend caps (ADR-0006); the business model is open |
| Accessibility grants are revoked by the user or by the system (background restrictions) | Runs fail | surface the service state prominently; fail with a clear outcome, never a silent hang |

## 10. Open decisions

- D1. Distribution: GitHub releases / Play / both.
- D2. Whether the Relay is open source and self-hostable, or a hosted service.
- D3. Whether the device token is a long-lived JWT or a rotating session.
- D4. Whether scheduled/recurring tasks are in v1 (P1's use case implies they
  are, but they need a background scheduler and survive the consent churn).
