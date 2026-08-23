package com.canarygraph.domain.usage;

import java.util.Objects;
import java.util.UUID;

public record ApiUsageId(UUID value) {

    public ApiUsageId {
        Objects.requireNonNull(value, "apiUsageId must not be null");
    }

    public static ApiUsageId newId() {
        return new ApiUsageId(UUID.randomUUID());
    }

    @Override
    public String toString() {
        return value.toString();
    }
}

