# ADR-0008: No shell tool; file access is app-scoped; there is no on-device key material

- Status: Accepted
- Date: 2026-10-20

## Context

An app that holds an AccessibilityService and a model-driven action loop is a
high-value target. The reference projects grant the Agent capabilities that
are far broader than "operate my screen":

- **CellClaw** — `script.exec` runs arbitrary shell through
  `ProcessBuilder("sh", "-c", command)` with a 120-second timeout, and the
  model may call it. `file.read`, `file.write` and `file.list` accept
  **absolute paths** with no sandbox, so the model can read and write any
  file the app UID can reach. Its command channel to the AccessibilityService
  is an exported broadcast, so a third-party app gets the same powers without
  going through the model at all.
- **ClosePaw** — declares `com.termux.permission.RUN_COMMAND` and
  `moe.shizuku.manager.permission.API_V23` in its shipped manifest, and
  exposes `shell` and `termux_shell` tools. Its `NOTICE` also reveals a
  proprietary on-device SDK embedded in the release binary.
- **android-agent** — a Lua scripting escape hatch (`run_script`, `save_script`,
  `call_script`), and a `network_security_config.xml` that permits cleartext
  traffic **globally**, which means the model API key can travel in the clear
  to any configured endpoint. It also depends on `security-crypto
  1.1.0-alpha06`, an alpha, on the key-storage path.

## Decision

**No shell.** AndroidUse ships no command execution capability of any kind:
no `Runtime.exec`, no `ProcessBuilder`, no Lua, no Termux integration, no
Shizuku, no hidden-API input injection. The Agent's entire effect on the device
is the `act` action set (ADR-0004).

**File access is app-scoped.** If the app reads or writes files at all, it does
so inside its own data directory (`filesDir`, `cacheDir`, `noBackupFilesDir`)
and through `FileProvider` for user-initiated sharing. There is no tool that
takes a path.

**No model credentials on the device.** The phone stores only a revocable
per-device token used to authenticate to the Relay (ADR-0001). There is no
provider API key on the device, so there is no provider key to leak, and no
`security-crypto` dependency on the critical path.

**Cleartext is off.** The app's network security configuration denies
cleartext. The Relay is reached over TLS.

**The manifest is minimal.** AndroidUse declares only what it uses, and the
`<queries>` element is scoped to the launcher intent rather than
`QUERY_ALL_PACKAGES`. Message and contact reading, if they are ever added,
arrive as their own Capability with their own Approval. The exact allow-list
and deny-list are enumerated in `docs/release-permissions.txt` and asserted by
the release test, so there is one list rather than two (ADR-0010).

**One privileged component.** Exactly one service in the app holds
AccessibilityService powers, and the only way to reach it is the app-private
channel of ADR-0005.

## Consequences

**Good**

- The worst thing a compromised Relay can do is drive the screen, which is
  what the user already granted, and it still faces the Local Policy.
- There is no file exfiltration path for the Agent, because there is no
  arbitrary-path tool.
- The manifest is small enough to be auditable by a user in a minute, which
  matters for a product that asks for an Accessibility grant.
- Shipping a release binary with no proprietary SDK and no alpha crypto
  dependency on the key path is straightforward.

**Bad, and accepted**

- The Agent cannot do things that genuinely need shell access, such as
  configuring a device setting that has no UI, or talking to a local service
  over `adb`. We accept this. The user asked for an app that operates the
  phone, not a general device-automation platform.
- Some tasks that CellClaw's `sms.send` does in one step will take this app
  five steps through the messaging UI. That is the correct trade: the
  capability is narrower and therefore the approval and Play-policy surface
  is smaller.

**Neutral**

- We may later add narrowly-scoped capabilities (read notifications, share a
  file the user picked). Each will be its own Capability, its own Approval
  default, and its own manifest entry.

## Alternatives considered

**Offer a shell tool with an approval gate, like CellClaw.** Rejected: an
approval gate is a speed bump, not a boundary, and shell access from a model
is a well-known route to total compromise. A model that can run shell can
exfiltrate everything the app UID can read, which is exactly what we are
declining to offer.

**Offer scripting, like android-agent's Lua.** Rejected for the same reason,
with the added problem of a sandbox that the script might escape.

**Ship the model key on the device, like all three references.** Rejected: it
is the main reason our topology has a server (ADR-0001), and giving it up
would give up the cost accounting and the kill-switch.
