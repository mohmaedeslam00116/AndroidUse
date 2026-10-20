package ai.androiduse.protocol

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonClassDiscriminator

/**
 * Where an [Action] is aimed.
 *
 * A target is exactly one of an element index (from the view tree) or a pixel
 * point (from the frame). It is never both and never neither — a target with
 * no destination is the main source of ambiguous failures, so the type
 * refuses to exist in that state.
 */
@Serializable
data class Target(
    @SerialName("element_index") val elementIndex: Int? = null,
    val x: Int? = null,
    val y: Int? = null,
) {
    init {
        val hasElement = elementIndex != null
        val hasX = x != null
        val hasY = y != null
        require(hasX == hasY) { "x and y must be provided together, or not at all" }
        val hasPoint = hasX && hasY
        require(hasElement != hasPoint) {
            "a target must be exactly one of element_index or (x, y); got elementIndex=$elementIndex x=$x y=$y"
        }
    }

    val isElement: Boolean get() = elementIndex != null

    companion object {
        fun element(index: Int): Target = Target(elementIndex = index)
        fun point(x: Int, y: Int): Target = Target(x = x, y = y)
    }
}

/**
 * The single action surface of AndroidUse.
 *
 * One tool, one discriminated union: the agent picks *what* to do and *where*
 * to do it, and never picks a tool name. See
 * `docs/adr/0004-native-computer-use-action-set.md`.
 */
/** The closed set of action kinds. This is the wire vocabulary the model sees. */
enum class ActionKind(val wireName: String) {
    SCREENSHOT("screenshot"),
    CLICK("click"),
    DOUBLE_CLICK("double_click"),
    LONG_PRESS("long_press"),
    DRAG("drag"),
    TYPE("type"),
    SCROLL("scroll"),
    PRESS_KEY("press_key"),
    OPEN_APP("open_app"),
    LIST_APPS("list_apps"),
    WAIT("wait"),
    FINISH("finish"),
    ASK_USER("ask_user"),
}

@Serializable
@JsonClassDiscriminator("action")
sealed interface Action {

    /** The kind of action, for the schema and for logs. */
    val kind: ActionKind

    /** The capability this action requires. Enforced by the device's policy. */
    val capability: Capability

    @Serializable
    @SerialName("screenshot")
    data object Screenshot : Action {
        override val kind: ActionKind get() = ActionKind.SCREENSHOT
        override val capability: Capability get() = Capability.SCREEN_READ
    }

    @Serializable
    @SerialName("click")
    data class Click(val target: Target) : Action {
        override val kind: ActionKind get() = ActionKind.CLICK
        override val capability: Capability get() = Capability.INPUT_TAP
    }

    @Serializable
    @SerialName("double_click")
    data class DoubleClick(val target: Target) : Action {
        override val kind: ActionKind get() = ActionKind.DOUBLE_CLICK
        override val capability: Capability get() = Capability.INPUT_TAP
    }

    @Serializable
    @SerialName("long_press")
    data class LongPress(val target: Target, val durationMs: Long = 600) : Action {
        override val kind: ActionKind get() = ActionKind.LONG_PRESS
        override val capability: Capability get() = Capability.INPUT_TAP
    }

    @Serializable
    @SerialName("drag")
    data class Drag(
        val from: Target,
        val to: Target,
        val durationMs: Long = 500,
    ) : Action {
        override val kind: ActionKind get() = ActionKind.DRAG
        override val capability: Capability get() = Capability.INPUT_GESTURE
    }

    @Serializable
    @SerialName("type")
    data class Type(val target: Target?, val text: String, val clear: Boolean = false) : Action {
        override val kind: ActionKind get() = ActionKind.TYPE
        override val capability: Capability get() = Capability.INPUT_TEXT
    }

    @Serializable
    @SerialName("scroll")
    data class Scroll(val target: Target?, val direction: Direction) : Action {
        override val kind: ActionKind get() = ActionKind.SCROLL
        override val capability: Capability get() = Capability.INPUT_GESTURE
    }

    @Serializable
    @SerialName("press_key")
    data class PressKey(val key: SystemKey) : Action {
        override val kind: ActionKind get() = ActionKind.PRESS_KEY
        override val capability: Capability get() = Capability.NAVIGATE_SYSTEM
    }

    @Serializable
    @SerialName("open_app")
    data class OpenApp(val packageName: String) : Action {
        override val kind: ActionKind get() = ActionKind.OPEN_APP
        override val capability: Capability get() = Capability.APP_LAUNCH
    }

    @Serializable
    @SerialName("list_apps")
    data object ListApps : Action {
        override val kind: ActionKind get() = ActionKind.LIST_APPS
        override val capability: Capability get() = Capability.APP_LIST
    }

    @Serializable
    @SerialName("wait")
    data class Wait(val durationMs: Long = 1000) : Action {
        override val kind: ActionKind get() = ActionKind.WAIT
        override val capability: Capability get() = Capability.SYSTEM_WAIT
    }

    @Serializable
    @SerialName("finish")
    data class Finish(val succeeded: Boolean, val message: String) : Action {
        override val kind: ActionKind get() = ActionKind.FINISH
        override val capability: Capability get() = Capability.TASK_COMPLETE
    }

    @Serializable
    @SerialName("ask_user")
    data class AskUser(val question: String) : Action {
        override val kind: ActionKind get() = ActionKind.ASK_USER
        override val capability: Capability get() = Capability.USER_QUESTION
    }
}

@Serializable
enum class Direction(val wireName: String) {
    UP("up"),
    DOWN("down"),
    LEFT("left"),
    RIGHT("right"),
}

@Serializable
enum class SystemKey {
    BACK,
    HOME,
    RECENTS,
    ENTER,
    ESCAPE,
    TAB,
    DELETE,
    MENU,
}
