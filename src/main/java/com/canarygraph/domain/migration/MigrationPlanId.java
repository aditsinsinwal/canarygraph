package com.canarygraph.domain.migration;

import java.util.Objects;
import java.util.UUID;

public record MigrationPlanId(UUID value) {

    public MigrationPlanId {
        Objects.requireNonNull(value, "migrationPlanId must not be null");
    }

    public static MigrationPlanId newId() {
        return new MigrationPlanId(UUID.randomUUID());
    }

    @Override
    public String toString() {
        return value.toString();
    }
}

