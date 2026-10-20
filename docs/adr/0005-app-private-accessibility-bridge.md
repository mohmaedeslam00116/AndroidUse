# ADR-0005: The AccessibilityService command channel is app-private

- Status: Accepted
- Date: 2026-10-20

## Context

On a non-rooted phone, an AccessibilityService is the only component permitted
to synthesise touch input and to read another app's view hierarchy. It is
therefore the most privileged thing in the app, and the way the app's other
components talk to it is a security decision.

The references do it three ways:

- **CellClaw** — broadcasts a `com.cellclaw.ACCESSIBILITY_ACTION` intent and
  replies through a `ResultReceiver` extra. The receiver is declared
  `exported="true"`, so **any third-party app on the device can drive the
  AccessibilityService** — tap, type, swipe — and completely bypass the
  approval policy. This is a remote-control hole in a security product.
- **ClosePaw** — keeps the agent loop *inside* the AccessibilityService, so
  there is no cross-process channel to abuse. The service is
  `exported="true"`, which the platform requires for the system to bind it.
- **android-agent** — also hosts the agent loop inside the AccessibilityService,
  with a `DecisionReceiver` that is `exported="false"`.

## Decision

AndroidUse splits the app into two processes, because the Agent loop is in the
Relay and the AccessibilityService must survive the Activity being closed:

```
:app process     ── RelayClient, Compose UI, Overlay, policy store
      │
      │ bound Messenger (explicit Intent, signature-level permission)
      ▼
:a11y process    ── DeviceAccessibilityService, executors, capture
```

The channel is a **bound service with a signature-level permission**:

- The service is declared `exported="false"` with
  `android:permission="ai.androiduse.permission.DEVICE_CONTROL"`, declared
  with `android:protectionLevel="signature"`. Only our own build can bind it.
- The client binds with an explicit `Intent` naming our own component. It
  never uses a broadcast, and never uses an implicit intent.
- Every request carries a monotonically increasing id; every reply is a typed
  result, never a free-form string.
- The service verifies the calling package at bind time and again on every
  call, and refuses anything else.

## Consequences

**Good**

- No third-party app can drive the phone through us. The CellClaw hole does
  not exist in AndroidUse.
- The AccessibilityService lives in its own process, so a crash in the UI
  cannot take the executor down, and a long Run survives the Activity being
  closed — which is the behaviour all three references want and none of them
  get from the UI side.
- The permission boundary is visible in the manifest and auditable.

**Bad, and accepted**

- Two processes means `android:process=":a11y"`, which costs memory and makes
  debugging slightly harder.
- Cross-process calls are slower than in-process calls. Since every Action
  crosses the boundary, this is on the critical path of every Step. We keep
  the messages small and the capture on the a11y side.
- The service still has to be `exported="true"` — no: it does not. The
  AccessibilityService *is* exported (the platform requires
  `BIND_ACCESSIBILITY_SERVICE` to bind it), but the **control channel** is a
  separate, private service. This distinction is the point of the ADR.

**Neutral**

- The signature-level permission means the two processes must be signed with
  the same key. That is automatic for a single APK.

## Alternatives considered

**Keep the agent loop inside the AccessibilityService, like ClosePaw and
android-agent.** Rejected: the loop is in the Relay (ADR-0001), so the
executor must be reachable from the UI process.

**Exported broadcast + ResultReceiver, like CellClaw.** Rejected: that is the
vulnerability, not the pattern.

**ContentProvider call.** Rejected: it works, but it exposes a queryable
surface to any app that can guess the authority, and it gives no per-call
caller identity. A bound service with a signature permission does.

## Related

- [ADR-0001](0001-cloud-agent-relay.md) — why the loop is not on the device
- [ADR-0008](0008-no-shell-no-unrestricted-file-io.md) — the other half of the
  privilege story
