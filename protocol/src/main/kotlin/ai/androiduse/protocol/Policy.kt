package ai.androiduse.protocol

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** What the local policy says about a capability. */
@Serializable
enum class PolicyVerdict {
    /** Run without asking. */
    ALLOW,

    /** Raise an approval request and wait for the user. */
    ASK,

    /** Refuse, whatever the relay asks for. */
    DENY,
}

/** How long an approval grant lasts. */
@Serializable
enum class ApprovalScope {
    /** This one action only. */
    ONCE,

    /** Every action of this capability until the run ends. */
    SESSION,

    /** Every action of this capability in this app, until the user revokes it. */
    ALWAYS_FOR_PACKAGE,
}

@Serializable
enum class ApprovalDecision {
    APPROVE_ONCE,
    APPROVE_SESSION,
    APPROVE_ALWAYS_FOR_PACKAGE,
    DENY,
    ;

    val scope: ApprovalScope?
        get() = when (this) {
            APPROVE_ONCE -> ApprovalScope.ONCE
            APPROVE_SESSION -> ApprovalScope.SESSION
            APPROVE_ALWAYS_FOR_PACKAGE -> ApprovalScope.ALWAYS_FOR_PACKAGE
            DENY -> null
        }
}

/**
 * The device's verdict for each capability.
 *
 * The device's copy is authoritative. The relay holds a mirror for
 * convenience; it can narrow this policy but never widen it.
 */
@Serializable
data class CapabilityPolicy(
    val verdicts: Map<Capability, PolicyVerdict> = emptyMap(),
) {
    fun verdictFor(capability: Capability): PolicyVerdict =
        verdicts[capability] ?: defaultVerdictFor(capability)

    /**
     * Combine with [other] so that the result is at least as restrictive as
     * both. `DENY` beats `ASK` beats `ALLOW`.
     */
    fun narrowedBy(other: CapabilityPolicy): CapabilityPolicy {
        val merged = mutableMapOf<Capability, PolicyVerdict>()
        for (capability in Capability.entries) {
            val a = verdictFor(capability)
            val b = other.verdictFor(capability)
            merged[capability] = when {
                a == PolicyVerdict.DENY || b == PolicyVerdict.DENY -> PolicyVerdict.DENY
                a == PolicyVerdict.ASK || b == PolicyVerdict.ASK -> PolicyVerdict.ASK
                else -> PolicyVerdict.ALLOW
            }
        }
        return CapabilityPolicy(merged)
    }

    companion object {
        /** Irreversible capabilities are denied; consequential ones are asked. */
        fun defaultVerdictFor(capability: Capability): PolicyVerdict = when (capability) {
            Capability.PAYMENT_AUTHORIZE,
            Capability.ACCOUNT_CHANGE,
            Capability.CREDENTIAL_READ,
            -> PolicyVerdict.DENY

            Capability.MESSAGE_SEND,
            Capability.CALL_PLACE,
            Capability.SETTINGS_WRITE,
            -> PolicyVerdict.ASK

            else -> PolicyVerdict.ALLOW
        }

        fun defaultPolicy(): CapabilityPolicy = CapabilityPolicy(
            Capability.entries.associateWith { defaultVerdictFor(it) },
        )

        /** The "Careful" preset: ask before anything consequential. */
        fun carefulPolicy(): CapabilityPolicy = CapabilityPolicy(
            Capability.entries.associateWith { capability ->
                when {
                    capability.isIrreversible -> PolicyVerdict.DENY
                    capability in consequentialCapabilities -> PolicyVerdict.ASK
                    else -> PolicyVerdict.ALLOW
                }
            },
        )

        /** The "Balanced" preset: ask only for messages, calls and settings. */
        fun balancedPolicy(): CapabilityPolicy = defaultPolicy()

        /** The "Trust" preset: ask only for the irreversible tier. */
        fun trustPolicy(): CapabilityPolicy = CapabilityPolicy(
            Capability.entries.associateWith { capability ->
                when {
                    capability.isIrreversible -> PolicyVerdict.DENY
                    else -> PolicyVerdict.ALLOW
                }
            },
        )

        private val consequentialCapabilities = setOf(
            Capability.MESSAGE_SEND,
            Capability.CALL_PLACE,
            Capability.SETTINGS_WRITE,
        )
    }
}

/** A request for the user to permit one action. */
@Serializable
data class ApprovalRequest(
    @SerialName("request_id") val requestId: String,
    val capability: Capability,
    @SerialName("app_package") val appPackage: String? = null,
    @SerialName("app_label") val appLabel: String? = null,
    /** What the agent wants to do, in plain language, in the user's language. */
    val summary: String,
    /** Why the agent wants to do it. */
    val reason: String,
)

/** The user's answer to an [ApprovalRequest]. */
@Serializable
data class ApprovalResponse(
    @SerialName("request_id") val requestId: String,
    val decision: ApprovalDecision,
    @SerialName("app_package") val appPackage: String? = null,
)
