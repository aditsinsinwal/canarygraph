package com.canarygraph.domain.repository;

import java.util.Objects;
import java.util.UUID;

public record RepositoryId(UUID value) {

    public RepositoryId {
        Objects.requireNonNull(value, "repositoryId must not be null");
    }

    public static RepositoryId newId() {
        return new RepositoryId(UUID.randomUUID());
    }

    @Override
    public String toString() {
        return value.toString();
    }
}

