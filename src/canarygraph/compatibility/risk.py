"""Transparent deterministic risk scoring."""

from __future__ import annotations

from statistics import fmean

from canarygraph.domain import (
    ApiUsage,
    BlastRadius,
    BreakingChange,
    Confidence,
    RiskLevel,
    RiskScore,
)


class RiskScorer:
    """Score = severity*0.45 + direct*8 + transitive*2 + endpoints*12 + uncertainty.

    Counts are capped (direct 3, transitive 8, endpoints 2). Low-confidence
    resolution adds five points because uncertainty itself raises migration risk.
    """

    def score(
        self,
        change: BreakingChange,
        usages: tuple[ApiUsage, ...],
        blast_radius: BlastRadius,
    ) -> RiskScore:
        severity = round(change.severity * 0.45)
        direct = min(len(blast_radius.direct_functions), 3) * 8
        transitive = min(len(blast_radius.transitive_functions), 8) * 2
        endpoints = min(len(blast_radius.affected_endpoints), 2) * 12
        confidence_values = {Confidence.HIGH: 1.0, Confidence.MEDIUM: 0.65, Confidence.LOW: 0.3}
        mean_confidence = (
            fmean(confidence_values[item.confidence] for item in usages) if usages else 1.0
        )
        uncertainty = 5 if mean_confidence < 0.75 else 0
        score = min(100, severity + direct + transitive + endpoints + uncertainty)
        level = (
            RiskLevel.CRITICAL
            if score >= 85
            else RiskLevel.HIGH
            if score >= 65
            else RiskLevel.MEDIUM
            if score >= 35
            else RiskLevel.LOW
        )
        factors = (
            f"severity contribution: {severity}",
            f"direct usage contribution: {direct}",
            f"transitive caller contribution: {transitive}",
            f"endpoint contribution: {endpoints}",
            f"static-resolution uncertainty contribution: {uncertainty}",
        )
        return RiskScore(score, level, factors)
