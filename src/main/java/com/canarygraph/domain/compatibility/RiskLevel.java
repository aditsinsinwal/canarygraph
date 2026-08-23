package com.canarygraph.domain.compatibility;

public enum RiskLevel {
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL;

    public static RiskLevel fromScore(int score) {
        if (score < 0 || score > 100) {
            throw new IllegalArgumentException("risk score must be between 0 and 100");
        }
        if (score < 30) {
            return LOW;
        }
        if (score < 55) {
            return MEDIUM;
        }
        if (score < 80) {
            return HIGH;
        }
        return CRITICAL;
    }
}

