# ADR-0011: The Provider credential is the user's own API key, held by the Relay

- Status: Accepted
- Date: 2026-10-22
- Context: [docs/research/provider-credentials.md](../research/provider-credentials.md)

## Context

AndroidUse was designed around the Relay holding **its own Provider API key**
and paying the vendor per token. ADR-0001 puts the model credentials on the
server side; ADR-0006 budgets a Run in `max_spend_usd` and
`max_cost_per_step_usd` on the premise that "the Relay knows the provider's
reported usage for the Run, so it can enforce spend exactly"; ADR-0008 keeps
every credential off the phone.

The maintainer's direction was to change that: the app should work by using
**the user's own accounts with AI companies**, the model Manus adopted, rather
than by the company buying metered credits.

The research behind this ADR checked what the vendors actually sanction, and
it corrected the premise in three ways.

**Manus did not ship consumer-subscription access.** On 2026-09-29 Manus
shipped **Manus Flex - bring-your-own-API-key**: the user's own key from a
supported inference provider drives inference inside Manus's own harness, with
OpenRouter, Fireworks and Modal as the first partners. "Model inference is
billed directly by that provider." The transferable precedent is **BYO key
plus a vendor-owned harness**, not BYO subscription. The maintainer's
*direction* survives that correction intact - the user's own credential, the
user's own bill - but the *mechanism* is an API key.

**The consumer-subscription paths are not available to a self-serve hosted
product.** Exactly one of the three major vendors has a documented,
tool-capable third-party path onto a consumer plan, and it is gated:

| Vendor | Position |
| --- | --- |
| OpenAI | "Sign in with ChatGPT" exists and carries tool use, but an open-source or locally-hosted app may use it immediately while a **paid or remotely hosted** app must apply to become a commercial partner |
| Anthropic | claude.ai login is permitted only under a prior commercial agreement; "unless previously approved, Anthropic does not allow third party developers to offer claude.ai login" |
| Google | forbidden by name, in the Gemini CLI and Antigravity terms |

**But a BYO API key is metered normally.** The subscription paths share an
allowance that is per-action invisible, which would have turned ADR-0006's
spend axes into estimates. An API key does not: the provider reports usage
per request, and the Relay reads it. So the budget machinery survives
unchanged - which it would not have on a subscription.

## Decision

**The Provider credential is the user's own API key**, for a provider the user
chooses. The Relay holds it, calls the provider with it, and the provider
bills the user directly.

- The Relay **sells no model inference**. It sells the agent loop, the device
  bridge, the budget and approval machinery, and the transcript. This is
  Manus's own split: the inference leg moves to the user's key, and the
  harness stays the product.
- The Relay holds the credential **in the user's name**, isolated per user,
  never logged, deletable on request.
- A user with no provider key cannot run a Run. Whether the Relay also sells
  model credits for such a user is a product decision, and this ADR does not
  make it.
- The **consumer-subscription** mechanisms are not the mechanism. The product
  must not depend on a commercial partnership it cannot obtain, and the terms
  of two of the three vendors forbid the route outright.

### ADR-0001 and ADR-0006 survive unchanged

- **ADR-0001**'s table says AndroidUse's model credentials "never leave the
  server". Still true - and now the credential is the user's rather than the
  company's, which strengthens the line rather than weakening it.
- **ADR-0001**'s "spend is bounded by a server that can see provider usage"
  holds exactly, because API-key usage is metered per request.
- **ADR-0006**'s `max_spend_usd` and `max_cost_per_step_usd` keep their
  meaning, and `max_cost_per_step_usd` keeps catching a single pathological
  step early. They would have become estimates on a subscription, and
  estimates are not enforceable.
- **ADR-0004**'s `act` tool and its hand-written JSON schema keep their
  contract: both sanctioned tool-capable paths - OpenAI's function and custom
  tools, Anthropic's Claude Code and Agent SDK - expose tool use, and the
  research found no sanctioned path without it.

### What this opens up

ADR-0001 gave the cloud Relay a reason: the company's model key had to stay
off the phone. With the credential being the **user's**, the company holds no
key of its own, and the case for a *hosted* Relay weakens - a Relay on the
user's own machine becomes possible.

That is the spec's open decision **D2** ("whether the Relay is open source
and self-hostable, or a hosted service"), and it was unowned. It is now the
pivotal question, and it is a separate decision: this ADR settles **whose
credential** and **which mechanism**, not **where the Relay runs**.

## Consequences

**Good**

- The company has **no model bill**, and its revenue no longer scales with
  model usage. A Run that loops costs the user their own provider credits, in
  a dashboard they can watch.
- The budget machinery works as designed. `max_spend_usd` is enforced against
  real usage rather than an estimate, which is what ADR-0006 always assumed.
- The vendor is the **user's** choice, and adding a second provider is the
  user's business, not a procurement cycle.
- The product can ship without waiting for a commercial agreement with
  anyone. The paths that need one are not on the critical path.
- The action model is untouched. The `act` tool's tool-use contract exists on
  the paths that are actually available.

**Bad, and accepted**

- **The Relay becomes a custodian of third-party API keys.** One per user,
  held server-side, in a multi-tenant service. Encryption at rest, per-user
  isolation, key rotation, deletion on request, and an iron rule that a key
  never reaches a log, a trace or a crash report. This is the largest
  operational surface the project acquires, and it is larger than the model
  bill it replaces.
- The Relay's service-level promise changes shape. It is no longer "we pay
  the model and sell you the outcome"; it is "we run your agent loop and
  spend your credits for you, and we will stop when you say stop".
- The user's spend is the user's problem in a way that needs saying out loud
  in the UI, because a runaway loop is a bill. ADR-0006's step and duration
  caps are the mitigation, and they are the reason the caps exist.
- The research could not establish a working tool-capable reverse-engineered
  consumer endpoint, and 2026 enforcement appears to have closed the Claude
  web path. So there is no fallback route if the sanctioned paths change.

**Neutral**

- Which provider the user picks is a procurement decision, and it stays one.
- A user needs a provider account and a key. That is one more onboarding step
  before the first Run, and it is the step that makes the product free to run
  for the company.

## Alternatives considered

**The consumer subscription via OAuth.** Rejected: OpenAI's path is
partner-gated for a paid or remotely hosted app, Anthropic's needs prior
approval, and Google's is forbidden by name. On top of that, a subscription
allowance is per-action invisible, so ADR-0006's spend axes would have had to
become estimates against a shared, unpredictable allowance - and the research
found that 40 steps in 10 minutes is not rate-limited anywhere, so the only
real constraint would have been the user's own shared quota, discovered
afterwards.

**Anthropic's claude.ai login.** Rejected: a commercial agreement, not a
signup. It is a partnership to negotiate, not a feature to ship, and the
product must not depend on it.

**Google's path.** Rejected: forbidden by name, in two of its own terms.

**Reverse-engineered consumer web endpoints.** Rejected: no guaranteed
tool-use contract, so ADR-0004's action model would not survive them; brittle
enough that a vendor's enforcement change breaks the product; and against the
vendors' terms.

**The company keeps buying API credits and reselling them.** Rejected: it is
the model this decision moves away from, and it puts the model bill back on
the company's books. It remains the obvious fallback if a user will not
supply a key, and the decision of whether to offer it is not made here.

## Related

- [ADR-0001](0001-cloud-agent-relay.md) - the Relay, the trust boundary, and
  the model credentials that "never leave the server".
- [ADR-0004](0004-native-computer-use-action-set.md) - the `act` tool and
  the tool-use contract this decision preserves.
- [ADR-0006](0006-run-budgets.md) - the spend axes, which survive unchanged.
- [ADR-0008](0008-no-shell-no-unrestricted-file-io.md) - no credential on the
  phone.
- [docs/research/provider-credentials.md](../research/provider-credentials.md)
  - the facts, with sources and dates.
