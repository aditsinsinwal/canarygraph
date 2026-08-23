package com.canarygraph.domain.api;

public enum Visibility {
    PRIVATE(0),
    PACKAGE_PRIVATE(1),
    PROTECTED(2),
    PUBLIC(3);

    private final int accessibility;

    Visibility(int accessibility) {
        this.accessibility = accessibility;
    }

    public boolean isReducedFrom(Visibility previous) {
        return accessibility < previous.accessibility;
    }
}

