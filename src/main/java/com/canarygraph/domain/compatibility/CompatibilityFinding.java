package com.canarygraph.domain.compatibility;

import com.canarygraph.domain.api.SymbolId;
import com.canarygraph.domain.common.DomainValidation;
import com.canarygraph.domain.usage.ApiUsage;

import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

public record CompatibilityFinding(
        FindingId id,
        BreakingChange breakingChange,
        List<ApiUsage> affectedUsages,
        RiskAssessment risk,
        MigrationDisposition migrationDisposition
) {

    public CompatibilityFinding {
        Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(breakingChange, "breakingChange must not be null");
        affectedUsages = DomainValidation.immutableList(affectedUsages, "affectedUsages");
        Objects.requireNonNull(risk, "risk must not be null");
        Objects.requireNonNull(migrationDisposition, "migrationDisposition must not be null");

        Set<Object> seenUsageIds = new HashSet<>();
        SymbolId affectedSymbol = breakingChange.oldSymbol()
                .orElseThrow(() -> new IllegalArgumentException("breaking change requires an old symbol"))
                .symbolId();
        for (ApiUsage usage : affectedUsages) {
            if (!seenUsageIds.add(usage.id())) {
                throw new IllegalArgumentException("affected usages must not contain duplicates");
            }
            SymbolId target = usage.target()
                    .orElseThrow(() -> new IllegalArgumentException("affected usage must have a target"))
                    .symbolId();
            if (!affectedSymbol.equals(target)) {
                throw new IllegalArgumentException("affected usage target must match the old API symbol");
            }
        }
    }

    public long affectedFileCount() {
        return affectedUsages.stream()
                .map(usage -> usage.callSite().sourceFileId())
                .distinct()
                .count();
    }

    public long affectedCallSiteCount() {
        return affectedUsages.size();
    }
}

