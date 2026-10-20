# ADR-0004: One `act` tool with a discriminated action payload

- Status: Accepted
- Date: 2026-10-20

## Context

The Agent has to choose what to do next. The reference projects expose that
choice three different ways:

- **ClosePaw** — one `mobile_action` tool with an `action` enum plus flat
  optional parameters (`element_index`, `text`, `x`, `y`, `input_text`,
  `direction`, `start`, `end`, `duration_ms`). Plus a dozen sibling tools
  (`open_app`, `system_button`, `complete_task`, `write_todos`, `scratchpad`,
  `shell`, `termux_shell`, `browser_script`, …).
- **CellClaw** — **34 flat tools** (`app.launch`, `screen.read`,
  `vision.analyze`, `messaging.reply`, `sms.send`, `phone.call`, `camera.snap`,
  `script.exec`, `file.read`, …).
- **android-agent** — 25 tools plus a Lua scripting escape hatch.

A wide tool surface forces the model to make a *tool-selection* decision before
it can make a *parameter* decision. Every extra tool is another chance to pick
the wrong one, and each tool description is tokens in every request. CellClaw's
34 tools are the extreme case; its `file.read`/`file.write`/`script.exec` are
also unrestricted capabilities wearing a tool's clothes.

## Decision

AndroidUse exposes **one** action tool, `act`, whose parameter is a
**discriminated union** on an `action` discriminator:

```jsonc
{
  "action": "click",        // one of the canonical action kinds
  "target": { "x": 412, "y": 1188 },   // or { "element_index": 17 }
  "text": "Hello",         // only for type
  "direction": "down",     // only for scroll
  "duration_ms": 600,      // only for long_press / drag
  "package": "com.x.y"     // only for open_app
}
```

Rules:

1. **One tool, one decision.** The Agent picks *what* to do (the action kind)
   and *where* (target) — it never picks a tool name.
2. **Action kinds are a closed set** shared with the Relay through the
   `:protocol` module, so the two ends cannot drift.
3. **Grounding is a target union**, not a pile of optional parameters:
   either `element_index` (from the Tree) or `x`/`y` (from the Frame). A
   target is always exactly one of the two. This is what stops the
   "ambiguous empty target" failures that plague flat-parameter designs.
4. **Every action declares its Capability** in the sealed hierarchy. The
   mapping is compile-time checked, so a new action kind cannot ship without a
   policy verdict.
5. **Non-device concerns are not actions.** Todos, scratchpad, and memory
   live in the Relay's own prompt scaffolding (as ClosePaw does with its
   working-memory blocks). They are not device tools, so they do not consume
   the tool-selection budget.

## Consequences

**Good**

- The model exercises a protocol it was trained on, which is exactly what
  Anthropic's computer-use and OpenAI's computer tool look like.
- The request shrinks: one tool schema instead of 25-34, which is a
  meaningful token saving on every Step of a long Run.
- The Capability mapping is compiler-enforced.
- The Relay and the phone share one vocabulary, so a protocol mismatch is a
  compile error, not a runtime surprise.

**Bad, and accepted**

- A discriminated union is a slightly awkward thing to serialise, and the
  JSON Schema for it is more verbose than a flat object. We generate the
  schema from the shared Kotlin types so it cannot drift.
- Some things genuinely are different tools conceptually ("list the apps
  installed" is not a "click"). We keep them inside the same `act` tool as
  distinct action kinds rather than as separate tools, which preserves the
  single-decision property.

**Neutral**

- We lose CellClaw's domain tools (`sms.send`, `calendar.create`,
  `contacts.add`). We are deliberately not shipping them in v1: each one is a
  new Capability, a new Play-policy surface, and a new source of abuse. The
  generic `act` surface can open an app and use it like a human, which is
  strictly more capable and much less privileged.

## Alternatives considered

**Flat optional parameters, like ClosePaw's `mobile_action`.** Rejected: the
target union is the whole point; flat optionals make "no target" a valid
state, which is where ambiguity bugs come from.

**34 domain tools, like CellClaw.** Rejected: tool-selection load, token cost,
and a much larger privileged surface.

**Per-action tools (`click`, `type`, `scroll`, …) with one schema each.**
Rejected: same selection problem as 34 tools, and no discriminated-union
typing.

## Related

- [ADR-0003](0003-capability-based-approval.md) — the Capability mapping
