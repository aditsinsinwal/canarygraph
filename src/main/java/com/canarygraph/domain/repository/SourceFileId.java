package com.canarygraph.domain.repository;

import java.util.Objects;
import java.util.UUID;

public record SourceFileId(UUID value) {

    public SourceFileId {
        Objects.requireNonNull(value, "sourceFileId must not be null");
    }

    public static SourceFileId newId() {
        return new SourceFileId(UUID.randomUUID());
    }

    @Override
    public String toString() {
        return value.toString();
    }
}

