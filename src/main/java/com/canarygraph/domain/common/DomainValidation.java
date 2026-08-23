package com.canarygraph.domain.common;

import java.util.List;
import java.util.Objects;

public final class DomainValidation {

    private DomainValidation() {
    }

    public static String requireNonBlank(String value, String fieldName) {
        Objects.requireNonNull(value, fieldName + " must not be null");
        String normalized = value.strip();
        if (normalized.isEmpty()) {
            throw new IllegalArgumentException(fieldName + " must not be blank");
        }
        return normalized;
    }

    public static <T> List<T> immutableList(List<T> values, String fieldName) {
        Objects.requireNonNull(values, fieldName + " must not be null");
        if (values.stream().anyMatch(Objects::isNull)) {
            throw new IllegalArgumentException(fieldName + " must not contain null elements");
        }
        return List.copyOf(values);
    }
}

