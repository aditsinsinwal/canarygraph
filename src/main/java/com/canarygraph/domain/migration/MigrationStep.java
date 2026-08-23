package com.canarygraph.domain.migration;

import com.canarygraph.domain.common.DomainValidation;
import com.canarygraph.domain.common.SourceRange;
import com.canarygraph.domain.repository.SourceFileId;

import java.util.Objects;
import java.util.Optional;

public record MigrationStep(
        int sequence,
        MigrationOperation operation,
        SourceFileId sourceFileId,
        SourceRange range,
        String description,
        Optional<String> replacement
) {

    public MigrationStep {
        if (sequence < 1) {
            throw new IllegalArgumentException("migration step sequence must be positive");
        }
        Objects.requireNonNull(operation, "operation must not be null");
        Objects.requireNonNull(sourceFileId, "sourceFileId must not be null");
        Objects.requireNonNull(range, "range must not be null");
        description = DomainValidation.requireNonBlank(description, "description");
        Objects.requireNonNull(replacement, "replacement must not be null");
    }
}

