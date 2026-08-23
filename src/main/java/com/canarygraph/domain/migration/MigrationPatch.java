package com.canarygraph.domain.migration;

import com.canarygraph.domain.common.DomainValidation;
import com.canarygraph.domain.common.SourcePath;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

public record MigrationPatch(
        MigrationPatchId id,
        MigrationPlanId planId,
        List<FilePatch> files
) {

    public MigrationPatch {
        Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(planId, "planId must not be null");
        files = new ArrayList<>(DomainValidation.immutableList(files, "files"));
        files.sort((left, right) -> left.path().compareTo(right.path()));
        files = List.copyOf(files);
        if (files.isEmpty()) {
            throw new IllegalArgumentException("a migration patch must contain at least one file");
        }
        Set<SourcePath> paths = new HashSet<>();
        for (FilePatch file : files) {
            if (!paths.add(file.path())) {
                throw new IllegalArgumentException("a migration patch must not repeat a file path");
            }
        }
    }
}
