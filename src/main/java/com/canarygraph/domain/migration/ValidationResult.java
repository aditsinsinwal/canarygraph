package com.canarygraph.domain.migration;

import com.canarygraph.domain.common.DomainValidation;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

public record ValidationResult(
        MigrationPlanId planId,
        Optional<MigrationPatchId> patchId,
        MigrationOutcome outcome,
        List<ValidationCheck> checks,
        Instant completedAt,
        Duration totalDuration
) {

    public ValidationResult {
        Objects.requireNonNull(planId, "planId must not be null");
        Objects.requireNonNull(patchId, "patchId must not be null");
        Objects.requireNonNull(outcome, "outcome must not be null");
        checks = new ArrayList<>(DomainValidation.immutableList(checks, "checks"));
        checks.sort((left, right) -> left.stage().compareTo(right.stage()));
        checks = List.copyOf(checks);
        Objects.requireNonNull(completedAt, "completedAt must not be null");
        Objects.requireNonNull(totalDuration, "totalDuration must not be null");
        if (totalDuration.isNegative()) {
            throw new IllegalArgumentException("total validation duration must not be negative");
        }

        Map<ValidationStage, ValidationCheckStatus> statusByStage = new EnumMap<>(ValidationStage.class);
        for (ValidationCheck check : checks) {
            if (statusByStage.put(check.stage(), check.status()) != null) {
                throw new IllegalArgumentException("validation stages must not be repeated");
            }
        }
        validateOutcome(outcome, patchId, statusByStage);
    }

    private static void validateOutcome(
            MigrationOutcome outcome,
            Optional<MigrationPatchId> patchId,
            Map<ValidationStage, ValidationCheckStatus> statuses
    ) {
        switch (outcome) {
            case VALIDATED -> {
                requirePatch(patchId, outcome);
                requireStatus(statuses, ValidationStage.PARSE, ValidationCheckStatus.PASSED, outcome);
                requireStatus(statuses, ValidationStage.COMPILE, ValidationCheckStatus.PASSED, outcome);
                requireStatus(statuses, ValidationStage.TEST, ValidationCheckStatus.PASSED, outcome);
            }
            case COMPILE_FAILED -> {
                requirePatch(patchId, outcome);
                requireStatus(statuses, ValidationStage.PARSE, ValidationCheckStatus.PASSED, outcome);
                requireStatus(statuses, ValidationStage.COMPILE, ValidationCheckStatus.FAILED, outcome);
                if (statuses.get(ValidationStage.TEST) == ValidationCheckStatus.PASSED) {
                    throw new IllegalArgumentException("tests cannot pass after compilation failed");
                }
            }
            case TEST_FAILED -> {
                requirePatch(patchId, outcome);
                requireStatus(statuses, ValidationStage.PARSE, ValidationCheckStatus.PASSED, outcome);
                requireStatus(statuses, ValidationStage.COMPILE, ValidationCheckStatus.PASSED, outcome);
                requireStatus(statuses, ValidationStage.TEST, ValidationCheckStatus.FAILED, outcome);
            }
            case REVIEW_REQUIRED -> {
                if (patchId.isPresent() || !statuses.isEmpty()) {
                    throw new IllegalArgumentException("review-required plans have not entered validation");
                }
            }
            case UNSUPPORTED -> {
                // Unsupported can be decided before generation or after a failed parse check.
            }
        }
    }

    private static void requirePatch(Optional<MigrationPatchId> patchId, MigrationOutcome outcome) {
        if (patchId.isEmpty()) {
            throw new IllegalArgumentException(outcome + " requires a generated patch");
        }
    }

    private static void requireStatus(
            Map<ValidationStage, ValidationCheckStatus> statuses,
            ValidationStage stage,
            ValidationCheckStatus expected,
            MigrationOutcome outcome
    ) {
        if (statuses.get(stage) != expected) {
            throw new IllegalArgumentException(outcome + " requires " + stage + " to be " + expected);
        }
    }
}
