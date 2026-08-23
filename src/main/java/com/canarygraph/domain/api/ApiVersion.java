package com.canarygraph.domain.api;

import com.canarygraph.domain.common.DomainValidation;
import com.canarygraph.domain.common.VersionNumber;

import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

public record ApiVersion(ApiLibrary library, VersionNumber version, List<ApiSymbol> symbols) {

    public ApiVersion {
        Objects.requireNonNull(library, "library must not be null");
        Objects.requireNonNull(version, "version must not be null");
        symbols = DomainValidation.immutableList(symbols, "symbols");
        Set<SymbolId> seen = new HashSet<>();
        for (ApiSymbol symbol : symbols) {
            if (!seen.add(symbol.symbolId())) {
                throw new IllegalArgumentException("duplicate API symbol: " + symbol.symbolId());
            }
        }
    }
}

