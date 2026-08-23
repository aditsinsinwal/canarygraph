package com.canarygraph.domain.common;

import java.nio.file.Path;
import java.util.Objects;

public record SourcePath(Path value) implements Comparable<SourcePath> {

    public SourcePath {
        Objects.requireNonNull(value, "sourcePath must not be null");
        if (value.toString().isBlank()) {
            throw new IllegalArgumentException("sourcePath must not be blank");
        }
        if (value.isAbsolute()) {
            throw new IllegalArgumentException("sourcePath must be relative to the repository root");
        }
        Path normalized = value.normalize();
        if (normalized.startsWith("..")) {
            throw new IllegalArgumentException("sourcePath must not escape the repository root");
        }
        value = normalized;
    }

    public static SourcePath of(String value) {
        return new SourcePath(Path.of(DomainValidation.requireNonBlank(value, "sourcePath")));
    }

    @Override
    public int compareTo(SourcePath other) {
        return value.toString().compareTo(other.value.toString());
    }

    @Override
    public String toString() {
        return value.toString();
    }
}

