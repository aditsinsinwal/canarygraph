package com.canarygraph.domain.api;

import com.canarygraph.domain.common.QualifiedName;

public sealed interface ApiSymbol permits ApiClass, ApiMethod {

    SymbolId symbolId();

    QualifiedName qualifiedName();

    Visibility visibility();

    SymbolKind kind();
}

