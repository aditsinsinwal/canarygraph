package com.canarygraph.domain.migration;

import com.canarygraph.domain.common.DomainValidation;

import java.time.Duration;
import java.util.Objects;

public record ValidationCheck(
        ValidationStage stage,
        ValidationCheckStatus status,
        Duration duration,
        String summary
) {

    public ValidationCheck {
        Objects.requireNonNull(stage, "stage must not be null");
        Objects.requireNonNull(status, "status must not be null");
        Objects.requireNonNull(duration, "duration must not be null");
        if (duration.isNegative()) {
            throw new IllegalArgumentException("validation duration must not be negative");
        }
        summary = DomainValidation.requireNonBlank(summary, "summary");
    }
}

