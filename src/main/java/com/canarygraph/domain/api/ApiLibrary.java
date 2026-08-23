package com.canarygraph.domain.api;

import com.canarygraph.domain.common.DomainValidation;

import java.util.Objects;

public record ApiLibrary(LibraryCoordinate coordinate, String displayName) {

    public ApiLibrary {
        Objects.requireNonNull(coordinate, "coordinate must not be null");
        displayName = DomainValidation.requireNonBlank(displayName, "displayName");
    }
}

