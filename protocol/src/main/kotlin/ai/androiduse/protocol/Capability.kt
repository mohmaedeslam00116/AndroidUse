package ai.androiduse.protocol

/**
 * The security-relevant class of an [Action].
 *
 * Approval policy is written against capabilities, not against package names or
 * tool names. See `docs/adr/0003-capability-based-approval.md`.
 */
enum class Capability {
    /** Observing the screen: frames and the view tree. */
    SCREEN_READ,

    /** Touching the screen without producing text. */
    INPUT_TAP,

    /** Producing text in a field. */
    INPUT_TEXT,

    /** Swipes and drags. */
    INPUT_GESTURE,

    /** Starting an application. */
    APP_LAUNCH,

    /** Enumerating installed applications. */
    APP_LIST,

    /** System-level navigation: back, home, recents. */
    NAVIGATE_SYSTEM,

    /** Idling. */
    SYSTEM_WAIT,

    /** Sending a message to a person. */
    MESSAGE_SEND,

    /** Placing a call. */
    CALL_PLACE,

    /** Changing a device or app setting. */
    SETTINGS_WRITE,

    /** Authorising a payment. */
    PAYMENT_AUTHORIZE,

    /** Changing an account, or adding/removing a credential. */
    ACCOUNT_CHANGE,

    /** Reading a credential. */
    CREDENTIAL_READ,

    /** Asking the user a question. */
    USER_QUESTION,

    /** Reporting the outcome of the run. */
    TASK_COMPLETE,
    ;

    /**
     * True when performing this capability can move money, change an account,
     * or disclose a secret. These are denied by default and are not
     * overridable by a per-run approval.
     */
    val isIrreversible: Boolean
        get() = this == PAYMENT_AUTHORIZE ||
            this == ACCOUNT_CHANGE ||
            this == CREDENTIAL_READ
}
