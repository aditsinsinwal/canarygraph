package com.canarygraph.domain.common;

public record SourcePosition(int line, int column) implements Comparable<SourcePosition> {

    public SourcePosition {
        if (line < 1) {
            throw new IllegalArgumentException("line must be positive");
        }
        if (column < 1) {
            throw new IllegalArgumentException("column must be positive");
        }
    }

    @Override
    public int compareTo(SourcePosition other) {
        int byLine = Integer.compare(line, other.line);
        return byLine != 0 ? byLine : Integer.compare(column, other.column);
    }
}

