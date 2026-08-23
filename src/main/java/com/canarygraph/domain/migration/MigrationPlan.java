package com.canarygraph.domain.migration;

import com.canarygraph.domain.common.DomainValidation;
import com.canarygraph.domain.compatibility.FindingId;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public record MigrationPlan(
        MigrationPlanId id,
        FindingId findingId,
        MigrationPlanStatus status,
        List<MigrationStep> steps,
        String explanation
) {

    public MigrationPlan {
        Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(findingId, "findingId must not be null");
        Objects.requireNonNull(status, "status must not be null");
        steps = new ArrayList<>(DomainValidation.immutableList(steps, "steps"));
        steps.sort((left, right) -> Integer.compare(left.sequence(), right.sequence()));
        steps = List.copyOf(steps);
        explanation = DomainValidation.requireNonBlank(explanation, "explanation");

        for (int index = 0; index < steps.size(); index++) {
            if (steps.get(index).sequence() != index + 1) {
                throw new IllegalArgumentException("migration step sequences must be contiguous from one");
            }
        }
        if (status == MigrationPlanStatus.READY) {
            if (steps.isEmpty()) {
                throw new IllegalArgumentException("a ready migration plan must have steps");
            }
            if (steps.stream().anyMatch(step -> step.replacement().isEmpty())) {
                throw new IllegalArgumentException("every ready migration step must have a replacement");
            }
        }
    }
}
