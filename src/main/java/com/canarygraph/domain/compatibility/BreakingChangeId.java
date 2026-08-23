package com.canarygraph.domain.compatibility;

import java.util.Objects;
import java.util.UUID;

public record BreakingChangeId(UUID value) {

    public BreakingChangeId {
        Objects.requireNonNull(value, "breakingChangeId must not be null");
    }

    public static BreakingChangeId newId() {
        return new BreakingChangeId(UUID.randomUUID());
    }

    @Override
    public String toString() {
        return value.toString();
    }
}

