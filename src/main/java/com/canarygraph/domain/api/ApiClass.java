package com.canarygraph.domain.api;

import com.canarygraph.domain.common.QualifiedName;

import java.util.Objects;

public record ApiClass(
        QualifiedName qualifiedName,
        Visibility visibility,
        ClassKind classKind,
        boolean finalType
) implements ApiSymbol {

    public ApiClass {
        Objects.requireNonNull(qualifiedName, "qualifiedName must not be null");
        Objects.requireNonNull(visibility, "visibility must not be null");
        Objects.requireNonNull(classKind, "classKind must not be null");
    }

    @Override
    public SymbolId symbolId() {
        return new SymbolId("CLASS:" + qualifiedName);
    }

    @Override
    public SymbolKind kind() {
        return SymbolKind.CLASS;
    }
}

