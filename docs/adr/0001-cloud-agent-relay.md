# ADR-0001: The Agent loop runs in the cloud Relay, not on the device

- Status: Accepted
- Date: 2026-10-20
- Context: [docs/research/reference-analysis.md](../research/reference-analysis.md)

## Context

AndroidUse's stated requirement is a **cloud** AI agent that controls the phone
and executes tasks on it. That is a different topology from all three reference
projects, each of which keeps the Agent loop in the phone's own process and
calls the model vendor directly from the device:

| Project | Loop location | Model credentials |
| --- | --- | --- |
| ClosePaw | on-device, inside the AccessibilityService | on device (EncryptedSharedPreferences) |
| CellClaw | on-device, in the app process | on device (Android Keystore) |
| android-agent | on-device, inside the AccessibilityService | on device (EncryptedSharedPreferences) |
| **AndroidUse** | **Relay (server)** | **never leave the server** |

The difference is not cosmetic. It decides where the trust boundary sits, who
pays for a runaway loop, and whether the phone is usable when the network is
not.

## Decision

The Agent loop lives in the **Relay**. The phone is a **Device Agent**: an
executor plus a Perception source plus a policy gate.

The Relay owns:

- the model provider credentials and the model routing between them;
- the Run Budget, including spend accounting against actual provider usage;
- the per-Run prompt, the tool/action schema, and the Agent skill catalogue;
- the policy that decides when to request an **Approval**;
- a remote kill-switch: a Run can be terminated server-side.

The Device Agent owns:

- Perception (MediaProjection frame, AccessibilityService tree);
- Action execution;
- the **Local Policy**, which is authoritative and cannot be widened by the
  Relay;
- the **Approval** UI and the transcript the user reads.

## Consequences

**Good**

- The model key never exists on the phone. A lost or stolen phone exposes
  conversations, not credentials.
- Model routing, prompt improvements, and new skills ship without an app
  release.
- Spend is bounded by a server that can see provider usage, not by a heuristic
  on the device.
- A runaway loop is stopped by the server, not only by the user.

**Bad, and accepted**

- AndroidUse is unusable as a phone-automation product without the Relay. We
  are building a two-part system, and the Relay is on the critical path for
  every feature except setup and the transcript viewer.
- The Relay is a trust boundary and a single point of failure. It must be
  treated as a security-relevant service: authenticated device sessions,
  encrypted transport, no long-lived shared secrets on the device beyond a
  revocable per-device token.
- Network latency is now inside every Step. Step budgets must be set with that
  in mind.

**Neutral**

- The Device Agent still needs the local policy and the Approval UI, because a
  Relay that is compromised, buggy, or simply wrong must not be able to type
  into a banking app. The server decides *when to ask*; the device decides
  *what is allowed at all*.

## Alternatives considered

**Keep the loop on-device, like the references.** Rejected: it puts the model
key on the phone, makes cost unbudgetable, and makes the product a
BYO-key tool rather than a service.

**Hybrid: the loop on-device, the model in the cloud.** This is what the
references do. It is indistinguishable from the cloud case in terms of where
the key lives, and it is strictly worse for cost control.

**Remote ADB, like `ghost-in-the-droid/android-agent`.** Rejected: requires a
host machine tethered to the phone, which contradicts "an app on my phone".

## Related

- [ADR-0003](0003-capability-based-approval.md) — the Local Policy
- [ADR-0006](0006-run-budgets.md) — the Run Budget
