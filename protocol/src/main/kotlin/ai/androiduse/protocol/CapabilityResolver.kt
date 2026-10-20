package ai.androiduse.protocol

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * The context an action is performed in.
 *
 * A computer-use action set describes *gestures*, and a gesture alone does not
 * say what it means. Tapping a button is `INPUT_TAP`; tapping the Send button
 * in a chat app is really `MESSAGE_SEND`. Without context the capability
 * policy would never fire for the actions that matter most.
 *
 * The device therefore resolves the **effective capability** of an action by
 * looking at where it is happening. See `docs/adr/0003-capability-based-approval.md`.
 */
@Serializable
data class ActionContext(
    @SerialName("foreground_package") val foregroundPackage: String? = null,
    @SerialName("target_text") val targetText: String? = null,
    @SerialName("target_description") val targetDescription: String? = null,
    @SerialName("target_class") val targetClass: String? = null,
    @SerialName("target_is_password") val targetIsPassword: Boolean = false,
) {
    /** Everything the device can read about the element the action addresses. */
    val targetLabels: List<String>
        get() = listOfNotNull(targetText, targetDescription).map { it.lowercase() }
}

/**
 * Resolves the effective capability of an action.
 *
 * The rules are deliberately conservative in one direction only: a gesture may
 * be *escalated* to a more dangerous capability, never de-escalated. A tap
 * that lands on a "Send" button is treated as sending, even if the agent
 * thought of it as a plain tap.
 */
object CapabilityResolver {

    /** Words that mean "this completes an outward-facing action". */
    val sendWords: List<String> = listOf(
        "send", "submit", "post", "publish", "share", "send message", "place order",
        "continue", "done", "ok", "yes", "agree", "confirm",
        // Arabic
        "إرسال", "أرسل", "إرسل", "مشاركة", "تأكيد", "موافق", "نعم", "متابعة", "تم", "إتمام",
    )

    /** Words that mean "this spends money". */
    val paymentWords: List<String> = listOf(
        "pay", "payment", "buy", "purchase", "checkout", "subscribe", "order now", "confirm payment",
        // Arabic
        "دفع", "ادفع", "شراء", "اشتر", "اشتري", "الشراء",
    )

    /**
     * The effective capability of [action] performed in [context].
     *
     * Escalations:
     *  - a tap or press onto a payment word becomes `PAYMENT_AUTHORIZE`;
     *  - a tap or press onto a send word becomes `MESSAGE_SEND`;
     *  - typing into a password field becomes `CREDENTIAL_READ`.
     */
    fun resolve(action: Action, context: ActionContext): Capability {
        val base = action.capability

        if (action is Action.Type && context.targetIsPassword) {
            return Capability.CREDENTIAL_READ
        }

        val isPress = action is Action.Click ||
            action is Action.DoubleClick ||
            action is Action.LongPress
        if (!isPress) return base

        val labels = context.targetLabels
        if (labels.isEmpty()) return base

        if (labels.any { label -> paymentWords.any { label.contains(it) } }) {
            return Capability.PAYMENT_AUTHORIZE
        }
        if (labels.any { label -> sendWords.any { label.contains(it) } }) {
            return Capability.MESSAGE_SEND
        }
        return base
    }
}
