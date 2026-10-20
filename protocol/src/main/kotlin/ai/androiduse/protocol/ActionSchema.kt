package ai.androiduse.protocol

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray
import kotlinx.serialization.json.putJsonObject

/**
 * The JSON Schema of the action surface, handed to the model verbatim.
 *
 * It is written by hand rather than generated so that the description the
 * model reads is the description we want it to read, in both languages.
 */
object ActionSchema {

    /** The schema for the whole `act` tool, including its parameters. */
    fun toolSchema(language: RunLanguage): JsonObject = buildJsonObject {
        put("type", "function")
        putJsonObject("function") {
            put("name", "act")
            put(
                "description",
                when (language) {
                    RunLanguage.ARABIC ->
                        "نفّذ إجراءً واحدًا على الهاتف. اختر الإجراء، ثم اختر الهدف " +
                            "(فهرس عنصر من شجرة الواجهة، أو إحداثيات نقطة)."
                    RunLanguage.ENGLISH ->
                        "Perform exactly one action on the phone. Choose the action, then the " +
                            "target (an element index from the view tree, or a pixel point)."
                },
            )
            putJsonObject("parameters") {
                put("type", "object")
                putJsonArray("required") { add(JsonPrimitive("action")) }
                putJsonObject("properties") {
                    putJsonObject("action") {
                        put("type", "string")
                        put(
                            "description",
                            when (language) {
                                RunLanguage.ARABIC -> "نوع الإجراء المطلوب."
                                RunLanguage.ENGLISH -> "The kind of action to perform."
                            },
                        )
                        putJsonArray("enum") {
                            ActionKind.entries.forEach { add(JsonPrimitive(it.wireName)) }
                        }
                    }
                    putJsonObject("target") { targetSchema(language) }
                    putJsonObject("from") { targetSchema(language) }
                    putJsonObject("to") { targetSchema(language) }
                    putJsonObject("text") {
                        put("type", "string")
                        put(
                            "description",
                            when (language) {
                                RunLanguage.ARABIC -> "النص المراد كتابته (للإجراء type فقط)."
                                RunLanguage.ENGLISH -> "The text to type (type action only)."
                            },
                        )
                    }
                    putJsonObject("direction") {
                        put("type", "string")
                        putJsonArray("enum") {
                            Direction.entries.forEach { add(JsonPrimitive(it.wireName)) }
                        }
                    }
                    putJsonObject("duration_ms") {
                        put("type", "integer")
                        put("description", "Hold or gesture duration in milliseconds.")
                    }
                    putJsonObject("package_name") {
                        put("type", "string")
                        put("description", "Package name of the app to open.")
                    }
                    putJsonObject("message") {
                        put("type", "string")
                        put("description", "The final answer, or the question to ask the user.")
                    }
                    putJsonObject("succeeded") {
                        put("type", "boolean")
                        put("description", "Whether the task succeeded (finish action only).")
                    }
                }
                put("additionalProperties", false)
            }
        }
    }

    private fun kotlinx.serialization.json.JsonObjectBuilder.targetSchema(language: RunLanguage) {
        put("type", "object")
        put(
            "description",
            when (language) {
                RunLanguage.ARABIC ->
                    "الهدف: فهرس عنصر واحد (element_index) أو نقطة واحدة (x و y)."
                RunLanguage.ENGLISH ->
                    "The target: exactly one element index (element_index) or one point (x and y)."
            },
        )
        putJsonObject("properties") {
            putJsonObject("element_index") {
                put("type", "integer")
                put(
                    "description",
                    when (language) {
                        RunLanguage.ARABIC -> "فهرس العنصر من شجرة الواجهة في آخر إدراك."
                        RunLanguage.ENGLISH -> "The element index from the latest view tree."
                    },
                )
            }
            putJsonObject("x") { put("type", "integer") }
            putJsonObject("y") { put("type", "integer") }
        }
        put("additionalProperties", false)
    }
}
