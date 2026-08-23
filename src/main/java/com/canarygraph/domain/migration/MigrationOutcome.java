package com.canarygraph.domain.migration;

public enum MigrationOutcome {
    VALIDATED,
    COMPILE_FAILED,
    TEST_FAILED,
    REVIEW_REQUIRED,
    UNSUPPORTED
}

