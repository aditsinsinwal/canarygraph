package com.canarygraph.domain.usage;

import com.canarygraph.domain.api.ApiSymbol;
import com.canarygraph.domain.repository.RepositoryId;

import java.util.Objects;
import java.util.Optional;

public record ApiUsage(
        ApiUsageId id,
        RepositoryId repositoryId,
        CallSite callSite,
        UsageKind kind,
        Optional<ApiSymbol> target,
        ResolutionConfidence resolution
) {

    public ApiUsage {
        Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(repositoryId, "repositoryId must not be null");
        Objects.requireNonNull(callSite, "callSite must not be null");
        Objects.requireNonNull(kind, "kind must not be null");
        Objects.requireNonNull(target, "target must not be null");
        Objects.requireNonNull(resolution, "resolution must not be null");
        if (resolution == ResolutionConfidence.UNRESOLVED && target.isPresent()) {
            throw new IllegalArgumentException("an unresolved usage cannot have a target symbol");
        }
        if (resolution != ResolutionConfidence.UNRESOLVED && target.isEmpty()) {
            throw new IllegalArgumentException("a resolved usage must have a target symbol");
        }
    }
}

