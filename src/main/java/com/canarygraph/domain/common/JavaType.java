package com.canarygraph.domain.common;

public record JavaType(String canonicalName) implements Comparable<JavaType> {

    public static final JavaType VOID = new JavaType("void");

    public JavaType {
        canonicalName = DomainValidation.requireNonBlank(canonicalName, "canonicalName")
                .replaceAll("\\s+", " ");
    }

    @Override
    public int compareTo(JavaType other) {
        return canonicalName.compareTo(other.canonicalName);
    }

    @Override
    public String toString() {
        return canonicalName;
    }
}

