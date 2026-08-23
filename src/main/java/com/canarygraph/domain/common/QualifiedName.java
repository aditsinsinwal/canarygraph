package com.canarygraph.domain.common;

import java.util.Arrays;

public record QualifiedName(String value) implements Comparable<QualifiedName> {

    public QualifiedName {
        value = DomainValidation.requireNonBlank(value, "qualifiedName");
        if (Arrays.stream(value.split("\\.", -1)).anyMatch(segment -> !isJavaIdentifier(segment))) {
            throw new IllegalArgumentException("qualifiedName must contain valid Java identifiers: " + value);
        }
    }

    private static boolean isJavaIdentifier(String value) {
        if (value.isEmpty() || !Character.isJavaIdentifierStart(value.codePointAt(0))) {
            return false;
        }
        return value.codePoints().skip(1).allMatch(Character::isJavaIdentifierPart);
    }

    public String simpleName() {
        int separator = value.lastIndexOf('.');
        return separator < 0 ? value : value.substring(separator + 1);
    }

    @Override
    public int compareTo(QualifiedName other) {
        return value.compareTo(other.value);
    }

    @Override
    public String toString() {
        return value;
    }
}

