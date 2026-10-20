package ai.androiduse.protocol

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonClassDiscriminator

/**
 * The typed result of executing one [Action].
 *
 * Outcomes are structural, never prose. The agent receives one of these and
 * must not have to infer status from English words.
 */
@Serializable
@JsonClassDiscriminator("status")
sealed interface Outcome {

    /** The action ran and the screen changed. */
    @Serializable
    @SerialName("ok")
    data class Ok(val detail: String? = null) : Outcome

    /** The action ran but the screen did not change. */
    @Serializable
    @SerialName("unchanged")
    data class Unchanged(val detail: String? = null) : Outcome

    /** The addressed element no longer exists, or no longer matches. */
    @Serializable
    @SerialName("stale_element")
    data class StaleElement(val requestedIndex: Int?, val detail: String? = null) : Outcome

    /** The local policy refused the action. */
    @Serializable
    @SerialName("denied")
    data class Denied(val capability: Capability, val reason: String) : Outcome

    /** The action did not complete in time. */
    @Serializable
    @SerialName("timeout")
    data class Timeout(val afterMs: Long) : Outcome

    /** The action is not available on this device or in this app. */
    @Serializable
    @SerialName("unsupported")
    data class Unsupported(val detail: String) : Outcome

    /** The action failed for a reason the device could not classify. */
    @Serializable
    @SerialName("failed")
    data class Failed(val reason: String) : Outcome
}

/** True when the outcome means "the agent should try something else". */
val Outcome.isFailure: Boolean
    get() = this is Outcome.Unchanged ||
        this is Outcome.StaleElement ||
        this is Outcome.Denied ||
        this is Outcome.Timeout ||
        this is Outcome.Unsupported ||
        this is Outcome.Failed

/** A short, language-neutral summary, for logs and for the transcript. */
val Outcome.label: String
    get() = when (this) {
        is Outcome.Ok -> "ok"
        is Outcome.Unchanged -> "unchanged"
        is Outcome.StaleElement -> "stale_element"
        is Outcome.Denied -> "denied"
        is Outcome.Timeout -> "timeout"
        is Outcome.Unsupported -> "unsupported"
        is Outcome.Failed -> "failed"
    }
