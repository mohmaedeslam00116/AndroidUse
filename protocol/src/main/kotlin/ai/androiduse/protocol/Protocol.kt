package ai.androiduse.protocol

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

/**
 * The single codec both ends use.
 *
 * The polymorphic hierarchies are encoded with their **base** serializer, not
 * with a reified type parameter: encoding `Action.Click` directly would drop
 * the class discriminator and produce JSON the other end cannot read.
 *
 * `ignoreUnknownKeys` is deliberate: a newer relay must be able to talk to an
 * older app without the app crashing on a field it does not know.
 */
object Protocol {
    val json: Json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
        explicitNulls = false
    }

    // ---- Action -----------------------------------------------------------------------------

    fun encodeAction(action: Action): String = json.encodeToString(Action.serializer(), action)

    fun decodeAction(text: String): Action = json.decodeFromString(Action.serializer(), text)

    // ---- Outcome ---------------------------------------------------------------------------

    fun encodeOutcome(outcome: Outcome): String = json.encodeToString(Outcome.serializer(), outcome)

    fun decodeOutcome(text: String): Outcome = json.decodeFromString(Outcome.serializer(), text)

    // ---- Envelope --------------------------------------------------------------------------

    fun encodeDeviceMessage(message: DeviceMessage): String =
        json.encodeToString(DeviceMessage.serializer(), message)

    fun decodeDeviceMessage(text: String): DeviceMessage =
        json.decodeFromString(DeviceMessage.serializer(), text)

    fun encodeRelayMessage(message: RelayMessage): String =
        json.encodeToString(RelayMessage.serializer(), message)

    fun decodeRelayMessage(text: String): RelayMessage =
        json.decodeFromString(RelayMessage.serializer(), text)
}
