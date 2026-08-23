package com.canarygraph.domain.migration;

import java.util.Objects;
import java.util.UUID;

public record MigrationPatchId(UUID value) {

    public MigrationPatchId {
        Objects.requireNonNull(value, "migrationPatchId must not be null");
    }

    public static MigrationPatchId newId() {
        return new MigrationPatchId(UUID.randomUUID());
    }

    @Override
    public String toString() {
        return value.toString();
    }
}

