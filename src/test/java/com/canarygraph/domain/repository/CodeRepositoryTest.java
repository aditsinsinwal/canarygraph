package com.canarygraph.domain.repository;

import com.canarygraph.domain.common.SourcePath;
import org.junit.jupiter.api.Test;

import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CodeRepositoryTest {

    @Test
    void resolvesASourcePathUnderTheRepositoryRoot() {
        CodeRepository repository = new CodeRepository(
                RepositoryId.newId(),
                "example-store",
                Path.of("/workspace/example-store")
        );

        assertThat(repository.resolve(SourcePath.of("src/App.java")))
                .isEqualTo(Path.of("/workspace/example-store/src/App.java"));
    }

    @Test
    void rejectsRelativeRepositoryRoots() {
        assertThatThrownBy(() -> new CodeRepository(
                RepositoryId.newId(),
                "example-store",
                Path.of("example-store")
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("must be absolute");
    }
}

