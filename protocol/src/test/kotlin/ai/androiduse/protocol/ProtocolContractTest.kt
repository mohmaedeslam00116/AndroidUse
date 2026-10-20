package ai.androiduse.protocol

import com.google.common.truth.Truth.assertThat
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Test

class ProtocolContractTest {

    // ---- Target -----------------------------------------------------------------------------

    @Test
    fun `a target is exactly one of element index or point`() {
        assertThat(Target.element(17).elementIndex).isEqualTo(17)
        assertThat(Target.point(412, 1188).x).isEqualTo(412)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `a target with neither element nor point is refused`() {
        Target()
    }

    @Test(expected = IllegalArgumentException::class)
    fun `a target with both element and point is refused`() {
        Target(elementIndex = 3, x = 1, y = 2)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `a target with a half point is refused`() {
        Target(x = 1)
    }

    // ---- Action and capability ---------------------------------------------------------------

    @Test
    fun `every action kind maps to exactly one capability`() {
        val actions = allActions()
        assertThat(actions.map { it.kind }.toSet()).hasSize(13)

        val byKind = actions.groupBy { it.kind }
        for ((kind, instances) in byKind) {
            assertThat(instances.map { it.capability }.distinct()).hasSize(1)
            assertThat(instances.map { it.capability }).isNotEmpty()
            assertThat(kind.wireName).isNotEmpty()
        }
    }

    @Test
    fun `gestures and typing are different capabilities`() {
        assertThat(Action.Type(null, "x").capability).isEqualTo(Capability.INPUT_TEXT)
        assertThat(Action.Click(Target.element(0)).capability).isEqualTo(Capability.INPUT_TAP)
    }

    @Test
    fun `actions serialise with an action discriminator`() {
        val encoded = Protocol.encodeAction(Action.Click(Target.element(4)))
        assertThat(encoded).contains("\"action\":\"click\"")
        assertThat(encoded).contains("\"element_index\":4")
    }

    @Test
    fun `an action round trips through the codec`() {
        val action = Action.Type(Target.element(2), "مرحبا", clear = true)
        assertThat(Protocol.decodeAction(Protocol.encodeAction(action))).isEqualTo(action)
    }

    @Test
    fun `arabic text survives the round trip`() {
        val action = Action.Type(Target.element(2), "افتح الإعدادات")
        val decoded = Protocol.decodeAction(Protocol.encodeAction(action))
        assertThat((decoded as Action.Type).text).isEqualTo("افتح الإعدادات")
    }

    // ---- Outcome ----------------------------------------------------------------------------

    @Test
    fun `outcomes serialise with a status discriminator`() {
        val encoded = Protocol.encodeOutcome(Outcome.StaleElement(7, "gone"))
        assertThat(encoded).contains("\"status\":\"stale_element\"")
        assertThat(encoded).contains("\"requestedIndex\":7")
    }

    @Test
    fun `an outcome round trips through the codec`() {
        val outcome = Outcome.Denied(Capability.MESSAGE_SEND, "policy")
        assertThat(Protocol.decodeOutcome(Protocol.encodeOutcome(outcome))).isEqualTo(outcome)
    }

    @Test
    fun `outcome failure classification covers every non-ok outcome`() {
        val outcomes = listOf(
            Outcome.Ok(),
            Outcome.Unchanged(),
            Outcome.StaleElement(1),
            Outcome.Denied(Capability.MESSAGE_SEND, "policy"),
            Outcome.Timeout(100),
            Outcome.Unsupported("no"),
            Outcome.Failed("boom"),
        )
        val failures = outcomes.filter { it.isFailure }
        assertThat(failures).hasSize(outcomes.size - 1)
        assertThat(Outcome.Ok().isFailure).isFalse()
    }

    // ---- Policy -----------------------------------------------------------------------------

    @Test
    fun `the default policy denies irreversible capabilities`() {
        val policy = CapabilityPolicy.defaultPolicy()
        assertThat(policy.verdictFor(Capability.PAYMENT_AUTHORIZE)).isEqualTo(PolicyVerdict.DENY)
        assertThat(policy.verdictFor(Capability.ACCOUNT_CHANGE)).isEqualTo(PolicyVerdict.DENY)
        assertThat(policy.verdictFor(Capability.CREDENTIAL_READ)).isEqualTo(PolicyVerdict.DENY)
    }

    @Test
    fun `the default policy asks for consequential capabilities and allows the rest`() {
        val policy = CapabilityPolicy.defaultPolicy()
        assertThat(policy.verdictFor(Capability.MESSAGE_SEND)).isEqualTo(PolicyVerdict.ASK)
        assertThat(policy.verdictFor(Capability.CALL_PLACE)).isEqualTo(PolicyVerdict.ASK)
        assertThat(policy.verdictFor(Capability.SETTINGS_WRITE)).isEqualTo(PolicyVerdict.ASK)
        assertThat(policy.verdictFor(Capability.SCREEN_READ)).isEqualTo(PolicyVerdict.ALLOW)
        assertThat(policy.verdictFor(Capability.INPUT_TAP)).isEqualTo(PolicyVerdict.ALLOW)
    }

    @Test
    fun `narrowing keeps the most restrictive verdict`() {
        val device = CapabilityPolicy.defaultPolicy()
        val relay = CapabilityPolicy(mapOf(Capability.INPUT_TAP to PolicyVerdict.DENY))

        val narrowed = device.narrowedBy(relay)

        assertThat(narrowed.verdictFor(Capability.INPUT_TAP)).isEqualTo(PolicyVerdict.DENY)
        assertThat(narrowed.verdictFor(Capability.MESSAGE_SEND)).isEqualTo(PolicyVerdict.ASK)
        assertThat(narrowed.verdictFor(Capability.SCREEN_READ)).isEqualTo(PolicyVerdict.ALLOW)
    }

    @Test
    fun `narrowing cannot widen a denial into an allow`() {
        val device = CapabilityPolicy(mapOf(Capability.MESSAGE_SEND to PolicyVerdict.DENY))
        val relay = CapabilityPolicy(mapOf(Capability.MESSAGE_SEND to PolicyVerdict.ALLOW))

        val narrowed = device.narrowedBy(relay)

        assertThat(narrowed.verdictFor(Capability.MESSAGE_SEND)).isEqualTo(PolicyVerdict.DENY)
    }

    @Test
    fun `narrowing is order independent`() {
        val a = CapabilityPolicy(mapOf(Capability.INPUT_TAP to PolicyVerdict.ASK))
        val b = CapabilityPolicy(mapOf(Capability.INPUT_TAP to PolicyVerdict.DENY))

        assertThat(a.narrowedBy(b)).isEqualTo(b.narrowedBy(a))
    }

    @Test
    fun `the careful preset asks for everything consequential but still allows reading`() {
        val careful = CapabilityPolicy.carefulPolicy()
        assertThat(careful.verdictFor(Capability.MESSAGE_SEND)).isEqualTo(PolicyVerdict.ASK)
        assertThat(careful.verdictFor(Capability.SETTINGS_WRITE)).isEqualTo(PolicyVerdict.ASK)
        assertThat(careful.verdictFor(Capability.SCREEN_READ)).isEqualTo(PolicyVerdict.ALLOW)
        assertThat(careful.verdictFor(Capability.PAYMENT_AUTHORIZE)).isEqualTo(PolicyVerdict.DENY)
    }

    @Test
    fun `the trust preset asks only for the irreversible tier`() {
        val trust = CapabilityPolicy.trustPolicy()
        assertThat(trust.verdictFor(Capability.MESSAGE_SEND)).isEqualTo(PolicyVerdict.ALLOW)
        assertThat(trust.verdictFor(Capability.PAYMENT_AUTHORIZE)).isEqualTo(PolicyVerdict.DENY)
    }

    // ---- Capability resolution ---------------------------------------------------------------

    @Test
    fun `a plain tap keeps its own capability`() {
        val resolved = CapabilityResolver.resolve(
            Action.Click(Target.element(1)),
            ActionContext(targetText = "Next"),
        )
        assertThat(resolved).isEqualTo(Capability.INPUT_TAP)
    }

    @Test
    fun `tapping a send button is a message send`() {
        val resolved = CapabilityResolver.resolve(
            Action.Click(Target.element(1)),
            ActionContext(targetText = "Send"),
        )
        assertThat(resolved).isEqualTo(Capability.MESSAGE_SEND)
    }

    @Test
    fun `tapping an arabic send button is a message send`() {
        val resolved = CapabilityResolver.resolve(
            Action.Click(Target.element(1)),
            ActionContext(targetText = "إرسال"),
        )
        assertThat(resolved).isEqualTo(Capability.MESSAGE_SEND)
    }

    @Test
    fun `tapping a pay button is a payment authorisation`() {
        val resolved = CapabilityResolver.resolve(
            Action.Click(Target.element(1)),
            ActionContext(targetText = "Pay now"),
        )
        assertThat(resolved).isEqualTo(Capability.PAYMENT_AUTHORIZE)
    }

    @Test
    fun `typing into a password field is a credential read`() {
        val resolved = CapabilityResolver.resolve(
            Action.Type(Target.element(1), "hunter2"),
            ActionContext(targetIsPassword = true),
        )
        assertThat(resolved).isEqualTo(Capability.CREDENTIAL_READ)
    }

    @Test
    fun `a non press action is never escalated`() {
        val resolved = CapabilityResolver.resolve(
            Action.Type(Target.element(1), "hello"),
            ActionContext(targetText = "Send"),
        )
        assertThat(resolved).isEqualTo(Capability.INPUT_TEXT)
    }

    // ---- Envelope ---------------------------------------------------------------------------

    @Test
    fun `relay messages round trip`() {
        val message = RelayMessage.RunStart(
            runId = "r-1",
            goal = "افتح الساعة واضبط تنبيهًا",
            language = RunLanguage.ARABIC,
            budget = RunBudget(maxSteps = 12),
        )
        assertThat(Protocol.decodeRelayMessage(Protocol.encodeRelayMessage(message)))
            .isEqualTo(message)
    }

    @Test
    fun `device messages round trip`() {
        val message = DeviceMessage.PerceptionMessage(
            step = 3,
            perception = Perception(
                frame = Frame(base64 = "AAA", width = 100, height = 200),
                tree = listOf(
                    UiElement(index = 0, text = "الإعدادات", clickable = true, bounds = Bounds(0, 0, 10, 10)),
                ),
                foregroundPackage = "com.android.settings",
                screenWidthPx = 1080,
                screenHeightPx = 2400,
                fingerprint = "abc123",
            ),
        )
        assertThat(Protocol.decodeDeviceMessage(Protocol.encodeDeviceMessage(message)))
            .isEqualTo(message)
    }

    @Test
    fun `an unknown field from a newer relay does not break an older device`() {
        val text = """{"type":"ping","something_new":42}"""
        assertThat(Protocol.decodeRelayMessage(text)).isEqualTo(RelayMessage.Ping)
    }

    // ---- Budget -----------------------------------------------------------------------------

    @Test
    fun `a budget intersection takes the tighter bound on every axis`() {
        val a = RunBudget(maxSteps = 40, maxDurationMs = 600_000, maxSpendUsd = 0.50)
        val b = RunBudget(maxSteps = 10, maxDurationMs = 60_000, maxSpendUsd = 1.00)
        val merged = a.intersect(b)
        assertThat(merged.maxSteps).isEqualTo(10)
        assertThat(merged.maxDurationMs).isEqualTo(60_000)
        assertThat(merged.maxSpendUsd).isEqualTo(0.50)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `a budget with no steps is refused`() {
        RunBudget(maxSteps = 0)
    }

    // ---- Schema -----------------------------------------------------------------------------

    @Test
    fun `the action schema names every action kind`() {
        val schema = ActionSchema.toolSchema(RunLanguage.ENGLISH)
        val function = schema["function"]!!.jsonObject
        val parameters = function["parameters"]!!.jsonObject
        val properties = parameters["properties"]!!.jsonObject
        val actionProperty = properties["action"]!!.jsonObject
        val enumValues = actionProperty["enum"]!!.jsonArray

        assertThat(enumValues.map { it.jsonPrimitive.content })
            .containsExactly(
                "screenshot", "click", "double_click", "long_press", "drag", "type",
                "scroll", "press_key", "open_app", "list_apps", "wait", "finish", "ask_user",
            )
    }

    @Test
    fun `the action schema is available in arabic`() {
        val schema = ActionSchema.toolSchema(RunLanguage.ARABIC)
        val function = schema["function"]!!.jsonObject
        val description = function["description"]!!.jsonPrimitive.content
        assertThat(description).contains("الهاتف")
    }

    @Test
    fun `the language of a run is derived from a tag`() {
        assertThat(RunLanguage.ofTag("ar-EG")).isEqualTo(RunLanguage.ARABIC)
        assertThat(RunLanguage.ofTag("ar")).isEqualTo(RunLanguage.ARABIC)
        assertThat(RunLanguage.ofTag("en-GB")).isEqualTo(RunLanguage.ENGLISH)
        assertThat(RunLanguage.ofTag(null)).isEqualTo(RunLanguage.ENGLISH)
    }

    private fun allActions(): List<Action> = listOf(
        Action.Screenshot,
        Action.Click(Target.element(0)),
        Action.DoubleClick(Target.element(0)),
        Action.LongPress(Target.element(0)),
        Action.Drag(Target.element(0), Target.element(1)),
        Action.Type(null, "hello"),
        Action.Scroll(null, Direction.DOWN),
        Action.PressKey(SystemKey.BACK),
        Action.OpenApp("com.example"),
        Action.ListApps,
        Action.Wait(),
        Action.Finish(true, "done"),
        Action.AskUser("?"),
    )
}
