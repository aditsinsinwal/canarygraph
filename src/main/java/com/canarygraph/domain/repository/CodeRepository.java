package com.canarygraph.domain.repository;

import com.canarygraph.domain.common.DomainValidation;
import com.canarygraph.domain.common.SourcePath;

import java.nio.file.Path;
import java.util.Objects;

public record CodeRepository(RepositoryId id, String name, Path root) {

    public CodeRepository {
        Objects.requireNonNull(id, "id must not be null");
        name = DomainValidation.requireNonBlank(name, "name");
        Objects.requireNonNull(root, "root must not be null");
        if (!root.isAbsolute()) {
            throw new IllegalArgumentException("repository root must be absolute");
        }
        root = root.normalize();
    }

    public Path resolve(SourcePath sourcePath) {
        Objects.requireNonNull(sourcePath, "sourcePath must not be null");
        Path resolved = root.resolve(sourcePath.value()).normalize();
        if (!resolved.startsWith(root)) {
            throw new IllegalArgumentException("resolved path escapes the repository root");
        }
        return resolved;
    }
}

