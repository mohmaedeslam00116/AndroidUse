# ADR-0010: The release manifest declares five permissions, and the Overlay cannot swallow a touch

- Status: Accepted
- Date: 2026-10-22

## Context

NFR-4 said only what the manifest must **not** contain: "The manifest declares
only used permissions; no `QUERY_ALL_PACKAGES`, no SMS/contacts/camera/location
in v1." The spec's own acceptance criterion 5 - "`grep` over the release
manifest shows only the permissions in NFR-4" - was therefore **not testable**,
because NFR-4 named no set to compare against.

The required set was implied across four documents and never enumerated:

- ADR-0002 requires a foreground service of type `mediaProjection`, started
  **before** the consent intent on Android 14+. That implies
  `FOREGROUND_SERVICE` and `FOREGROUND_SERVICE_MEDIA_PROJECTION`, and an
  `android:foregroundServiceType` entry. Both permissions are **normal** -
  granted at install, never revocable - and the platform is unforgiving
  about them: without the type permission on API 34+ `startForeground()`
  throws `SecurityException`, and without the type in the manifest it throws
  `MissingForegroundServiceTypeException`.
- ADR-0005 requires the control service to be declared `exported="false"`
  with the signature-level permission `ai.androiduse.permission.DEVICE_CONTROL`,
  and the AccessibilityService to be declared `exported="true"` with
  `BIND_ACCESSIBILITY_SERVICE`.
- The Overlay is drawn above other apps, which implies
  `SYSTEM_ALERT_WINDOW` - a **special** permission, granted in Settings, and
  the one entry on this list that is a real security question, because it
  lets the app draw over everything and receive the user's touches.
- The Relay connection over TLS implies no permission at all, which is the
  point of ADR-0008's cleartext rule - except that `INTERNET` itself must be
  declared, and without it there is no WebSocket at all.

Two further problems came out of writing the list down.

**"The three permissions" was never defined.** The spec's section 8,
criterion 1 says "a user grants the three permissions and runs ...". The
number was never explained, and the real user-facing grants are **four**, of
which only two are manifest permissions the user grants at runtime: the
AccessibilityService toggle (a Settings switch, not a permission), the
MediaProjection consent (a consent dialog, not a permission),
`SYSTEM_ALERT_WINDOW` (a Settings grant), and `POST_NOTIFICATIONS` (a runtime
prompt on API 33+).

**`POST_NOTIFICATIONS` is not required to run the capture.** The platform is
explicit: "Apps don't need to request the `POST_NOTIFICATIONS` permission in
order to launch a foreground service." If it is denied, the foreground
service's notification is not shown in the drawer, but the service still runs
and is still visible in the FGS Task Manager. The permission therefore buys
*visibility*, not function. And on API 33+ the foreground service's
notification is dismissible by default anyway.

## Decision

### The allow-list is five permissions, each with its reason

The list itself, and the implemented feature that justifies each entry, live
in **`docs/release-permissions.txt`** - one line per permission, with the
justification after a `#`. That file is the single source of truth and the
test in `:app` reads it.

| Permission | Level | Why it is there |
| --- | --- | --- |
| `android.permission.INTERNET` | normal, auto-granted | the Relay's WebSocket connection, over TLS. Without it there is no WebSocket at all |
| `android.permission.FOREGROUND_SERVICE` | normal, auto-granted | the MediaProjection capture service (ADR-0002) |
| `android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION` | normal, auto-granted | the same service's foreground service type on API 34+. Without it `startForeground()` throws `SecurityException` |
| `android.permission.SYSTEM_ALERT_WINDOW` | special, granted in Settings | the Overlay: the Approval card and the Run's status line (ADR-0002, ADR-0007) |
| `android.permission.POST_NOTIFICATIONS` | dangerous, API 33+ | telling the user their screen is being shared, while it is |

### The deny-list is eight permissions

`QUERY_ALL_PACKAGES`, `READ_SMS`, `READ_CONTACTS`, `CAMERA`,
`ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `ACCESS_BACKGROUND_LOCATION`,
`READ_PHONE_STATE`. ADR-0008 already decided these; what was missing was a
list a test could read.

One of them had to be renamed on the way. ADR-0008 and NFR-4 both wrote
"`LOCATION`", which is **not a permission that exists** - asserting its absence
tests nothing. The real names are `ACCESS_FINE_LOCATION` and
`ACCESS_COARSE_LOCATION`, plus `ACCESS_BACKGROUND_LOCATION` for the background
case, and those are what the file names. #10's brief had it right; the ADR
and the spec did not.

### The Overlay cannot swallow a touch

This is the condition that makes `SYSTEM_ALERT_WINDOW` acceptable here.

The Overlay's window is laid out with `FLAG_NOT_TOUCHABLE`,
`FLAG_NOT_FOCUSABLE` and `FLAG_NOT_TOUCH_MODAL`, so it neither receives the
user's touches nor blocks the app underneath. `dispatchGesture` - the
AccessibilityService's own tap and swipe mechanism - reaches the app below,
which is the only way `act` can work at all.

The window becomes **touchable only while an Approval card is on screen**. At
that moment the Agent is blocked waiting for the user's decision, so nothing
underneath needs the touch, and the user can answer. The rule is therefore
not "the Overlay is careful about touches" but "**the Overlay takes touches
only when it is asking the user a question**".

The window is hidden around captures, as ADR-0002 already requires, so it
cannot appear in its own frames.

### `POST_NOTIFICATIONS` is requested at the first Run, not at first launch

The request is deferred until the app has a reason to ask, which is the
moment the user starts a Run and their screen is about to be shared. Asking
at first launch would spend a prompt on a user who may never run anything,
and on API 32 and below a single denial is permanent until the app is
updated.

If the user denies it, the capture still runs and the foreground service is
still visible in the FGS Task Manager.

### One file is the source of truth

`docs/release-permissions.txt` holds the allow-list and the deny-list. The
test in `:app` reads it and asserts that the release manifest's
`<uses-permission>` set is **exactly** the allow-list and that the deny-list
is absent. ADR-0008's prose keeps the rule; the file keeps the set. There
is one of each, and the test reads the one that can be compared.

### The rest of the manifest's surface is asserted by name

A test that only compares `<uses-permission>` passes while the control
service is exported without its guard. So the release assertion covers:

- the custom signature-level permission `ai.androiduse.permission.DEVICE_CONTROL`;
- the AccessibilityService's component guard `android.permission.BIND_ACCESSIBILITY_SERVICE`;
- the control service's component guard `ai.androiduse.permission.DEVICE_CONTROL`,
  with the service declared `exported="false"`;
- `<queries>` scoped to the launcher intent, never `QUERY_ALL_PACKAGES`;
- `android:foregroundServiceType="mediaProjection"` on the capture service.

## Consequences

**Good**

- NFR-4 and the spec's criterion 5 become testable, and the manifest
  becomes auditable by a user in a minute - which matters for a product that
  asks for an Accessibility grant.
- The Overlay's touch behaviour is a stated rule rather than an
  implementation detail, and it is the rule that makes the overlay
  permission defensible.
- The set is small enough that "adding a permission to make the assertion
  pass is a defect, not a fix" is enforceable by a machine.

**Bad, and accepted**

- The user is asked for four things before the first Run: the
  AccessibilityService toggle, the MediaProjection consent, the overlay
  grant, and the notification prompt. Two of those are not manifest
  permissions at all, and the spec's "the three permissions" was wrong
  about the number.
- `SYSTEM_ALERT_WINDOW` is a **Play policy surface**. The app must declare
  its overlay use, and Play reviews overlay usage against its
  "background activity launch" and overlay policies. The reference analysis
  already records Play Store viability as an open risk.
- The `mediaProjection` foreground service type needs a **Play Console
  declaration with a demo video** showing the user initiating the capture.
  That is a release-time cost, not a build-time one.
- On API 33+ the foreground service's notification is dismissible by default,
  so the notification is not a reliable transparency surface. The system's
  own capture indicator and the Overlay's status line are the load-bearing
  ones.

**Neutral**

- The list has five entries today. Every future capability that needs a
  platform permission adds a line to the file, a row to the table above, and
  a justification - which is the intended friction.

## Alternatives considered

**No `SYSTEM_ALERT_WINDOW`: the Approval card becomes a full-screen
Activity, the status line becomes a notification.** Rejected: ADR-0002's
requirement that the Overlay be "hidden or excluded around captures" is a
statement about a window, not an Activity, and a full-screen Activity would
cover the very screen the user is approving an action on - hiding the
grounding the decision is about.

**The Approval card as a notification with approve and deny buttons.**
Rejected: a notification is dismissible and easy to miss for a decision that
stops the Run, and the Run waits on it. The Approval surface needs to be
in front of the user at the moment the decision is asked.

**`POST_NOTIFICATIONS` never requested.** Rejected: an app that captures the
whole screen should say so in a place the user cannot swipe away, and the
request costs one prompt, deferred to the first Run.

**A per-build-variant allow-list.** Rejected: one release, one list. A
manifest is static; a list that can be computed is not auditable.

## Related

- [ADR-0002](0002-mediaprojection-primary-perception.md) - the capture
  service and the foreground service type.
- [ADR-0005](0005-app-private-accessibility-bridge.md) - the custom
  permission and the component guards.
- [ADR-0008](0008-no-shell-no-unrestricted-file-io.md) - the minimal
  manifest, and the deny-list this ADR enumerates.
