package ai.androiduse.protocol

import kotlinx.serialization.Serializable

/**
 * The hard ceilings on a run.
 *
 * The relay enforces this authoritatively. The device enforces a defensive
 * subset, so a compromised relay cannot drive an unbounded session.
 * See `docs/adr/0006-run-budgets.md`.
 */
@Serializable
data class RunBudget(
    val maxSteps: Int = 40,
    val maxDurationMs: Long = 10 * 60 * 1000,
    val maxSpendUsd: Double = 0.50,
    val maxCostPerStepUsd: Double = 0.05,
) {
    init {
        require(maxSteps > 0) { "maxSteps must be positive" }
        require(maxDurationMs > 0) { "maxDurationMs must be positive" }
        require(maxSpendUsd > 0) { "maxSpendUsd must be positive" }
        require(maxCostPerStepUsd > 0) { "maxCostPerStepUsd must be positive" }
    }

    /** The tighter of this budget and the device's defensive subset. */
    fun intersect(other: RunBudget): RunBudget = RunBudget(
        maxSteps = minOf(maxSteps, other.maxSteps),
        maxDurationMs = minOf(maxDurationMs, other.maxDurationMs),
        maxSpendUsd = minOf(maxSpendUsd, other.maxSpendUsd),
        maxCostPerStepUsd = minOf(maxCostPerStepUsd, other.maxCostPerStepUsd),
    )

    companion object {
        /**
         * The subset the device enforces on its own. It cannot know the spend,
         * so it does not pretend to.
         */
        fun deviceDefensiveSubset(): RunBudget = RunBudget(
            maxSteps = 40,
            maxDurationMs = 10 * 60 * 1000,
            maxSpendUsd = 0.50,
            maxCostPerStepUsd = 0.05,
        )
    }
}

/** Which bound stopped a run. */
@Serializable
enum class BudgetBound {
    STEPS,
    DURATION,
    SPEND,
    COST_PER_STEP,
    COMPACTION,
    LOOP,
    ;

    val messageKey: String get() = "budget_exhausted.$name"
}
