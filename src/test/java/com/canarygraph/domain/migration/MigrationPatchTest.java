package com.canarygraph.domain.migration;

import com.canarygraph.domain.common.ContentHash;
import com.canarygraph.domain.common.SourcePath;
import com.canarygraph.domain.common.SourcePosition;
import com.canarygraph.domain.common.SourceRange;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class MigrationPatchTest {

    @Test
    void sortsEditsAndCopiesTheInputList() {
        TextEdit later = edit(20, 5, 20, 17, "createPayment");
        TextEdit earlier = edit(3, 8, 3, 19, "PaymentClient");
        List<TextEdit> edits = new ArrayList<>(List.of(later, earlier));

        FilePatch filePatch = new FilePatch(
                SourcePath.of("src/main/java/CheckoutService.java"),
                ContentHash.from("source".getBytes(StandardCharsets.UTF_8)),
                edits
        );
        edits.clear();

        assertThat(filePatch.edits()).containsExactly(earlier, later);
        assertThatThrownBy(() -> filePatch.edits().clear())
                .isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    void rejectsOverlappingEditsInTheSameFile() {
        TextEdit first = edit(10, 5, 10, 20, "first");
        TextEdit overlap = edit(10, 18, 10, 25, "second");

        assertThatThrownBy(() -> new FilePatch(
                SourcePath.of("src/App.java"),
                ContentHash.from(new byte[0]),
                List.of(first, overlap)
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("must not overlap");
    }

    @Test
    void rejectsDuplicateFilesInAMigrationPatch() {
        SourcePath path = SourcePath.of("src/App.java");
        ContentHash hash = ContentHash.from(new byte[0]);
        FilePatch first = new FilePatch(path, hash, List.of(edit(1, 1, 1, 3, "one")));
        FilePatch second = new FilePatch(path, hash, List.of(edit(2, 1, 2, 3, "two")));

        assertThatThrownBy(() -> new MigrationPatch(
                MigrationPatchId.newId(),
                MigrationPlanId.newId(),
                List.of(first, second)
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("must not repeat");
    }

    private TextEdit edit(int startLine, int startColumn, int endLine, int endColumn, String replacement) {
        return new TextEdit(
                new SourceRange(
                        new SourcePosition(startLine, startColumn),
                        new SourcePosition(endLine, endColumn)
                ),
                replacement
        );
    }
}

