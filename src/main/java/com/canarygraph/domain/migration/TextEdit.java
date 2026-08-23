package com.canarygraph.domain.migration;

import com.canarygraph.domain.common.SourceRange;

import java.util.Objects;

public record TextEdit(SourceRange range, String replacement) implements Comparable<TextEdit> {

    public TextEdit {
        Objects.requireNonNull(range, "range must not be null");
        Objects.requireNonNull(replacement, "replacement must not be null");
    }

    @Override
    public int compareTo(TextEdit other) {
        return range.compareTo(other.range);
    }
}

