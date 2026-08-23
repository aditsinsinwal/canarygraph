package com.canarygraph.domain.migration;

import com.canarygraph.domain.common.SourcePosition;
import com.canarygraph.domain.common.SourceRange;
import com.canarygraph.domain.compatibility.FindingId;
import com.canarygraph.domain.repository.SourceFileId;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class MigrationPlanTest {

    @Test
    void representsAnUnknownSemanticArgumentAsReviewRequired() {
        MigrationPlan plan = new MigrationPlan(
                MigrationPlanId.newId(),
                FindingId.newId(),
                MigrationPlanStatus.REVIEW_REQUIRED,
                List.of(step(Optional.empty())),
                "The new currency argument cannot be derived safely"
        );

        assertThat(plan.status()).isEqualTo(MigrationPlanStatus.REVIEW_REQUIRED);
        assertThat(plan.steps().getFirst().replacement()).isEmpty();
    }

    @Test
    void rejectsAReadyStepWithoutAConcreteReplacement() {
        assertThatThrownBy(() -> new MigrationPlan(
                MigrationPlanId.newId(),
                FindingId.newId(),
                MigrationPlanStatus.READY,
                List.of(step(Optional.empty())),
                "Rename is deterministic"
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("must have a replacement");
    }

    @Test
    void rejectsNonContiguousStepSequences() {
        MigrationStep secondStep = new MigrationStep(
                2,
                MigrationOperation.RENAME_METHOD,
                SourceFileId.newId(),
                new SourceRange(new SourcePosition(4, 1), new SourcePosition(4, 5)),
                "Rename the method",
                Optional.of("newName")
        );

        assertThatThrownBy(() -> new MigrationPlan(
                MigrationPlanId.newId(),
                FindingId.newId(),
                MigrationPlanStatus.READY,
                List.of(secondStep),
                "Rename is deterministic"
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("contiguous from one");
    }

    private MigrationStep step(Optional<String> replacement) {
        return new MigrationStep(
                1,
                MigrationOperation.REPLACE_ARGUMENTS,
                SourceFileId.newId(),
                new SourceRange(new SourcePosition(10, 9), new SourcePosition(10, 26)),
                "Add the required currency argument",
                replacement
        );
    }
}
