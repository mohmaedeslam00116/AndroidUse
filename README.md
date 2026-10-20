# AndroidUse

An Android application that lets a **cloud** AI agent see the phone's screen
and carry out multi-step tasks on it — the way a Computer Use agent drives a
desktop, but on a stock phone, with **no root** and **no companion PC**.

The user gives a goal in Arabic or English. The agent perceives the screen,
navigates between apps, taps, scrolls, types, executes multi-step tasks,
verifies the results, recovers from failures, and asks the user for approval
before anything sensitive.

**Status:** v0.1.0 in design and scaffold. The protocol contract is
implemented and tested; the Android app and the relay are the next tracer
bullets.

## Layout

| Path | What it is |
| --- | --- |
| `CONTEXT.md` | The domain model and the vocabulary. Read this first. |
| `docs/adr/` | The load-bearing decisions, with the alternatives that were rejected. |
| `docs/spec/0001-product-spec.md` | The product and technical specification. |
| `docs/research/reference-analysis.md` | What three existing phone-agent projects do, what we take from them, and what we refuse. |
| `docs/agents/` | The configuration the engineering skills read. |
| `protocol/` | The wire contract, shared by the phone and the relay. Pure Kotlin, no Android. |
| `app/` | The Android application. |
| `relay/` | The cloud relay: model credentials, the agent loop, budgets, approvals. |
| `tools/eval/` | The evaluation harness. |

## The shape of it

```
┌───────────────────── AndroidUse app (Android 10+) ─────────────────────┐
│  :app process    Compose UI · Overlay · Local Policy · RelayClient      │
│        │ bound Messenger, signature-level permission                   │
│  :a11y process   AccessibilityService · frame capture · executors      │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │ wss
┌──────────────────────────────▼─────────────────────────────────────────┐
│  Relay   Agent loop · model credentials · budgets · approvals            │
│    ──► model providers                                                 │
└────────────────────────────────────────────────────────────────────────┘
```

The phone decides nothing. It executes actions the relay asks for, refuses
what the local policy forbids, and reports structured outcomes back. The
relay holds the model key, so the phone never does.

## The five decisions that shape everything

| ADR | Decision |
| --- | --- |
| [0001](docs/adr/0001-cloud-agent-relay.md) | The agent loop runs in the cloud relay, not on the device. |
| [0002](docs/adr/0002-mediaprojection-primary-perception.md) | MediaProjection is the pixel channel; the accessibility tree is the structural channel. |
| [0003](docs/adr/0003-capability-based-approval.md) | Approval is per **capability**, resolved in context, and enforced on the device. |
| [0004](docs/adr/0004-native-computer-use-action-set.md) | One `act` tool with a discriminated action payload. |
| [0008](docs/adr/0008-no-shell-no-unrestricted-file-io.md) | No shell, no arbitrary file access, no model key on the device. |

## Building

The build needs JDK 17 and the Android SDK (compileSdk 35). The Gradle
wrapper pins the rest.

```bash
./gradlew :protocol:test     # the wire contract
./gradlew :app:assembleDebug
./gradlew :relay:run
```

`GRADLE_USER_HOME` and `TEMP` are expected to point at a drive with room:
a full `C:` will fail the build and the JADX bridge alike.

## Work tracking

Issues live in this repository's GitHub Issues. The specification is issue
[#1](https://github.com/mohmaedeslam00116/AndroidUse/issues/1); the tracer
bullets are [#2](https://github.com/mohmaedeslam00116/AndroidUse/issues/2)
through [#10](https://github.com/mohmaedeslam00116/AndroidUse/issues/10).

## Licence

To be decided. Note that the reference projects analysed in
`docs/research/reference-analysis.md` are **not** uniformly licensed — only
ClosePaw ships a licence file — and nothing has been copied from them.
