package com.canarygraph.domain.api;

import com.canarygraph.domain.common.DomainValidation;
import com.canarygraph.domain.common.JavaType;

import java.util.Objects;
import java.util.Optional;

public record MethodParameter(JavaType type, Optional<String> declaredName, boolean varargs) {

    public MethodParameter {
        Objects.requireNonNull(type, "type must not be null");
        Objects.requireNonNull(declaredName, "declaredName must not be null");
        declaredName = declaredName.map(name -> DomainValidation.requireNonBlank(name, "declaredName"));
    }

    public static MethodParameter of(JavaType type) {
        return new MethodParameter(type, Optional.empty(), false);
    }

    public String descriptor() {
        return type.canonicalName() + (varargs ? "..." : "");
    }
}

