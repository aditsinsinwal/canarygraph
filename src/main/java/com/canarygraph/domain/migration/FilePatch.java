package com.canarygraph.domain.migration;

import com.canarygraph.domain.common.ContentHash;
import com.canarygraph.domain.common.DomainValidation;
import com.canarygraph.domain.common.SourcePath;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public record FilePatch(SourcePath path, ContentHash expectedContentHash, List<TextEdit> edits) {

    public FilePatch {
        Objects.requireNonNull(path, "path must not be null");
        Objects.requireNonNull(expectedContentHash, "expectedContentHash must not be null");
        edits = new ArrayList<>(DomainValidation.immutableList(edits, "edits"));
        if (edits.isEmpty()) {
            throw new IllegalArgumentException("a file patch must contain at least one edit");
        }
        edits.sort(TextEdit::compareTo);
        for (int index = 1; index < edits.size(); index++) {
            if (edits.get(index - 1).range().overlaps(edits.get(index).range())) {
                throw new IllegalArgumentException("text edits in the same file must not overlap");
            }
        }
        edits = List.copyOf(edits);
    }
}

