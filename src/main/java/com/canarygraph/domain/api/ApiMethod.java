package com.canarygraph.domain.api;

import com.canarygraph.domain.common.QualifiedName;

import java.util.Objects;

public record ApiMethod(
        MethodSignature signature,
        Visibility visibility,
        boolean finalMethod,
        boolean abstractMethod
) implements ApiSymbol {

    public ApiMethod {
        Objects.requireNonNull(signature, "signature must not be null");
        Objects.requireNonNull(visibility, "visibility must not be null");
        if (finalMethod && abstractMethod) {
            throw new IllegalArgumentException("a method cannot be both final and abstract");
        }
    }

    @Override
    public SymbolId symbolId() {
        return signature.symbolId();
    }

    @Override
    public QualifiedName qualifiedName() {
        return new QualifiedName(signature.owner() + "." + signature.name());
    }

    @Override
    public SymbolKind kind() {
        return SymbolKind.METHOD;
    }
}

