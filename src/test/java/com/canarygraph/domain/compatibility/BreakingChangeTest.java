package com.canarygraph.domain.compatibility;

import com.canarygraph.DomainFixtures;
import com.canarygraph.domain.api.ApiMethod;
import com.canarygraph.domain.api.Visibility;
import com.canarygraph.domain.common.VersionNumber;
import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class BreakingChangeTest {

    @Test
    void representsAParameterAdditionUsingStructuredMethods() {
        ApiMethod oldMethod = DomainFixtures.method(
                "createPayment",
                "com.example.Payment",
                "int"
        );
        ApiMethod newMethod = DomainFixtures.method(
                "createPayment",
                "com.example.Payment",
                "int",
                "java.lang.String"
        );

        BreakingChange change = change(
                BreakingChangeType.PARAMETER_ADDED,
                Optional.of(oldMethod),
                Optional.of(newMethod)
        );

        assertThat(change.oldSymbol()).contains(oldMethod);
        assertThat(change.newSymbol()).contains(newMethod);
        assertThat(change.type()).isEqualTo(BreakingChangeType.PARAMETER_ADDED);
    }

    @Test
    void rejectsParameterAddedWhenArityDidNotIncrease() {
        ApiMethod oldMethod = DomainFixtures.method("createPayment", "void", "int");
        ApiMethod newMethod = DomainFixtures.method("createPayment", "void", "long");

        assertThatThrownBy(() -> change(
                BreakingChangeType.PARAMETER_ADDED,
                Optional.of(oldMethod),
                Optional.of(newMethod)
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("increase arity");
    }

    @Test
    void rejectsRemovedMethodThatStillHasANewSymbol() {
        ApiMethod method = DomainFixtures.method("charge", "void", "int");

        assertThatThrownBy(() -> change(
                BreakingChangeType.METHOD_REMOVED,
                Optional.of(method),
                Optional.of(method)
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("must not have a new symbol");
    }

    @Test
    void acceptsVisibilityReductionAndRejectsAnIncrease() {
        ApiMethod publicMethod = DomainFixtures.method("charge", "void", "int");
        ApiMethod protectedMethod = new ApiMethod(
                publicMethod.signature(),
                Visibility.PROTECTED,
                false,
                false
        );

        assertThat(change(
                BreakingChangeType.VISIBILITY_REDUCED,
                Optional.of(publicMethod),
                Optional.of(protectedMethod)
        ).type()).isEqualTo(BreakingChangeType.VISIBILITY_REDUCED);

        assertThatThrownBy(() -> change(
                BreakingChangeType.VISIBILITY_REDUCED,
                Optional.of(protectedMethod),
                Optional.of(publicMethod)
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("lower than old");
    }

    private BreakingChange change(
            BreakingChangeType type,
            Optional<com.canarygraph.domain.api.ApiSymbol> oldSymbol,
            Optional<com.canarygraph.domain.api.ApiSymbol> newSymbol
    ) {
        return new BreakingChange(
                BreakingChangeId.newId(),
                type,
                DomainFixtures.paymentLibrary(),
                new VersionNumber("1.0"),
                new VersionNumber("2.0"),
                oldSymbol,
                newSymbol,
                ChangeSeverity.HIGH,
                "Structured compatibility rule matched"
        );
    }
}

