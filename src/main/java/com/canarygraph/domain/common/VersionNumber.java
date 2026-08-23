package com.canarygraph.domain.common;

import java.util.regex.Pattern;

public record VersionNumber(String value) {

    private static final Pattern VALID_VERSION = Pattern.compile("[A-Za-z0-9][A-Za-z0-9._+\\-]*");

    public VersionNumber {
        value = DomainValidation.requireNonBlank(value, "version");
        if (!VALID_VERSION.matcher(value).matches()) {
            throw new IllegalArgumentException("version contains unsupported characters: " + value);
        }
    }

    @Override
    public String toString() {
        return value;
    }
}
