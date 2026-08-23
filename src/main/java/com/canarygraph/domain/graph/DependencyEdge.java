package com.canarygraph.domain.graph;

import java.util.Objects;

public record DependencyEdge(
        DependencyNodeId from,
        DependencyNodeId to,
        DependencyRelation relation
) {

    public DependencyEdge {
        Objects.requireNonNull(from, "from must not be null");
        Objects.requireNonNull(to, "to must not be null");
        Objects.requireNonNull(relation, "relation must not be null");
        if (from.equals(to)) {
            throw new IllegalArgumentException("dependency edges cannot be self-referential");
        }
    }
}

