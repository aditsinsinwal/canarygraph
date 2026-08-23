package com.canarygraph.domain.api;

import com.canarygraph.domain.common.DomainValidation;

public record SymbolId(String value) implements Comparable<SymbolId> {

    public SymbolId {
        value = DomainValidation.requireNonBlank(value, "symbolId");
    }

    @Override
    public int compareTo(SymbolId other) {
        return value.compareTo(other.value);
    }

    @Override
    public String toString() {
        return value;
    }
}

