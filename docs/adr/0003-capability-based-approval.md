# ADR-0003: Approval is granted per Capability and enforced on the device

- Status: Accepted
- Date: 2026-10-20

## Context

The user's requirement includes "requesting user approval when executing
sensitive actions". All three reference projects implement something here, and
each does it differently:

| Project | Granularity | Where it lives | Persisted? | Failure mode |
| --- | --- | --- | --- | --- |
| ClosePaw | per **app package**, tiered (`BLOCKED` / `CAUTIOUS` / `NORMAL`), 35 hard-coded financial/auth packages blocked absolutely | device | yes | English/US-centric list; a non-US bank is "NORMAL" |
| CellClaw | per **tool**, 3 autonomy profiles | device | **no** — the profile is only restored when the user changes it in Settings | after a restart the policy silently reverts to `FULL_AUTO` |
| android-agent | per **tool**, via a rules DSL plus a risky-word regex and a risky-package regex | device | yes | failure detection is English substring matching, so a screen that merely *contains* the word "Failed" is treated as a failure |
| **AndroidUse** | per **Capability** | device, authoritative; Relay may only narrow | yes | — |

## Decision

Every **Action** maps to exactly one **Capability**. The Device Agent holds a
**Local Policy** that assigns each Capability a verdict:

- `allow` — run without asking.
- `ask` — raise an **Approval** request, wait for the human.
- `deny` — refuse, regardless of what the Relay asks for.

Rules:

1. The Local Policy is **authoritative**. The Relay may request a more
   restrictive verdict but can never move a Capability from `deny` or `ask` to
   `allow`. This is the defence-in-depth boundary: a compromised or buggy
   Relay cannot talk the phone into a banking app.
2. `deny` is final. The Agent is told the Capability is unavailable so it does
   not retry the same class of action.
3. The default policy ships `deny` for the genuinely irreversible Capabilities
   (`payment.authorize`, `account.change`, `credential.read`) and `ask` for the
   merely consequential ones (`message.send`, `call.place`, `settings.write`).
   Everything observational is `allow`.
4. An Approval grant is scoped: `once`, `session`, or `always_for_package`.
   `always_for_package` is only offered for `ask` Capabilities and is
   revocable at any time.
5. Approvals are raised on the device, rendered on the **Overlay**, and
   answered there. A Run waiting for approval has a hard timeout after which
   the Action is refused with Outcome `denied` — an approval never blocks a
   Run forever.

The Relay holds a *mirror* of the policy so it can avoid proposing actions it
knows will be refused, and so the transcript can explain *why* something was
refused. The mirror is advisory; the device's copy is the one that counts.

## Consequences

**Good**

- The policy is comprehensible to a user: "this app can type, but it may not
  send messages without asking" is understandable in a way that "per-tool"
  or "per-package" policy lists are not.
- It is locale- and jurisdiction-neutral: it is expressed in capabilities, not
  in a list of American bank package names.
- It survives restarts, and it cannot be silently relaxed.
- It is testable: a table of capability → verdict → expected outcome, with no
  package-specific fixtures.

**Bad, and accepted**

- A capability list has to be maintained, and a new Action type must declare
  its Capability at compile time. We make that a sealed hierarchy so the
  compiler forces the mapping.
- It does not capture "this particular app is sensitive". `always_for_package`
  covers the common case, and users who need more can be told how.

**Neutral**

- The Relay has to learn the policy vocabulary, which is now part of the
  protocol. That is a cost, paid once, in ADR-0004's action schema.

## Alternatives considered

**Per-app package tiers, like ClosePaw.** Rejected as the primary axis: it
needs a hard-coded list of package names that is jurisdiction-specific and
perpetually out of date. We keep package-scoped grants, but only as a
*scope* on an Approval, not as the primary classification.

**Per-tool policy, like CellClaw and android-agent.** Rejected: a flat tool
list makes the policy a list of implementation details. It also does not
compose: "typing is fine, but typing into a password field is not" is
unexpressible per tool.

**Trust the Relay to enforce policy.** Rejected outright. The Relay is a
remote service; the phone is the thing being protected.

## Amendment (2026-10-20): effective capabilities

Implementing the protocol surfaced a hole in the design above, and it is
important enough to record rather than quietly patch.

A computer-use action set describes **gestures**. Tapping a button is
`INPUT_TAP`; tapping the Send button in a chat app is *really* `MESSAGE_SEND`;
tapping "Pay" is `PAYMENT_AUTHORIZE`; typing into a password field is
`CREDENTIAL_READ`. If the capability comes only from the action kind, then
**the capabilities that matter most are never triggered** — the agent sends a
message with a plain tap, and the policy lets it through, because the policy
was written about taps.

This is not hypothetical in the references. ClosePaw solves it with a
hard-coded list of 35 banking package names; android-agent solves it with a
regex over package names and English words. Both are static and
jurisdiction-specific, and both miss the case where the sensitive action is
not in a "known sensitive app" at all.

**The decision:** the capability of an action is the **effective capability**,
resolved by the device from the action *and* its context:

- the action's own base capability (`INPUT_TAP` for a click, `INPUT_TEXT` for
  a type);
- the foreground package;
- the text and content description of the element the action addresses;
- whether that element is a password field.

Escalations, and only escalations — a gesture may be made *more* dangerous,
never less:

| Situation | Effective capability |
| --- | --- |
| a press whose target reads "Send" / "إرسال" | `MESSAGE_SEND` |
| a press whose target reads "Pay" / "دفع" | `PAYMENT_AUTHORIZE` |
| typing into a password field | `CREDENTIAL_READ` |

The word lists are bilingual and live in the protocol module
(`CapabilityResolver`), so they are testable and versioned with the wire
format rather than buried in an app.

**Why the device, not the relay.** The device is the only party that can see
the element the agent is about to touch. If the relay decided, the relay would
have to trust the agent's description of what it is about to do — which is
exactly the thing an untrusted model may get wrong, or be induced to get wrong.

**Consequence.** The approval policy now has to be written against a
capability that is resolved at execution time, not at request time. The relay
therefore receives the *effective* capability in the outcome, and the device
raises the approval **before** the action runs. The relay's mirror of the
policy remains advisory and is still narrowing-only.

**Open.** The word lists are a heuristic. They will produce false positives
(a button that happens to contain the word "ok") and false negatives (a Send
button labelled with an icon, which has no text at all). The icon case is the
serious one: an element with no text cannot be classified from its label, and
classifying it from its position in a known screen layout is a different and
much larger problem. This is tracked as an open question in
`docs/research/reference-analysis.md` §4.

## Related

- [ADR-0001](0001-cloud-agent-relay.md) — the Relay
- [ADR-0006](0006-run-budgets.md) — budgets are enforced in the same place
