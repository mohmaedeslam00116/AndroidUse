package ai.androiduse.protocol

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Bounds(
    val left: Int,
    val top: Int,
    val right: Int,
    val bottom: Int,
) {
    val centerX: Int get() = (left + right) / 2
    val centerY: Int get() = (top + bottom) / 2
}

@Serializable
data class Point(val x: Int, val y: Int)

/**
 * One node of the foreground app's view tree.
 *
 * [index] is the position in the rendered list the agent sees. It is only
 * valid for the perception that produced it.
 */
@Serializable
data class UiElement(
    val index: Int,
    val text: String? = null,
    @SerialName("content_description") val contentDescription: String? = null,
    @SerialName("resource_id") val resourceId: String? = null,
    @SerialName("class_name") val className: String? = null,
    val bounds: Bounds? = null,
    val center: Point? = null,
    val clickable: Boolean = false,
    val editable: Boolean = false,
    val scrollable: Boolean = false,
    val focused: Boolean = false,
    val checked: Boolean = false,
    val password: Boolean = false,
)

/** A screenshot of the real display, produced by MediaProjection. */
@Serializable
data class Frame(
    @SerialName("media_type") val mediaType: String = "image/jpeg",
    val base64: String,
    val width: Int,
    val height: Int,
)

/**
 * Everything the device could see at one step.
 *
 * [frame] and [tree] are complementary, not redundant: the frame is what the
 * agent looks at, the tree is what it grounds against. Either may be absent,
 * and [limitations] records why.
 */
@Serializable
data class Perception(
    val frame: Frame? = null,
    val tree: List<UiElement> = emptyList(),
    @SerialName("foreground_package") val foregroundPackage: String? = null,
    @SerialName("screen_width_px") val screenWidthPx: Int = 0,
    @SerialName("screen_height_px") val screenHeightPx: Int = 0,
    val fingerprint: String? = null,
    val limitations: List<String> = emptyList(),
)
