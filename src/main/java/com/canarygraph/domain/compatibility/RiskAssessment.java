package com.canarygraph.domain.compatibility;

import com.canarygraph.domain.common.DomainValidation;

import java.util.List;
import java.util.Objects;

public record RiskAssessment(
        int score,
        RiskLevel level,
        String policyVersion,
        List<RiskFactor> factors
) {

    public RiskAssessment {
        if (score < 0 || score > 100) {
            throw new IllegalArgumentException("risk score must be between 0 and 100");
        }
        Objects.requireNonNull(level, "level must not be null");
        if (level != RiskLevel.fromScore(score)) {
            throw new IllegalArgumentException("risk level does not match the score threshold");
        }
        policyVersion = DomainValidation.requireNonBlank(policyVersion, "policyVersion");
        factors = DomainValidation.immutableList(factors, "factors");
    }
}

