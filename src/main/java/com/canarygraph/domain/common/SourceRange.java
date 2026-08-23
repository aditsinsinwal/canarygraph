package com.canarygraph.domain.common;

import java.util.Objects;

public record SourceRange(SourcePosition start, SourcePosition end) implements Comparable<SourceRange> {

    public SourceRange {
        Objects.requireNonNull(start, "start must not be null");
        Objects.requireNonNull(end, "end must not be null");
        if (start.compareTo(end) > 0) {
            throw new IllegalArgumentException("source range start must not be after end");
        }
    }

    public boolean overlaps(SourceRange other) {
        Objects.requireNonNull(other, "other must not be null");
        return start.compareTo(other.end) <= 0 && other.start.compareTo(end) <= 0;
    }

    @Override
    public int compareTo(SourceRange other) {
        int byStart = start.compareTo(other.start);
        return byStart != 0 ? byStart : end.compareTo(other.end);
    }
}

