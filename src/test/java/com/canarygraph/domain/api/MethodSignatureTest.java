package com.canarygraph.domain.api;

import com.canarygraph.domain.common.JavaType;
import com.canarygraph.domain.common.QualifiedName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class MethodSignatureTest {

    @Test
    void createsAStableStructuredDescriptorAndDefensiveCopy() {
        List<MethodParameter> parameters = new ArrayList<>();
        parameters.add(MethodParameter.of(new JavaType("int")));
        parameters.add(new MethodParameter(
                new JavaType("java.lang.String"),
                Optional.of("currency"),
                false
        ));

        MethodSignature signature = new MethodSignature(
                new QualifiedName("com.example.PaymentClient"),
                "createPayment",
                parameters,
                new JavaType("com.example.Payment"),
                false
        );
        parameters.clear();

        assertThat(signature.descriptor()).isEqualTo("createPayment(int,java.lang.String)");
        assertThat(signature.canonicalForm()).isEqualTo(
                "com.example.PaymentClient#createPayment(int,java.lang.String):com.example.Payment"
        );
        assertThat(signature.parameters()).hasSize(2);
        assertThatThrownBy(() -> signature.parameters().clear())
                .isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    void rejectsVarargsBeforeTheFinalParameter() {
        List<MethodParameter> parameters = List.of(
                new MethodParameter(new JavaType("java.lang.String"), Optional.empty(), true),
                MethodParameter.of(new JavaType("int"))
        );

        assertThatThrownBy(() -> new MethodSignature(
                new QualifiedName("com.example.Client"),
                "call",
                parameters,
                JavaType.VOID,
                false
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("final method parameter");
    }

    @Test
    void returnTypeIsNotPartOfTheJavaOverloadIdentity() {
        MethodSignature first = signatureWithReturnType("java.lang.String");
        MethodSignature second = signatureWithReturnType("java.lang.Object");

        assertThat(first.symbolId()).isEqualTo(second.symbolId());
        assertThat(first.canonicalForm()).isNotEqualTo(second.canonicalForm());
    }

    private MethodSignature signatureWithReturnType(String returnType) {
        return new MethodSignature(
                new QualifiedName("com.example.Client"),
                "find",
                List.of(MethodParameter.of(new JavaType("int"))),
                new JavaType(returnType),
                false
        );
    }
}

