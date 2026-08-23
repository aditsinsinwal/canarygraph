package com.canarygraph.domain.api;

import com.canarygraph.domain.common.DomainValidation;

public record LibraryCoordinate(String groupId, String artifactId) implements Comparable<LibraryCoordinate> {

    public LibraryCoordinate {
        groupId = DomainValidation.requireNonBlank(groupId, "groupId");
        artifactId = DomainValidation.requireNonBlank(artifactId, "artifactId");
    }

    @Override
    public int compareTo(LibraryCoordinate other) {
        int byGroup = groupId.compareTo(other.groupId);
        return byGroup != 0 ? byGroup : artifactId.compareTo(other.artifactId);
    }

    @Override
    public String toString() {
        return groupId + ":" + artifactId;
    }
}

