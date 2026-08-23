package com.canarygraph;

import com.canarygraph.domain.api.ApiLibrary;
import com.canarygraph.domain.api.ApiMethod;
import com.canarygraph.domain.api.LibraryCoordinate;
import com.canarygraph.domain.api.MethodParameter;
import com.canarygraph.domain.api.MethodSignature;
import com.canarygraph.domain.api.Visibility;
import com.canarygraph.domain.common.JavaType;
import com.canarygraph.domain.common.QualifiedName;

import java.util.Arrays;
import java.util.List;

public final class DomainFixtures {

    private static final QualifiedName PAYMENT_CLIENT = new QualifiedName("com.example.PaymentClient");

    private DomainFixtures() {
    }

    public static ApiLibrary paymentLibrary() {
        return new ApiLibrary(
                new LibraryCoordinate("com.example", "payment-sdk"),
                "Payment SDK"
        );
    }

    public static ApiMethod method(String name, String returnType, String... parameterTypes) {
        List<MethodParameter> parameters = Arrays.stream(parameterTypes)
                .map(JavaType::new)
                .map(MethodParameter::of)
                .toList();
        return new ApiMethod(
                new MethodSignature(
                        PAYMENT_CLIENT,
                        name,
                        parameters,
                        new JavaType(returnType),
                        false
                ),
                Visibility.PUBLIC,
                false,
                false
        );
    }
}

