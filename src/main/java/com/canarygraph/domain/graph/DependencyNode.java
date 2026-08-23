package com.canarygraph.domain.graph;

import com.canarygraph.domain.common.DomainValidation;

import java.util.Objects;

public record DependencyNode(DependencyNodeId id, DependencyNodeType type, String label) {

    public DependencyNode {
        Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(type, "type must not be null");
        label = DomainValidation.requireNonBlank(label, "label");
    }
}

