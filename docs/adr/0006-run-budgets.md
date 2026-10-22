# ADR-0006: Every Run is budgeted, and the budget is enforced on both ends

- Status: Accepted
- Date: 2026-10-20

## Context

An agent that can see a screen and press buttons will, given a confusing goal
and a weak model, press buttons forever. Because AndroidUse's Agent is in the
cloud (ADR-0001), that loop is billed to the user by the provider.

None of the reference projects has a guard:

| Project | Step cap | Wall-clock cap | Spend cap |
| --- | --- | --- | --- |
| ClosePaw | **none in production** — `doc/main/agent/loop.md` states there is no hard turn-count cap; the only backstop is 3 consecutive compaction failures | none | none (cost is recorded, not enforced) |
| CellClaw | `maxIterations` default **0 = unlimited** | none | none |
| android-agent | `while (true)` — **no cap at all** | none | usage cost is displayed, never enforced |

This is acceptable when the model key belongs to the user and they are paying
their own provider bill, and it is close to unacceptable when our Relay is
paying a provider on the user's behalf.

## Decision

A **Run Budget** is created when a Run starts and is enforced in two places.

**Relay (authoritative).** The Relay knows the provider's reported usage for
the Run, so it can enforce spend exactly.

| Bound | Default | Rationale |
| --- | --- | --- |
| `max_steps` | 40 | A legitimate multi-step task is 5-15 steps; 40 is generous and stops a loop |
| `max_duration_ms` | 10 min | Long enough for a slow multi-app task, short enough to be a session |
| `max_spend_usd` | $0.50 | Covers ~40 steps of a mid-tier model with headroom |
| `max_cost_per_step_usd` | $0.05 | Catches a single pathological step early |

When any bound is hit, the Relay ends the Run with outcome `budget_exhausted`
and tells the user which bound was reached, in their language.

**Device (defensive subset).** The Device Agent independently enforces a
`max_steps` and a `max_duration_ms` on the actions it will execute in one Run.
It cannot know the spend, so it does not pretend to. The device's limit is
always the tighter of the two, and it refuses an action that would exceed it
with Outcome `denied`.

In addition:

- **Compaction.** When the conversation exceeds the model's context, the Relay
  compacts it, dropping old frames and old tool bodies first. The Relay
  tracks compaction failures and ends the Run after 3 consecutive failures.
- **Loop detection.** The Relay compares consecutive **Screen Sets** (ADR-0009);
  5 consecutive near-identical screens (Jaccard ≥ 0.95) is a stall, and the
  Relay injects a "you appear to be repeating yourself" turn before ending
  the Run. This is a warning, not a strategy change — the Agent decides.
- **Per-Capability rate limit.** The device refuses more than N actions of one
  Capability in a short window, which stops a tap-loop that happens to be
  individually legal.

## Consequences

**Good**

- The cost of a Run is knowable before it starts and capped while it runs.
- A confused Agent is stopped by the system, not only by the user noticing.
- The device still cannot be driven into an unbounded session by a bad Relay.

**Bad, and accepted**

- A legitimate 40-step task can be cut off. The user is told why, and can
  start a follow-up Run that continues from the transcript.
- Spend accounting depends on the provider reporting usage. Providers that do
  not report it fall back to an estimated per-step cost, which is
  conservative but not exact.

**Neutral**

- The budget is part of the protocol, so the phone can display "8 of 40 steps,
  $0.04 of $0.50" while a Run is in flight.

## Alternatives considered

**Trust the Agent to stop itself.** Rejected: this is precisely what all three
references do, and it is the failure mode that costs money.

**Rely on the provider's own rate limits.** Rejected: they bound abuse, not
spend on our account, and they do not stop a legal-but-useless loop.

**Charge per use, like a hosted agent product.** Compatible with this ADR, and
probably where the business model ends up, but it does not replace the caps.

## Related

- [ADR-0009](0009-screen-fingerprint-and-screen-set.md) - the Screen
  Fingerprint and the Screen Set. This ADR's loop detection compares Screen
  Sets; the fingerprint itself answers a different question.

