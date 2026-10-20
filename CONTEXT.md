# Context — AndroidUse

The domain model for AndroidUse: an Android application that lets a **cloud** AI
agent see the phone's screen and carry out multi-step tasks on it, without root.

Terms below are the canonical vocabulary. Use these words in code, in issues, in
commit messages, and in ADRs — do not invent synonyms.

## Agent

The reasoning entity that decides what to do next. In AndroidUse the Agent lives
in the **Relay**, not on the phone. The phone never interprets a goal; it only
executes **Actions** and reports **Observations**.

The three reference projects all keep the Agent loop on the device. AndroidUse
moves it to the server. See [ADR-0001](docs/adr/0001-cloud-agent-relay.md).

## Relay

The server-side component that owns the model credentials, runs the Agent loop,
enforces the **Run Budget**, and brokers **Approval** requests. It is the only
party that speaks to a model provider.

Not to be confused with the "model API" — the Relay is our own code, not the
vendor's.

## Device Agent

The on-device half of AndroidUse: the app's AccessibilityService, screen capture,
gesture and text executors, local policy gate, and the UI that shows the user
what is happening. The Device Agent never decides anything; it obeys.

## Run

One user request carried from submission to completion. A Run has exactly one
**Goal**, a **Run Budget**, an ordered list of **Steps**, and a terminal outcome
(`succeeded` / `failed` / `blocked` / `aborted` / `budget_exhausted`).

## Step

One turn of the Agent loop: send observation, receive one or more **Actions**,
execute them, capture the next observation. Steps are numbered from 1 and are
the unit the **Run Budget** counts.

## Goal

What the user asked for, in the user's own language. The Goal is never
translated into steps by the phone; the Relay owns that decomposition.

## Action

A single instruction the Agent issues to the Device Agent. Actions are the
**only** way the Agent affects the phone. The canonical set is the native
computer-use set: `screenshot`, `click`, `double_click`, `long_press`, `drag`,
`type`, `scroll`, `press_key`, `open_app`, `list_apps`, `wait`, `finish`,
`ask_user`.

See [ADR-0004](docs/adr/0004-native-computer-use-action-set.md).

## Capability

The security-relevant *class* of an Action. Examples: `screen.read`,
`input.tap`, `input.text`, `app.launch`, `navigate.back`, `settings.write`,
`message.send`, `payment.authorize`, `account.change`.

Capability — not package name, not tool name — is what the **Approval** policy
is written against. See [ADR-0003](docs/adr/0003-capability-based-approval.md).

An Action has a **base capability**, fixed by its kind. The capability that
actually governs is the **effective capability**: the device resolves it from
the action *and* where it happens, so that a tap on a "Send" button is
`message.send` rather than `input.tap`. Effective capabilities may only be
*more* restrictive than base ones, never less.

## Approval

A user decision that permits one Action (or a scoped family of Actions) to run.
An Approval is requested by the Agent, surfaced by the Device Agent, decided by
the human, and reported back to the Relay.

Approval scope is one of: `once`, `session`, `always_for_package`.

## Perception

What the Device Agent can see of the screen. AndroidUse has two Perception
channels:

- **Frame** — a screenshot of the real display, produced by MediaProjection.
- **Tree** — the structural view of the foreground app, produced by the
  AccessibilityService node hierarchy.

A **Perception** is the pair sent to the Agent each Step. See
[ADR-0002](docs/adr/0002-mediaprojection-primary-perception.md).

## Grounding

The mapping from something the Agent says ("the blue Send button") to a
concrete place on the device (a pixel coordinate or a node index). Grounding is
where most failures happen, and it is why the Tree channel exists.

## Element Index

The position of a node in the Tree's rendered list, used by the Agent to
address an element without coordinates. Indices are only valid for the
**Perception** that produced them; a new Perception invalidates all of them.

## Screen Fingerprint

A short hash over the salient contents of a Perception (visible text, element
geometry, foreground package), used to answer "did the screen actually change?".
It is how the Device Agent tells a successful Action from a no-op.

## Outcome

The structured result of executing one Action. Outcomes are typed, never prose:
`ok`, `unchanged`, `stale_element`, `denied`, `timeout`, `unsupported`,
`failed`.

The Agent receives the Outcome, not a human-readable message it must
re-interpret. This is deliberate: our reference projects infer status by
matching English words, which is brittle and misfires on content.

## Verification

An explicit check that the task's goal state was reached. Verification is a
distinct Step, not an inference from "the Action returned ok". The Agent
performs it by re-reading the screen; the Device Agent reports the result
structurally.

## Run Budget

The hard ceilings on a Run: maximum Steps, maximum wall-clock duration,
maximum spend, and per-Capability rate limits. The Relay enforces them
authoritatively; the Device Agent enforces a local subset so a malicious or
buggy Relay cannot drive an unbounded session.

See [ADR-0006](docs/adr/0006-run-budgets.md).

## Task

A user-facing unit of work in the UI ("find a flight", "summarise my unread
messages"). A Task becomes a **Goal** when the user submits it. Do not use
"Task" and "Goal" interchangeably.

## Session

The pairing between one phone and the Relay, established by a device token.
A Session survives app restarts and carries the device's identity, its granted
**Capability** policy, and its device preferences.

## Local Policy

The authoritative, on-device rules about which Capabilities may run without
asking. The Relay can *narrow* the Local Policy but never widen it.

## Overlay

The always-on-top status surface the Device Agent draws above other apps. It
shows what the Agent is doing, offers pause/takeover, and renders pending
**Approval** requests. It must be transparent to gesture injection — the
overlay cannot swallow the taps it is describing.

## Tracer Bullet

A vertical slice that exercises the whole system end to end, from user input to
an Action actually executed on the device. Tracer bullets are the unit of
delivery; a ticket is not done until its tracer bullet runs.

## Non-goals

The following are explicitly **not** in AndroidUse's scope, and are named here
so that proposals to add them can be recognised and declined:

- Rooting, or any privileged/root-only mechanism.
- Shizuku and hidden-API input injection. AndroidUse targets a stock device.
- Background execution on a virtual display. The Agent drives the real screen.
- An on-device model. Reasoning is in the cloud by definition.
- General-purpose shell execution on the device.
- An MCP server. AndroidUse speaks its own protocol to its own Relay.
