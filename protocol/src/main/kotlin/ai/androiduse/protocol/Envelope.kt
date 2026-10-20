package ai.androiduse.protocol

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonClassDiscriminator

/** How a run ended. */
@Serializable
enum class RunStatus {
    SUCCEEDED,
    FAILED,
    BLOCKED,
    ABORTED,
    BUDGET_EXHAUSTED,
}

/** The language a run is conducted in. */
@Serializable
enum class RunLanguage {
    ENGLISH,
    ARABIC,
    ;

    companion object {
        /** Guess from a BCP-47 tag, defaulting to English. */
        fun ofTag(tag: String?): RunLanguage {
            val lower = tag?.lowercase().orEmpty()
            return if (lower.startsWith("ar")) ARABIC else ENGLISH
        }
    }
}

/** A message sent by the device to the relay. */
@Serializable
@JsonClassDiscriminator("type")
sealed interface DeviceMessage {

    @Serializable
    @SerialName("hello")
    data class Hello(
        @SerialName("device_id") val deviceId: String,
        @SerialName("app_version") val appVersion: String,
        @SerialName("device_language") val deviceLanguage: RunLanguage,
        @SerialName("local_policy") val localPolicy: CapabilityPolicy,
    ) : DeviceMessage

    @Serializable
    @SerialName("perception")
    data class PerceptionMessage(
        val step: Int,
        val perception: Perception,
    ) : DeviceMessage

    @Serializable
    @SerialName("outcome")
    data class OutcomeMessage(
        val step: Int,
        val outcome: Outcome,
    ) : DeviceMessage

    @Serializable
    @SerialName("approval_response")
    data class ApprovalResponseMessage(
        val response: ApprovalResponse,
    ) : DeviceMessage

    @Serializable
    @SerialName("run_state")
    data class RunState(
        val step: Int,
        val elapsedMs: Long,
        @SerialName("spend_usd") val spendUsd: Double,
        val status: RunStatus? = null,
        val note: String? = null,
    ) : DeviceMessage

    @Serializable
    @SerialName("error")
    data class ErrorMessage(
        val step: Int? = null,
        val reason: String,
    ) : DeviceMessage
}

/** A message sent by the relay to the device. */
@Serializable
@JsonClassDiscriminator("type")
sealed interface RelayMessage {

    @Serializable
    @SerialName("run_start")
    data class RunStart(
        @SerialName("run_id") val runId: String,
        val goal: String,
        val language: RunLanguage,
        val budget: RunBudget,
        /** The relay's mirror of the local policy. Narrowing only. */
        @SerialName("policy_mirror") val policyMirror: CapabilityPolicy = CapabilityPolicy(),
    ) : RelayMessage

    @Serializable
    @SerialName("act")
    data class Act(
        val step: Int,
        val action: Action,
    ) : RelayMessage

    @Serializable
    @SerialName("approval_request")
    data class ApprovalRequestMessage(
        val request: ApprovalRequest,
    ) : RelayMessage

    @Serializable
    @SerialName("run_end")
    data class RunEnd(
        @SerialName("run_id") val runId: String,
        val status: RunStatus,
        val message: String,
        @SerialName("bound") val bound: BudgetBound? = null,
    ) : RelayMessage

    /** A narrowing of the local policy. The device ignores any widening. */
    @Serializable
    @SerialName("policy_update")
    data class PolicyUpdate(
        val policy: CapabilityPolicy,
    ) : RelayMessage

    @Serializable
    @SerialName("ping")
    data object Ping : RelayMessage
}
