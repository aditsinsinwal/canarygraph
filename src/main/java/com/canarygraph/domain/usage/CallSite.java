package com.canarygraph.domain.usage;

import com.canarygraph.domain.api.MethodSignature;
import com.canarygraph.domain.common.QualifiedName;
import com.canarygraph.domain.common.SourceRange;
import com.canarygraph.domain.repository.SourceFileId;

import java.util.Objects;
import java.util.Optional;

public record CallSite(
        SourceFileId sourceFileId,
        QualifiedName enclosingClass,
        Optional<MethodSignature> enclosingMethod,
        SourceRange range
) {

    public CallSite {
        Objects.requireNonNull(sourceFileId, "sourceFileId must not be null");
        Objects.requireNonNull(enclosingClass, "enclosingClass must not be null");
        Objects.requireNonNull(enclosingMethod, "enclosingMethod must not be null");
        Objects.requireNonNull(range, "range must not be null");
        enclosingMethod.ifPresent(method -> {
            if (!method.owner().equals(enclosingClass)) {
                throw new IllegalArgumentException("enclosing method owner must match the call-site class");
            }
        });
    }
}

