package com.canarygraph.domain.compatibility;

import java.util.Objects;
import java.util.UUID;

public record FindingId(UUID value) {

    public FindingId {
        Objects.requireNonNull(value, "findingId must not be null");
    }

    public static FindingId newId() {
        return new FindingId(UUID.randomUUID());
    }

    @Override
    public String toString() {
        return value.toString();
    }
}

