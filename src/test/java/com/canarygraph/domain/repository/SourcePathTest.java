package com.canarygraph.domain.repository;

import com.canarygraph.domain.common.SourcePath;
import org.junit.jupiter.api.Test;

import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class SourcePathTest {

    @Test
    void normalizesARepositoryRelativePath() {
        SourcePath sourcePath = SourcePath.of("src/main/../main/java/App.java");

        assertThat(sourcePath.value()).isEqualTo(Path.of("src/main/java/App.java"));
    }

    @Test
    void rejectsAPathThatEscapesTheRepositoryRoot() {
        assertThatThrownBy(() -> SourcePath.of("../../private/key"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("must not escape");
    }

    @Test
    void rejectsAnAbsolutePath() {
        assertThatThrownBy(() -> new SourcePath(Path.of("/tmp/App.java")))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("must be relative");
    }
}

