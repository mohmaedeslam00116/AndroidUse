# AGENTS.md

## Toolchain

`:protocol` pins `jvmToolchain(17)`. Gradle provisions that JDK itself through
the `foojay-resolver-convention` plugin in `settings.gradle.kts`, so any JDK 17
or newer runs the build; the first build downloads a JDK 17 if the machine has
none. Gradle 8.11.1 cannot run on JDK 25.

`GRADLE_USER_HOME` and `TEMP` must point at a drive with room - a full `C:`
fails the build. On this machine `GRADLE_USER_HOME` is `D:\.gradle`.

The Android SDK is at `D:\Android\Sdk` (`ANDROID_HOME` is set). It has
platforms 30, 31, 33, 34, 35, 36 and 36.1, and **no** `android-29` platform.

**No emulator is provisioned, and none is needed.** The maintainer does not use
one. Any acceptance criterion that needs a running device is recorded as not
locally verifiable, with the reason, and is never marked met. Do not stand up
an emulator to satisfy one.

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues (`mohmaedeslam00116/AndroidUse`), operated via the `gh` CLI. See `docs/agents/issue-tracker.md`.

The [wayfinder map](https://github.com/mohmaedeslam00116/AndroidUse/issues/12) is the canonical index of the backlog. The nine tracer bullets (#2 to #10) and the Provider-adapter issue (#11) are its children, and their order is expressed as **native GitHub issue dependencies** - read the blocking edges, do not re-derive the order from the issue bodies.

### Triage labels

Five canonical triage roles; each label string equals its role name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: one `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
