package com.canarygraph.domain.api;

import com.canarygraph.domain.common.DomainValidation;
import com.canarygraph.domain.common.JavaType;
import com.canarygraph.domain.common.QualifiedName;

import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

public record MethodSignature(
        QualifiedName owner,
        String name,
        List<MethodParameter> parameters,
        JavaType returnType,
        boolean staticMethod
) {

    public MethodSignature {
        Objects.requireNonNull(owner, "owner must not be null");
        name = DomainValidation.requireNonBlank(name, "name");
        if (!isJavaIdentifier(name)) {
            throw new IllegalArgumentException("method name must be a valid Java identifier: " + name);
        }
        parameters = DomainValidation.immutableList(parameters, "parameters");
        Objects.requireNonNull(returnType, "returnType must not be null");
        for (int index = 0; index < parameters.size() - 1; index++) {
            if (parameters.get(index).varargs()) {
                throw new IllegalArgumentException("only the final method parameter may be varargs");
            }
        }
    }

    private static boolean isJavaIdentifier(String value) {
        return Character.isJavaIdentifierStart(value.codePointAt(0))
                && value.codePoints().skip(1).allMatch(Character::isJavaIdentifierPart);
    }

    public String descriptor() {
        return name + parameters.stream()
                .map(MethodParameter::descriptor)
                .collect(Collectors.joining(",", "(", ")"));
    }

    public String canonicalForm() {
        return owner + "#" + descriptor() + ":" + returnType;
    }

    public SymbolId symbolId() {
        return new SymbolId("METHOD:" + owner + "#" + descriptor());
    }
}

