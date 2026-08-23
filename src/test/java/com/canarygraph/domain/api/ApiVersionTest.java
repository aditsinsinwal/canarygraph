package com.canarygraph.domain.api;

import com.canarygraph.DomainFixtures;
import com.canarygraph.domain.common.VersionNumber;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ApiVersionTest {

    @Test
    void copiesItsSymbolList() {
        List<ApiSymbol> symbols = new ArrayList<>();
        symbols.add(DomainFixtures.method("createPayment", "com.example.Payment", "int"));

        ApiVersion version = new ApiVersion(
                DomainFixtures.paymentLibrary(),
                new VersionNumber("1.0.0"),
                symbols
        );
        symbols.clear();

        assertThat(version.symbols()).hasSize(1);
    }

    @Test
    void rejectsDuplicateStructuredSymbolIdentities() {
        ApiMethod first = DomainFixtures.method("createPayment", "com.example.Payment", "int");
        ApiMethod duplicate = DomainFixtures.method("createPayment", "java.lang.Object", "int");

        assertThatThrownBy(() -> new ApiVersion(
                DomainFixtures.paymentLibrary(),
                new VersionNumber("1.0.0"),
                List.of(first, duplicate)
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("duplicate API symbol");
    }
}

