package com.canarygraph.domain.migration;

import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ValidationResultTest {

    @Test
    void acceptsValidatedOnlyWhenEveryStagePassed() {
        ValidationResult result = new ValidationResult(
                MigrationPlanId.newId(),
                Optional.of(MigrationPatchId.newId()),
                MigrationOutcome.VALIDATED,
                List.of(
                        passed(ValidationStage.PARSE),
                        passed(ValidationStage.COMPILE),
                        passed(ValidationStage.TEST)
                ),
                Instant.parse("2026-08-14T12:00:00Z"),
                Duration.ofSeconds(3)
        );

        assertThat(result.outcome()).isEqualTo(MigrationOutcome.VALIDATED);
    }

    @Test
    void storesChecksInPipelineOrder() {
        ValidationCheck tests = passed(ValidationStage.TEST);
        ValidationCheck parse = passed(ValidationStage.PARSE);
        ValidationCheck compile = passed(ValidationStage.COMPILE);

        ValidationResult result = new ValidationResult(
                MigrationPlanId.newId(),
                Optional.of(MigrationPatchId.newId()),
                MigrationOutcome.VALIDATED,
                List.of(tests, parse, compile),
                Instant.parse("2026-08-14T12:00:00Z"),
                Duration.ofSeconds(3)
        );

        assertThat(result.checks()).containsExactly(parse, compile, tests);
    }

    @Test
    void rejectsCompileFailureThatClaimsTestsPassed() {
        assertThatThrownBy(() -> new ValidationResult(
                MigrationPlanId.newId(),
                Optional.of(MigrationPatchId.newId()),
                MigrationOutcome.COMPILE_FAILED,
                List.of(
                        passed(ValidationStage.PARSE),
                        new ValidationCheck(
                                ValidationStage.COMPILE,
                                ValidationCheckStatus.FAILED,
                                Duration.ofSeconds(1),
                                "Compiler returned a non-zero exit code"
                        ),
                        passed(ValidationStage.TEST)
                ),
                Instant.parse("2026-08-14T12:00:00Z"),
                Duration.ofSeconds(2)
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("tests cannot pass");
    }

    @Test
    void reviewRequiredHasNoGeneratedPatchOrValidationChecks() {
        ValidationResult result = new ValidationResult(
                MigrationPlanId.newId(),
                Optional.empty(),
                MigrationOutcome.REVIEW_REQUIRED,
                List.of(),
                Instant.parse("2026-08-14T12:00:00Z"),
                Duration.ZERO
        );

        assertThat(result.patchId()).isEmpty();
        assertThat(result.checks()).isEmpty();
    }

    private ValidationCheck passed(ValidationStage stage) {
        return new ValidationCheck(
                stage,
                ValidationCheckStatus.PASSED,
                Duration.ofMillis(250),
                stage + " completed"
        );
    }
}
