package com.canarygraph.domain.compatibility;

import com.canarygraph.domain.common.DomainValidation;

public record RiskFactor(String name, int contribution, String explanation) {

    public RiskFactor {
        name = DomainValidation.requireNonBlank(name, "name");
        if (contribution < 0) {
            throw new IllegalArgumentException("risk contribution must not be negative");
        }
        explanation = DomainValidation.requireNonBlank(explanation, "explanation");
    }
}

