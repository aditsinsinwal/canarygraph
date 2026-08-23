package com.canarygraph.domain.graph;

import com.canarygraph.domain.common.DomainValidation;

public record DependencyNodeId(String value) implements Comparable<DependencyNodeId> {

    public DependencyNodeId {
        value = DomainValidation.requireNonBlank(value, "dependencyNodeId");
    }

    @Override
    public int compareTo(DependencyNodeId other) {
        return value.compareTo(other.value);
    }

    @Override
    public String toString() {
        return value;
    }
}

