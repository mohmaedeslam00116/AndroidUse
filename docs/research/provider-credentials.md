# Which providers sanction third-party use of a consumer subscription, and what does Manus actually do?

Research ticket: [#40](https://github.com/mohmaedeslam00116/AndroidUse/issues/40).
Date: 2026-10-22. Every source below was retrieved on 2026-10-22; where a source
carries its own publication or "last updated" date, that date is given too.

This note gathers facts. It does not decide. The decision is
[#39](https://github.com/mohmaedeslam00116/AndroidUse/issues/39) ("Does the Relay
hold a Provider API key, or the user's own account?"), and this file is an input
to it.

## What this note is about

AndroidUse's current design has the Relay holding a **Provider API key** and
calling a vendor's API directly, paying per token
(`CONTEXT.md`, "Provider"; `docs/adr/0008-no-shell-no-unrestricted-file-io.md:41-44`,
"No model credentials on the device"; `docs/adr/0006-run-budgets.md:7-10` and
`28-36`, where `max_spend_usd` and `max_cost_per_step_usd` exist on the premise
that "the Relay knows the provider's reported usage for the Run, so it can enforce
spend exactly").

The maintainer now wants to consider the alternative: the app runs on the **user's
own existing consumer accounts** with AI companies. That alternative is only
available if a provider **sanctions** it, and the whole action model depends on
the provider exposing a **tool-use contract** — AndroidUse's entire effect on the
device is one `act` function with a hand-written JSON schema
(`protocol/src/main/kotlin/ai/androiduse/protocol/ActionSchema.kt:20-91`,
`docs/adr/0004-native-computer-use-action-set.md`).

**Answer in one line.** Exactly one of the three major vendors has a documented,
tool-capable, third-party path onto a consumer subscription today, and it is
**OpenAI** — but it is gated: an open-source or locally-hosted app can use it
immediately, while a **paid or remotely hosted** app like AndroidUse's Relay must
apply to become a commercial partner
([developer docs](https://developers.openai.com/siwc/token-sharing-open-source),
2026-10-22); **Anthropic** permits it only under a prior commercial agreement
("Unless previously approved, Anthropic does not allow third party developers to
offer claude.ai login or rate limits for their products",
[Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview), 2026-10-22);
and **Google** forbids it in terms, by name
([Gemini CLI ToS](https://geminicli.com/docs/resources/tos-privacy/), last updated
2026-04-10; [Antigravity ToS](https://antigravity.google/terms/), 2026-10-22).
And the premise itself is off: **Manus did not ship consumer-subscription
access.** It shipped **Manus Flex, bring-your-own-API-key**, on 2026-09-29, with
OpenRouter, Fireworks and Modal as its initial inference partners
([Manus](https://manus.im/blog/introducing-manus-flex), 2026-09-29).

---

## 1. What Manus actually shipped

### 1.1 The mechanics

On **Tuesday 29 September 2026** Manus published "Introducing Manus Flex: Use
your own API key in the Manus workspace"
([manus.im/blog/introducing-manus-flex](https://manus.im/blog/introducing-manus-flex),
2026-09-29). The primary source says, in full:

> "Manus is launching Manus Flex, a new module that lets users power Manus with
> **your own API key** from a supported inference provider."
>
> "With Flex, users can bring an existing provider relationship into Manus. Their
> **API key** connects provider inference to the same projects, tools, execution
> environments, and agent workflows they already use."
>
> "Manus continues to provide the agent system that plans the work, uses tools,
> operates across execution environments, and turns model output into completed
> tasks. Flex configuration includes a model and a reasoning-effort setting for
> the connected provider. **Model inference is billed directly by that provider.**
> Other services and infrastructure used as part of a Manus task still consume
> Manus credits."
>
> "We are excited to announce **OpenRouter, Fireworks, and Modal** as our initial
> inference partners for Manus Flex."
>
> "Connect a supported inference provider, configure its primary model and effort
> level, then use your existing provider account in the projects, automations,
> and agent workflows you are already building."

Manus's own product feed said the same in one line: "Bring your own API key to
Manus." ([@ManusAI](https://x.com/ManusAI/status/2105085387391533430), cited by
[Releasebot](https://releasebot.io/updates/manus), 2026-10-22).

### 1.2 What that means for the premise

**Manus did not adopt a consumer subscription.** It adopted a **bring-your-own-API-key**
model, and the three named partners (OpenRouter, Fireworks, Modal) are inference
**aggregators and hosts**, not consumer-subscription vendors. On this path:

- The user still buys **metered API credits**. "Model inference is billed directly
  by that provider" — there is no flat-rate subscription entitlement, no
  "connect your ChatGPT plan" permission screen, no OAuth against a consumer
  account.
- **Only the inference leg moves to the user's own key.** "Other services and
  infrastructure used as part of a Manus task still consume Manus credits" — so
  Manus still sells credits; it just stops paying the model's bill.
- The **harness is the product**. "Manus continues to provide the agent system
  that plans the work, uses tools, operates across execution environments." That
  is the part of Manus's model that transfers to AndroidUse: the agent loop and
  tool-calling layer sit above a provider you choose, and the provider choice is
  made by the **end user**, not by Manus.

**So the premise the maintainer quoted is materially different from what Manus
shipped.** "Use the user's own account" is what Manus shipped; "use the user's own
*subscription*" is not, at least not in the primary announcement. The nearest
Manus feature to the subscription idea is the separate **"My Computer"** desktop
agent (announced March 2026; [manus.im/blog/manus-my-computer-desktop](https://manus.im/blog/manus-my-computer-desktop),
reported by [CNBC 2026-03-18](https://www.cnbc.com/2026/03/18/metas-manus-launches-desktop-app-to-bring-its-ai-agent-onto-personal-devices.html)),
which is a *local-execution* feature, not a *credential* feature.

### 1.3 Is there a Manus consumer-subscription path at all?

**Not established.** The Flex announcement names API-key partners only, and
Manus's model catalogue page lists media models (video/image/audio/3D) rather
than LLM credential modes ([manus.im/models](https://manus.im/models), 2026-10-22).
What would establish it: a Manus release note or help-centre article naming a
consumer-subscription login. The Manus help centre's "Manus 2.0" collection
contains two articles, neither about credentials
([help.manus.im](https://help.manus.im/en/collections/19763651-manus-2-0),
2026-10-22). Note the naming collision: the community project
**manus-codex-bridge** is *not* a Manus product and does not use the Codex
backend — it uses OpenAI's official OAuth and Responses API
([glama.ai listing](https://glama.ai/mcp/servers/zhiqiang73-cpu/Manus-codex-bridge),
2026-10-22). Do not read it as evidence of a Manus feature.

---

## 2. Comparison table

"Consumer subscription" means a flat-rate personal plan (Claude Pro/Max, ChatGPT
Plus/Pro, Google AI Pro/Ultra), as opposed to a metered API key.

| Vendor | Official third-party path onto a **consumer subscription** | Tool use / function calling on that path | Per-token **cost** signal to the caller | Terms position on third-party use | Rate / quota behaviour |
| --- | --- | --- | --- | --- | --- |
| **OpenAI** (ChatGPT Plus/Pro) | **Yes — "Sign in with ChatGPT" with optional ChatGPT plan usage.** Public docs cover open-source and locally-hosted apps ([siwc](https://developers.openai.com/siwc), 2026-10-22). A **paid or remotely hosted** app must complete an interest form and join a limited set of commercial partners ([request-a-client-ID](https://developers.openai.com/siwc/request-client-id), 2026-10-22; [help.openai.com/en/articles/20001542](https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites), updated 2026-10-22). | **Yes.** "Supported tools: Group function/custom tools in namespaces or supply them through `additional_tools` input items" ([preview-limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations), 2026-10-22). Native `computer use` and hosted MCP/connectors are *not* supported on this route — irrelevant, because AndroidUse supplies its own `act` tool. | **Token counts yes; dollars no.** The Responses API returns `usage: {input_tokens, input_tokens_details, output_tokens, …}` ([API reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create), 2026-10-22). OpenAI states plainly: "**API token prices are separate from subscription usage; don't use them to estimate included tasks**" ([codex/pricing](https://developers.openai.com/codex/pricing), 2026-10-22). | Permitted **only** via the partner programme. Terms of Use (2026-01-01) bar "Automatically or programmatically extract data or Output" and "circumvent any rate limits or restrictions" ([openai.com/policies/terms-of-use](https://openai.com/policies/terms-of-use/), 2026-01-01), but Sign in with ChatGPT is the vendor-sanctioned exception, so an approved app is not "extracting". | Plus: five-hour limit **shared across all apps** using the plan, plus weekly limits; **no separate allowance per app**; the user caps each app at a percentage of their weekly usage ([profiles-and-sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions), 2026-10-22). Estimated local messages per five-hour period on Plus: GPT-6.1 Sol 15–160, GPT-6 Sol 15–150, GPT-6 Luna 350–3000, GPT-6 Astra 5–45; **Pro has no five-hour limit** ([codex/pricing](https://developers.openai.com/codex/pricing), 2026-10-22). Access token 1 h, refresh token 30 d rolling ([token-reference](https://developers.openai.com/siwc/token-sharing-open-source/token-reference), 2026-10-22). |
| **Anthropic** (Claude Pro/Max) | **Conditionally.** Two routes: (a) host the **unmodified Claude Code binary** in your product, under Anthropic's Commercial ToS, with each end user authenticating with their own subscription credential and with **no** intermediating of usage ([legal-and-compliance](https://code.claude.com/docs/en/legal-and-compliance), 2026-10-22); (b) use the Claude Agent SDK — but "**Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK**" ([agent-sdk/overview](https://code.claude.com/docs/en/agent-sdk/overview), 2026-10-22). | **Yes.** Claude Code and the Agent SDK have a full tool layer; custom tools are reachable through MCP ([agent-sdk/overview](https://code.claude.com/docs/en/agent-sdk/overview), 2026-10-22). | **Token counts yes; dollars no.** The Messages API returns `usage.input_tokens` / `output_tokens` (and cache fields when prompt caching is on) ([platform.claude.com/docs/en/api/overview](https://platform.claude.com/docs/en/api/overview), 2026-10-22; corroborated by [NVIDIA AIPerf's Anthropic guide](https://docs.nvidia.com/aiperf/tutorials/model-endpoint-guides/profile-the-anthropic-messages-api-with-ai-perf), 2026-10-22). Subscription usage carries no per-token price. | "Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests through Free, Pro, or Max plan credentials on behalf of their users. Moreover, developers may not collect, store, or intermediate Claude.ai credentials or session tokens — sign-in to a Claude account must complete through Anthropic's own flow." ([legal-and-compliance](https://code.claude.com/docs/en/legal-and-compliance), 2026-10-22). Anthropic "reserves the right to take measures to enforce these restrictions and may do so without prior notice." Consumer ToS §3.7: "Except when you are accessing our Services via an Anthropic API Key **or where we otherwise explicitly permit it**, to access the Services through automated or non-human means, whether through a bot, script, or otherwise" ([consumer-terms](https://www.anthropic.com/legal/consumer-terms), effective 2025-10-08). | Pro/Max have a **five-hour session limit plus a weekly limit**, "shared across Claude and Claude Code, meaning all activity in both tools counts against the same limits"; no numeric token or message allowance is published in the help centre ([support 11145838](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan), updated ~2026-10-15; [support 11647753](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work), updated ~2026-10-15). Five-hour limits were **doubled** and peak-hour reductions **removed** on 2026-05-06 ([anthropic.com/news/higher-limits-spacex](https://www.anthropic.com/news/higher-limits-spacex), 2026-05-06). `claude setup-token` mints a **one-year** OAuth token for headless use ([authentication](https://code.claude.com/docs/en/authentication), 2026-10-22). |
| **Google** (Google AI Pro/Ultra) | **No sanctioned path.** Gemini CLI / Antigravity OAuth is for those products only; the sanctioned route for a third-party agent is "a Vertex AI or Google AI Studio API key" ([Gemini CLI FAQ](https://geminicli.com/docs/resources/faq/), last updated 2026-04-10; [Antigravity FAQ](https://antigravity.google/docs/faq/), 2026-10-22). | n/a on a consumer path. The Gemini CLI itself has function calling, but Google forbids third parties from using its OAuth to reach it. | The Gemini CLI exposes **total token usage** via its `/stats` command even for OAuth users — but **cached-token counts are API-key users only**, "because the Gemini Code Assist API does not support cached content creation" ([Gemini CLI FAQ](https://geminicli.com/docs/resources/faq/), 2026-04-10). No dollar signal. | **Explicitly forbidden, by name.** "Directly accessing the services powering Gemini CLI (for example, the Gemini Code Assist service) using third-party software, tools, or services (for example, using OpenClaw with Gemini CLI OAuth) is a violation of applicable terms and policies. Such actions may be grounds for suspension or termination of your account." ([tos-privacy](https://geminicli.com/docs/resources/tos-privacy/), 2026-04-10). Antigravity ToS §6: "Using third party software, tools, or services to access the Service (e.g. using OpenClaw with Antigravity OAuth) is a breach of this Agreement. Such actions may be grounds for suspension or termination of your Antigravity and/or Gemini CLI accounts." ([antigravity.google/terms](https://antigravity.google/terms/), 2026-10-22). Antigravity FAQ also rules out the headless wrapper: "Wrapping `agy` inside third-party coding agents or applications, or automating account rotation, is not supported under consumer plans" ([faq](https://antigravity.google/docs/faq/), 2026-10-22). | Daily request caps, shared across Gemini CLI and agent mode: **1 000/day** (Gemini Code Assist individual, free), **1 500/day** (Google AI Pro; Code Assist Standard), **2 000/day** (Google AI Ultra; Enterprise) ([quota-and-pricing](https://geminicli.com/docs/resources/quota-and-pricing/), 2026-10-22; [Google Cloud quotas](https://docs.cloud.google.com/gemini/docs/quotas), last updated 2026-10-20). Per-minute limits also apply but are not numerically published. Over-quota yields `429 — Resource exhausted` ([Gemini CLI FAQ](https://geminicli.com/docs/resources/faq/), 2026-04-10). |
| **xAI / Grok (SuperGrok)** | **Not established.** Warp documents a "SuperGrok subscription" connection for Grok models ([docs.warp.dev](https://docs.warp.dev/agents/inference/bring-your-own-api-key/), 2026-10-22), which suggests a sanctioned path exists, but xAI's own terms and OAuth documentation were not located in this research pass. | **Not established.** | **Not established.** | **Not established.** | **Not established.** |
| **Others** (Mistral Le Chat, DeepSeek, Qwen, Moonshot/Kimi) | **Not established.** No consumer-subscription third-party OAuth path was found for any of them in this pass. Their relevant paths are metered API keys, like Manus Flex's. | — | — | — | — |

---

## 3. The sanctioned paths, in detail

### 3.1 OpenAI — the only one that is documented and tool-capable

**What it is.** "Let users sign in with ChatGPT and use their ChatGPT plan for
eligible AI requests in your app" ([siwc](https://developers.openai.com/siwc),
2026-10-22). The flow is ordinary OAuth 2.0 with PKCE against
`https://auth.openai.com/api/accounts/authorize`, plus three extra scopes
(`offline_access resource.invoke chatgpt.tokens.use.direct`) and a host
identifier (`ext_agent_host_id`) that lets OpenAI attribute plan usage to the
machine the tool runs on ([sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in),
2026-10-22). Inference goes to the **public** Responses API,
`POST https://api.openai.com/v1/responses` with the OAuth token as a bearer —
OpenAI says explicitly "do not point it at ChatGPT's `backend-api` endpoints"
([models-and-inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference),
2026-10-22).

**Why it carries AndroidUse's `act` tool.** From
[preview-limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)
(2026-10-22):

> "**Supported tools:** Group function/custom tools in namespaces or supply them
> through `additional_tools` input items."

So a hand-written function schema like `ActionSchema.toolSchema()` is
expressible. The **unsupported** list — image generation, file search, Code
Interpreter, native computer use, hosted MCP/connectors, `tool_search` — contains
nothing AndroidUse needs, because AndroidUse implements its own action surface
rather than asking the provider for a computer-use tool.

**Constraints that will bite an Android app.**

- `store: false` and `stream: true` are **required** on every inference request
  ([models-and-inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference),
  2026-10-22).
- `previous_response_id` must be **omitted over HTTP**; the required history goes
  in `input` ([preview-limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations),
  2026-10-22). The Relay must therefore resend (or compact) the transcript on
  every step, which is what ADR-0006 already plans.
- The OAuth `redirect_uri` must be an **HTTP loopback on `127.0.0.1`**, and only
  the port may vary: "Do not substitute with `localhost`"
  ([sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in),
  2026-10-22). An Android app cannot host that callback; a **Relay-side** loopback
  listener can. This is an argument for keeping the OAuth on the Relay, which is
  where AndroidUse already keeps provider access.
- Access tokens live **1 hour**; refresh tokens **30 days**, replaced on each
  refresh ([token-reference](https://developers.openai.com/siwc/token-sharing-open-source/token-reference),
  2026-10-22).

**The gate.** "Sign in with ChatGPT is currently offered to a **select group of
commercial partners**. To join the waitlist, complete the Sign in with ChatGPT
interest form" ([request-client-id](https://developers.openai.com/siwc/request-client-id),
2026-10-22). And from the token-sharing overview: "These docs explain ChatGPT
plan usage for **open-source and locally hosted apps**. If you're interested in
offering it in a **paid or remotely hosted app**, complete the interest form"
([token-sharing-open-source](https://developers.openai.com/siwc/token-sharing-open-source),
2026-10-22). AndroidUse's Relay is a remotely hosted, paid service. So the path
is real but **not self-serve** for AndroidUse.

**The partner list is a live, curated directory** and shows what OpenAI considers
in-scope ([learn.chatgpt.com/docs/sign-in-with-chatgpt](https://learn.chatgpt.com/docs/sign-in-with-chatgpt),
2026-10-22):

- *Apps with ChatGPT plan usage:* Amp Code, Conductor, Dactyl, Devin, Hermes
  Agent, Hyperagent, Kilo Code, Lovable (coming soon), Notion, Vercel, Vorflux,
  Warp.
- *Apps with sign-in only:* Airtable, Canva, GitLab, HubSpot, Supabase.
- *Open-source integrations:* OpenClaw, OpenCode, Pi, T3.

Every one of the listed plan-usage apps is a **developer tool that runs on the
user's own machine**. None is a hosted agent service.

### 3.2 Anthropic — sanctioned, but only by arrangement

**The prohibition and the exception.** The Claude Code legal page is the
authoritative statement ([legal-and-compliance](https://code.claude.com/docs/en/legal-and-compliance),
2026-10-22):

> "**Developers** building products or services that interact with Claude's
> capabilities, including those using the Agent SDK, should use API key
> authentication through Claude Console or a supported cloud provider. Anthropic
> does not permit third-party developers to offer Claude.ai login into their own
> applications, or to route requests through Free, Pro, or Max plan credentials on
> behalf of their users. Moreover, developers may not collect, store, or
> intermediate Claude.ai credentials or session tokens — sign-in to a Claude
> account must complete through Anthropic's own flow."

**But the same page sanctions one specific shape** — the *unmodified Claude Code
binary hosted by you*:

> "Unless we've mutually agreed otherwise, preinstalling or running Claude Code
> in your products or services (e.g. in hosted sandboxes or other agent
> infrastructure) requires **agreeing to our Commercial Terms of Service** and
> complying with the conditions below:
>
> - **The Claude Code binary must not be modified.** …
> - **Customers may not pay for, resell, or intermediate Claude usage on their end
>   users' behalf.** Each end user must authenticate with their own Anthropic API
>   key, Claude subscription plan credentials, or 3P inference provider credential
>   … That usage is billed directly to the end user under their own agreement with
>   Anthropic."

That is, structurally, **the model AndroidUse's maintainer described**: the user's
own subscription credential, billed to the user, with the company not
intermediating the spend. The price is a **commercial agreement with Anthropic**
and an **unmodified binary** — which conflicts with ADR-0004's requirement for a
hand-written `act` tool unless the tool is exposed through Claude Code's MCP
surface.

**Two operational facts a hosted relay must handle.**

1. `claude setup-token` mints a **one-year** OAuth token that "authenticates with
   your Claude subscription and requires a Pro, Max, Team, or Enterprise plan" and
   "can only make model requests" ([authentication](https://code.claude.com/docs/en/authentication),
   2026-10-22). This is the credential shape a Relay would need to hold, and it
   is long-lived enough to be operationally workable.
2. **Authentication precedence** puts `CLAUDE_CODE_OAUTH_TOKEN` (rank 5) *below*
   `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_API_KEY` (ranks 2 and 3) — so a stale
   `ANTHROPIC_API_KEY` in the environment silently converts a subscription-backed
   run into a metered one ([authentication](https://code.claude.com/docs/en/authentication),
   2026-10-22). For a hosted relay this is a real footgun.

**Consumer Terms §3.7** is the clause that governs unattended use
([consumer-terms](https://www.anthropic.com/legal/consumer-terms), effective
2025-10-08, retrieved 2026-10-22):

> "Except when you are accessing our Services via an Anthropic API Key or where we
> otherwise explicitly permit it, to access the Services through automated or
> non-human means, whether through a bot, script, or otherwise."

Note the "or where we otherwise explicitly permit it" clause: the prohibition is
not absolute, and it is Anthropic's permission, not the user's consent, that
opens the door.

**A note on the 2026 policy churn.** Anthropic's position moved several times
during 2026. A February 2026 docs revision carried a blanket sentence — "Using
OAuth tokens obtained through Claude Free, Pro, or Max accounts in any other
product, tool, or service, including the Agent SDK, is not permitted and
constitutes a violation of the Consumer Terms of Service" — which was widely
reported at the time ([WinBuzzer, 2026-02-19](https://winbuzzer.com/2026/02/19/anthropic-bans-claude-subscription-oauth-in-third-party-apps-xcxwbn/)),
then characterised as a botched docs edit rather than a policy change
([Hacker News discussion, 2026-02](https://news.ycombinator.com/item?id=47069488)).
Separately, a **June 15, 2026** announcement of a separate metered Agent SDK
credit pool was paused within roughly 24 hours
([beam.ai summary](https://beam.ai/agentic-insights/anthropics-new-billing-split-reveals-what-ai-agents-actually-cost);
[Hermes Agent issue #47260](https://github.com/NousResearch/hermes-agent/issues/47260));
the June 16 email said Agent SDK / `claude -p` / third-party Agent SDK usage
"continues to work with your subscription exactly as it did before". **These are
secondary sources; I did not locate a first-party Anthropic announcement page for
either event.** What *is* first-party is the text quoted above, as it stands on
2026-10-22. Treat the churn as a risk signal, not as a settled rule.

### 3.3 Google — no sanctioned consumer path, and the consumer product moved

**The rule.** Gemini CLI's own terms page, in the second paragraph:

> "Directly accessing the services powering Gemini CLI (for example, the Gemini
> Code Assist service) using third-party software, tools, or services (for
> example, using OpenClaw with Gemini CLI OAuth) is a violation of applicable terms
> and policies. Such actions may be grounds for suspension or termination of your
> account."
> ([tos-privacy](https://geminicli.com/docs/resources/tos-privacy/), last updated
> 2026-04-10)

The FAQ is blunter:

> "Using third-party software, tools, or services to harvest or piggyback on Gemini
> CLI's OAuth authentication to access our backend services is a direct violation of
> our applicable terms and policies. … If you would like to use a third-party
> coding agent with Gemini, the supported and secure method is to use a Vertex AI
> or Google AI Studio API key."
> ([faq](https://geminicli.com/docs/resources/faq/), 2026-04-10)

**The product moved.** "On June 18, 2026, Gemini CLI and Gemini Code Assist IDE
extensions will stop serving requests for Google AI Pro and Ultra, as well as
those using it free of charge using Gemini Code Assist for individuals"
([developers.googleblog.com, 2026-05-19](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli)).
Google AI Pro/Ultra users now get their agentic quota through **Antigravity CLI**,
and the Antigravity terms carry the same prohibition, naming the same example
([antigravity.google/terms](https://antigravity.google/terms/), 2026-10-22), plus
an explicit ruling against the headless-wrapper pattern AndroidUse would need
([Antigravity FAQ](https://antigravity.google/docs/faq/), 2026-10-22). There are
documented enforcement cases — accounts suspended for third-party OAuth use, with
appeals failing ([gemini-cli discussion #20632](https://github.com/google-gemini/gemini-cli/discussions/20632),
2026-05 to 2026-06; [Google support thread](https://support.google.com/gemini/thread/413116187/gemini-cli-got-disabled),
2026).

**Google is out** for this design, on the vendor's own words.

---

## 4. The unofficial path

The unofficial path is: take the user's **session cookie or a credential file**
and call the consumer web app's private API, bypassing the OAuth grant and the
partner programme entirely.

| Vendor | Does it exist? | Is it widely used? | Tool use? | Vendor's terms say |
| --- | --- | --- | --- | --- |
| **OpenAI** | **Yes.** `https://chatgpt.com/backend-api/codex/responses` is the Codex backend, reached with the OAuth access token from `~/.codex/auth.json`. Also `https://chatgpt.com/backend-api/codex/models`, `.../backend-api/wham/usage`, `.../backend-api/transcribe`. | **Yes** — many independent implementations: the `openai-codex-oauth` npm package, `arthjean/pyxis`, `codex-as-api`, `rotom`, `better-ccflare`, `CLIProxyAPI`/`RelayAPI` ([jsDelivr package page](https://www.jsdelivr.com/package/npm/openai-codex-oauth), [pyxis](https://github.com/arthjean/pyxis), [codex-as-api on PyPI](https://libraries.io/pypi/codex-as-api), 2026-10-22). | **Yes** — the Codex backend is the Responses API with function/custom tools, which is why it is attractive as an `act`-carrier. | **Forbidden.** OpenAI's Terms of Use (2026-01-01) bar reverse engineering, "Automatically or programmatically extract data or Output", and "circumvent any rate limits or restrictions or bypass any protective measures" ([terms-of-use](https://openai.com/policies/terms-of-use/)). The SIWC docs exist precisely to point people at the supported route instead of this one. Enforcement and breakage are routine: the OSS bridge's own README warns that `chatgpt.com/backend-api/codex/*` "may change without notice" ([glama listing](https://glama.ai/mcp/servers/zhiqiang73-cpu/Manus-codex-bridge), 2026-10-22). |
| **Anthropic** | **Partly.** The `claude setup-token` credential is *sanctioned* (see §3.2); what exists unsanctioned is the practice of third-party harnesses replaying the Claude Code CLI's transcript JSONL to recover usage and tool events — a technique discussed openly in the community ([paseo issue #1029, 2026-06-15 to 2026-06-20](https://github.com/getpaseo/paseo/issues/1029); [claudefa.st guide](https://claudefa.st/blog/guide/development/claude-code-subscription), 2026). | **Yes** for the CLI-transcript technique. | **Yes** (tool events are recovered from the transcript). | **Forbidden.** Consumer ToS §3.7 covers "automated or non-human means"; §3.3 forbids reverse engineering; §2 forbids sharing account credentials; the legal page forbids collecting or intermediating Claude.ai credentials ([consumer-terms](https://www.anthropic.com/legal/consumer-terms), 2025-10-08; [legal-and-compliance](https://code.claude.com/docs/en/legal-and-compliance), 2026-10-22). Anthropic enforced hard in April 2026, blocking third-party harnesses from Max OAuth ([WinBuzzer, 2026-01-10](https://winbuzzer.com/2026/01/10/claude-code-anthropic-blocks-unauthorized-claude-harnesses-and-xai-access-in-major-crackdown-xcxwbn/); [decodethefuture summary](https://decodethefuture.org/en/anthropic-blocks-third-party-tools/), 2026-04). |
| **Google** | **Yes**, and in the worst way. The pattern is to harvest a `AIza…` Google AI Studio API key out of the Gemini web app / an installed app's resources and call `generativelanguage.googleapis.com` with it. This key is an *account-scoped* key used by the web app itself, so usage lands on the user's account and can trigger bans. | **Yes** — the ban wave is itself the evidence of wide use ([gemini-cli discussion #22970, 2026-04-30 to 2026-05-01](https://github.com/google-gemini/gemini-cli/discussions/22970); [discuss.ai.google.dev thread](https://discuss.ai.google.dev/t/urgent-mass-403-tos-bans-on-gemini-api-antigravity-for-open-source-cli-users-paid-tier/124508), 2026). | **Yes** — the Gemini API supports function calling. | **Forbidden, and enforced.** The Gemini CLI / Antigravity ToS ban third-party access to the OAuth-backed services, and Google documents mass `403` ToS suspensions of AI Pro subscribers triggered by third-party wrappers ([Gemini CLI FAQ](https://geminicli.com/docs/resources/faq/), 2026-04-10; [Antigravity ToS](https://antigravity.google/terms/), 2026-10-22). A Google AI Studio **API key** used in a third-party tool is a different question from harvesting a web-app key — Google permits using your own API key in third-party tools, but the harvesting pattern is what triggers bans. |

**The general shape of the risk.** Every unofficial path in this space depends on
a private endpoint that "may change without notice", on a credential that the
vendor can revoke at will, and on an account that the vendor can terminate
without notice. Anthropic explicitly reserves the right to enforce "without prior
notice" ([legal-and-compliance](https://code.claude.com/docs/en/legal-and-compliance),
2026-10-22). For AndroidUse, that risk lands on **the user's own account** —
the failure mode is "the user's ChatGPT Plus or Claude Max gets banned", not
"the company's API bill spikes". The blast radius is the user's, not the
company's.

---

## 5. Consequences for a looping agent

ADR-0006 budgets a Run at **`max_steps` 40** and **`max_duration_ms` 10 minutes**
(`docs/adr/0006-run-budgets.md:31-36`). That is **one model call every 15
seconds, 40 calls, sustained**. Against the documented limits:

### 5.1 Burst rate is not the constraint

No vendor publishes a per-minute consumer limit low enough to bite at 4 calls
per minute. Google publishes only "requests are limited per user per minute"
without a number ([Google Cloud quotas](https://docs.cloud.google.com/gemini/docs/quotas),
2026-10-20); the Cloud API limit of 2 requests/second is an order of magnitude
above what AndroidUse needs (same page). Anthropic's published API rate limits
are far higher still ([platform.claude.com/docs/en/api/rate-limits](https://platform.claude.com/docs/en/api/rate-limits),
2026-10-22). **A 40-step Run is not rate-limited on any of these paths.**

### 5.2 The allowance is the constraint, and it is not the company's money

Every provider's consumer allowance is **a shared pool**, not a per-app one:

- OpenAI: "For ChatGPT Plus users, the five-hour usage limit is shared across
  all apps where they use their ChatGPT plan, including private and open-source
  clients. Usage in one app contributes to the same five-hour usage total, and no
  app receives a separate allowance" ([profiles-and-sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions),
  2026-10-22). The user can cap AndroidUse at a percentage of their weekly usage
  in ChatGPT Settings, and that cap "is a cap, not a separate pool" — the app can
  hit its cap while the plan still has usage left
  ([help.openai.com/en/articles/20001542](https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites),
  2026-10-22).
- Anthropic: the five-hour session limit and the weekly limit are "shared across
  Claude and Claude Code, meaning all activity in both tools counts against the
  same limits" ([support 11145838](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan),
  ~2026-10-15).
- Google: daily caps are per user per day, aggregated across Gemini CLI and
  agent mode and across model families ([Google Cloud quotas](https://docs.cloud.google.com/gemini/docs/quotas),
  2026-10-20).

So the honest statement of the risk is not "the agent might get rate-limited".
It is **"the agent spends the user's shared weekly allowance, and the user
cannot see what it spent"** — OpenAI's own words: "Usage settings do not show
details about your actions in the app" and "Usage settings may not show a
complete action-level history"
([help.openai.com/en/articles/20001542](https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites),
2026-10-22). The Relay and the device are flying blind on the user's plan.

### 5.3 Unattended use

- **Anthropic**: Consumer ToS §3.7 forbids accessing the Services "through
  automated or non-human means, whether through a bot, script, or otherwise"
  *unless* you use an API key "or where we otherwise explicitly permit it"
  ([consumer-terms](https://www.anthropic.com/legal/consumer-terms), 2025-10-08).
  So unattended use on a consumer subscription is permitted only where Anthropic
  has explicitly permitted it — which, on the evidence above, is the hosted-
  Claude-Code-under-commercial-agreement route.
- **Google**: explicitly not. "Wrapping `agy` inside third-party coding agents
  or applications, or automating account rotation, is not supported under consumer
  plans" ([Antigravity FAQ](https://antigravity.google/docs/faq/), 2026-10-22).
- **OpenAI**: the sanctioned partner route *is* an unattended-use route — that
  is what "eligible AI requests" in an app means ([siwc](https://developers.openai.com/siwc),
  2026-10-22). The Terms of Use bar "Automatically or programmatically extract
  data or Output", which is aimed at scraping, not at an approved app making
  requests ([terms-of-use](https://openai.com/policies/terms-of-use/), 2026-01-01).

### 5.4 Concurrency

**Not established** for the sanctioned consumer paths: no vendor publishes a
per-account concurrency limit for them. OpenAI's Codex access tokens are aimed
at "trusted, non-interactive Codex local workflows" and are a **ChatGPT
Enterprise** feature ([codex/auth](https://developers.openai.com/codex/auth/),
2026-10-22), which is the only documented unattended-automation credential on
any of the three paths.

---

## 6. The spend problem

**The question.** ADR-0006's `max_spend_usd` ($0.50) and `max_cost_per_step_usd`
($0.05) rest on "the Relay knows the provider's reported usage for the Run, so it
can enforce spend exactly" (`docs/adr/0006-run-budgets.md:28-29`), with the
fallback that "providers that do not report it fall back to an **estimated
per-step cost**, which is conservative but not exact"
(`docs/adr/0006-run-budgets.md:72-74`).

**Finding: no sanctioned consumer path exposes a per-token *dollar* cost, and
OpenAI explicitly warns against estimating included subscription usage from API
prices.**

| | Token counts visible? | Dollar amount visible? | Citation |
| --- | --- | --- | --- |
| OpenAI (SIWC, plan usage) | **Yes** — `usage: {input_tokens, input_tokens_details, output_tokens, …}` on the Responses API | **No.** "API token prices are separate from subscription usage; **don't use them to estimate included tasks**." Credits are the unit for *credit-based* plans, and included-plan usage has its own multipliers. | [API reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create) 2026-10-22; [codex/pricing](https://developers.openai.com/codex/pricing) 2026-10-22 |
| Anthropic (subscription OAuth) | **Yes** — `usage.input_tokens` / `output_tokens` (plus cache fields) | **No.** Subscription usage has no per-token price; Anthropic charges at standard API rates only for separately-enabled "usage credits". | [platform.claude.com API overview](https://platform.claude.com/docs/en/api/overview) 2026-10-22; [support 11145838](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) ~2026-10-15 |
| Google (Gemini CLI OAuth) | **Partly** — `/stats` shows total token usage, but **cached-token counts are API-key-only** | **No** | [Gemini CLI FAQ](https://geminicli.com/docs/resources/faq/) 2026-04-10 |
| *Unofficial* OpenAI (`/backend-api/wham/usage`) | Yes, plus quota state | **Almost** — the unofficial response shape includes `credits.balance` (e.g. `"$4.20"`), `credits.has_credits`, `spend_control.reached`, `rate_limit.primary_window.used_percent`, and `rate_limit_reset_credits.available_count` | [unofficial reference gist](https://gist.github.com/monperrus/21dc7d85ea518dc2a66606006d356b5b) 2026-10-22 — **unofficial, undocumented, and not usable in a sanctioned product** |

**What this means for ADR-0006 — stated as a fact, not a decision.**

1. `max_spend_usd` **cannot mean the same thing** on a subscription path. There
   is no metered spend to cap; what there is to cap is **the user's shared
   plan allowance**. The bound survives only if it is re-expressed (for example
   as a fraction of the user's remaining allowance, or as a provider-agnostic
   step/time bound with a user-visible consumption estimate).
2. `max_cost_per_step_usd` **cannot be enforced exactly**, because the only
   available signal is token counts. Converting tokens to dollars requires
   pricing them at list API rates — which OpenAI explicitly says not to do for
   included usage ([codex/pricing](https://developers.openai.com/codex/pricing),
   2026-10-22), and which would mis-report a subscription call as if it were a
   metered one. It remains a *reasonable upper-bound estimate*, not a cost.
3. ADR-0006's existing fallback clause is, in hindsight, the clause that carries
   the subscription case: "Providers that do not report it fall back to an
   estimated per-step cost" (`docs/adr/0006-run-budgets.md:72-74`). Under a
   subscription the estimate is the *only* figure, and its unit changes from
   dollars to **plan allowance consumed**.
4. The device-side subset (`max_steps`, `max_duration_ms`) is **unaffected** and
   remains the enforceable floor — ADR-0006 already says the device "cannot
   know the spend, so it does not pretend to" (`:40-45`). On a subscription path
   that sentence becomes the whole story.
5. A **quota signal, not a cost signal, is available**: the provider tells the
   caller when the user is out of allowance. OpenAI surfaces this as
   `response.failed` with `subscription_sharing_usage_limit_exceeded` or
   `subscription_sharing_usage_unavailable`
   ([models-and-inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference),
   2026-10-22), and Anthropic surfaces the five-hour/weekly limit as a hard stop
   ([support 11145838](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan),
   ~2026-10-15). Those are **terminal conditions**, not gradations — they say
   "stop", not "you have spent $0.04 of $0.50".

---

## 7. What this does and does not settle for AndroidUse

**Settled by the facts above:**

- **Google is ruled out** for a consumer-subscription credential model, by its
  own terms, twice, by name.
- **The `act` tool contract is compatible with at least one sanctioned path**
  (OpenAI's function/custom tools on SIWC), so ADR-0004's hand-written schema is
  not itself a blocker.
- **Manus's precedent does not support the subscription model.** Manus moved the
  *billing* of inference to the user's own API key while keeping the harness
  and the other services on Manus credits. If AndroidUse wants the Manus
  precedent, the analogous move is **BYO API key**, not BYO subscription — and
  that path has no vendor-policy obstacle at all.
- **`max_spend_usd` does not survive unchanged** in meaning, though it survives
  in form as an estimate.

**Not settled, and deliberately left to #39:**

- Whether the Relay holds a company key, the user's key, or the user's
  subscription credential. That is #39.
- Whether to apply to OpenAI's partner programme or Anthropic's commercial
  terms. That is a procurement decision, and #39 should record it as a
  dependency, not assume it.
- Which vendor. Out of scope per the map's "Out of scope" section.

**Two structural consequences of the credential choice, whichever way #39
goes:**

- **ADR-0008.** If the credential is the user's *subscription* OAuth token, the
  Relay holds a credential that can make model calls on the user's account. That
  is still "no Provider credential on the device", so ADR-0008 survives as
  written — but the Relay becomes a **credential broker for the user's account**,
  which is a materially different trust relationship from "holds our API key".
- **ADR-0001 / the topology.** OpenAI's SIWC requires a `127.0.0.1` loopback
  OAuth callback ([sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in),
  2026-10-22). On Android, that callback cannot live in the app. It must live in
  the **Relay**, which means the phone's sign-in flow ends at the Relay — and
  the Relay holds the long-lived refresh token. There is no configuration in
  which the phone holds the provider credential.

---

## 8. Not established

Recorded so the next reader does not mistake silence for a finding.

| Question | Why it is not established | What would establish it |
| --- | --- | --- |
| Does Manus have any consumer-subscription credential mode? | The Flex announcement names API-key partners only; no help-centre article covers it. | A Manus release note or help-centre article naming a subscription login. |
| Does xAI sanction third-party use of a SuperGrok subscription? | Warp documents such a connection, but xAI's own terms and OAuth docs were not located. | xAI's ToS and any xAI OAuth/partner documentation. |
| Does any vendor publish a **concurrency** limit for consumer-subscription paths? | Not found on any of the three primary doc sets. | Vendor rate-limit documentation specific to the consumer path. |
| Is there a **currently working, widely used, tool-capable** reverse-engineered **Claude web** endpoint (not the sanctioned `setup-token` credential)? | Not located in this pass; the 2026 enforcement wave appears to have closed this path. | A maintained open-source implementation plus evidence it still works. |
| Did Anthropic publish a first-party announcement of the June 2026 Agent SDK credit split and its rollback? | Only secondary sources (an X post and a user email) were found. | An Anthropic news post or help-centre article. |
| What exactly is OpenAI's partner-approval criteria, timeline, and cost? | The interest form is public; the criteria are not published. | The form's confirmation, or an OpenAI partner agreement. |
| Does Anthropic's hosted-Claude-Code route accept a **custom** `act` tool (as opposed to only Claude Code's built-in tools plus MCP)? | MCP is documented as a capability of the Agent SDK; the interaction with "the binary must not be modified" is not spelled out. | A statement from Anthropic sales, or a documented MCP-hosting arrangement. |

---

## 9. Sources

All retrieved 2026-10-22. Dates in parentheses are the source's own publication,
effective, or last-updated date where it has one.

**Manus**
- [Introducing Manus Flex: Use your own API key in the Manus workspace](https://manus.im/blog/introducing-manus-flex) — manus.im, 2026-09-29
- [Introducing Manus 2.0](https://manus.im/blog/introducing-manus-2-0) — manus.im, 2026-09-28
- [Explore all Manus AI models](https://manus.im/models) — manus.im
- [Manus Help Center — Manus 2.0 collection](https://help.manus.im/en/collections/19763651-manus-2-0) — help.manus.im
- [Manus Joins Meta](https://manus.im/blog/manus-joins-meta-for-next-era-of-innovation) / [A Note to Our Users](https://manus.im/blog/a-note-to-our-users) — manus.im (context only)
- [Manus launches desktop app 'My Computer'](https://www.cnbc.com/2026/03/18/metas-manus-launches-desktop-app-to-bring-its-ai-agent-onto-personal-devices.html) — CNBC, 2026-03-18 (secondary)

**OpenAI**
- [Sign in with ChatGPT — home](https://developers.openai.com/siwc) — developers.openai.com
- [ChatGPT plan usage: Overview](https://developers.openai.com/siwc/token-sharing-open-source) — developers.openai.com
- [Registration and sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in) — developers.openai.com
- [Accounts and sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions) — developers.openai.com
- [Models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference) — developers.openai.com
- [Preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations) — developers.openai.com
- [Token reference](https://developers.openai.com/siwc/token-sharing-open-source/token-reference) — developers.openai.com
- [Request a client ID](https://developers.openai.com/siwc/request-client-id) — developers.openai.com
- [Sign in with ChatGPT — partners directory](https://learn.chatgpt.com/docs/sign-in-with-chatgpt) — learn.chatgpt.com
- [Using your ChatGPT plan in other apps and sites](https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites) — help.openai.com, updated 2026-10-22
- [Authentication — Codex](https://developers.openai.com/codex/auth/) — developers.openai.com
- [Pricing — Codex / ChatGPT Work](https://developers.openai.com/codex/pricing) — developers.openai.com
- [Terms of Use](https://openai.com/policies/terms-of-use/) — openai.com, published 2026-01-01
- [Responses API — create a model response](https://developers.openai.com/api/reference/cli/resources/responses/methods/create) — developers.openai.com

**Anthropic**
- [Legal and compliance — Claude Code](https://code.claude.com/docs/en/legal-and-compliance) — code.claude.com
- [Authentication — Claude Code](https://code.claude.com/docs/en/authentication) — code.claude.com
- [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) — code.claude.com
- [Consumer Terms of Service](https://www.anthropic.com/legal/consumer-terms) — anthropic.com, effective 2025-10-08
- [Use Claude Code with your Pro or Max plan](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) — support.claude.com, updated ~2026-10-15
- [How do usage and length limits work?](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work) — support.claude.com, updated ~2026-10-15
- [Higher usage limits for Claude and a compute deal with SpaceX](https://www.anthropic.com/news/higher-limits-spacex) — anthropic.com, 2026-05-06
- [Rate limits — Claude Platform](https://platform.claude.com/docs/en/api/rate-limits) — platform.claude.com
- [API overview — Claude Platform](https://platform.claude.com/docs/en/api/overview) — platform.claude.com
- [Claude Max Usage — Agent SDK issue #11](https://github.com/anthropics/claude-agent-sdk-typescript/issues/11) — github.com/anthropics, 2026-03-30/31 (community report, marked resolved)

**Google**
- [Gemini CLI: License, Terms of Service, and Privacy Notices](https://geminicli.com/docs/resources/tos-privacy/) — geminicli.com, last updated 2026-04-10
- [Gemini CLI: Frequently asked questions](https://geminicli.com/docs/resources/faq/) — geminicli.com, last updated 2026-04-10
- [Gemini CLI: Quotas and pricing](https://geminicli.com/docs/resources/quota-and-pricing/) — geminicli.com
- [Google Antigravity Additional Terms of Service](https://antigravity.google/terms/) — antigravity.google
- [Google Antigravity — FAQ](https://antigravity.google/docs/faq/) — antigravity.google
- [An important update: Transitioning Gemini CLI to Antigravity CLI](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli) — developers.googleblog.com, 2026-05-19
- [Quotas and limits — Gemini for Google Cloud](https://docs.cloud.google.com/gemini/docs/quotas) — cloud.google.com, last updated 2026-10-20

**Unofficial paths (secondary / implementation sources)**
- [manus-codex-bridge — glama listing](https://glama.ai/mcp/servers/zhiqiang73-cpu/Manus-codex-bridge) — glama.ai
- [openai-codex-oauth — npm package page](https://www.jsdelivr.com/package/npm/openai-codex-oauth) — jsDelivr
- [arthjean/pyxis](https://github.com/arthjean/pyxis) — GitHub
- [codex-as-api — PyPI](https://libraries.io/pypi/codex-as-api) — libraries.io
- [OpenAI Codex `wham/usage` API — unofficial reference](https://gist.github.com/monperrus/21dc7d85ea518dc2a66606006d356b5b) — GitHub Gist
- [Claude provider roadmap after Agent SDK billing changes — issue #1029](https://github.com/getpaseo/paseo/issues/1029) — GitHub, 2026-06-15 to 2026-06-20
- [Claude Code Subscription: Safe Use Without a Ban](https://claudefa.st/blog/guide/development/claude-code-subscription) — claudefa.st
- [Hermes Agent — Claude Code OAuth credit accounting issue #47260](https://github.com/NousResearch/hermes-agent/issues/47260) — GitHub, 2026-06-16
- [Addressing Antigravity Bans & Reinstating Access — gemini-cli discussion #20632](https://github.com/google-gemini/gemini-cli/discussions/20632) — GitHub, 2026-05 to 2026-06
- [Service update: mitigating abuse and prioritizing traffic — gemini-cli discussion #22970](https://github.com/google-gemini/gemini-cli/discussions/22970) — GitHub, 2026-04-30
- [Urgent: Mass 403 ToS bans on Gemini API/Antigravity for open-source CLI users](https://discuss.ai.google.dev/t/urgent-mass-403-tos-bans-on-gemini-api-antigravity-for-open-source-cli-users-paid-tier/124508) — discuss.ai.google.dev, 2026
- [Anthropic Bans Claude Subscription OAuth in Third-Party Apps](https://winbuzzer.com/2026/02/19/anthropic-bans-claude-subscription-oauth-in-third-party-apps-xcxwbn/) — WinBuzzer, 2026-02-19
- [Anthropic blocks third-party use of Claude Code subscriptions — HN thread](https://news.ycombinator.com/item?id=46549823) — Hacker News, 2026
- [Anthropic's New Billing Split Reveals What AI Agents Actually Cost](https://beam.ai/agentic-insights/anthropics-new-billing-split-reveals-what-ai-agents-actually-cost) — Beam.ai, 2026-06
- [Anthropic Blocks Third-Party Tools From Claude (2026)](https://decodethefuture.org/en/anthropic-blocks-third-party-tools/) — decodethefuture.org, 2026-04
