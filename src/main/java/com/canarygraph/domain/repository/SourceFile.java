package com.canarygraph.domain.repository;

import com.canarygraph.domain.common.ContentHash;
import com.canarygraph.domain.common.SourcePath;

import java.util.Objects;

public record SourceFile(
        SourceFileId id,
        RepositoryId repositoryId,
        SourcePath path,
        ContentHash contentHash,
        long lineCount
) {

    public SourceFile {
        Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(repositoryId, "repositoryId must not be null");
        Objects.requireNonNull(path, "path must not be null");
        Objects.requireNonNull(contentHash, "contentHash must not be null");
        if (lineCount < 0) {
            throw new IllegalArgumentException("lineCount must not be negative");
        }
    }
}

