package com.canarygraph.domain.compatibility;

import com.canarygraph.domain.api.ApiClass;
import com.canarygraph.domain.api.ApiLibrary;
import com.canarygraph.domain.api.ApiMethod;
import com.canarygraph.domain.api.ApiSymbol;
import com.canarygraph.domain.api.MethodParameter;
import com.canarygraph.domain.common.DomainValidation;
import com.canarygraph.domain.common.VersionNumber;

import java.util.List;
import java.util.Objects;
import java.util.Optional;

public record BreakingChange(
        BreakingChangeId id,
        BreakingChangeType type,
        ApiLibrary library,
        VersionNumber oldVersion,
        VersionNumber newVersion,
        Optional<ApiSymbol> oldSymbol,
        Optional<ApiSymbol> newSymbol,
        ChangeSeverity severity,
        String rationale
) {

    public BreakingChange {
        Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(type, "type must not be null");
        Objects.requireNonNull(library, "library must not be null");
        Objects.requireNonNull(oldVersion, "oldVersion must not be null");
        Objects.requireNonNull(newVersion, "newVersion must not be null");
        if (oldVersion.equals(newVersion)) {
            throw new IllegalArgumentException("breaking change versions must differ");
        }
        Objects.requireNonNull(oldSymbol, "oldSymbol must not be null");
        Objects.requireNonNull(newSymbol, "newSymbol must not be null");
        Objects.requireNonNull(severity, "severity must not be null");
        rationale = DomainValidation.requireNonBlank(rationale, "rationale");
        validateShape(type, oldSymbol, newSymbol);
    }

    private static void validateShape(
            BreakingChangeType type,
            Optional<ApiSymbol> oldSymbol,
            Optional<ApiSymbol> newSymbol
    ) {
        switch (type) {
            case METHOD_REMOVED -> requireRemoval(oldSymbol, newSymbol, ApiMethod.class, "method");
            case CLASS_REMOVED -> requireRemoval(oldSymbol, newSymbol, ApiClass.class, "class");
            case METHOD_RENAMED -> {
                ApiMethod oldMethod = requireSymbol(oldSymbol, ApiMethod.class, "old method");
                ApiMethod newMethod = requireSymbol(newSymbol, ApiMethod.class, "new method");
                if (oldMethod.signature().name().equals(newMethod.signature().name())) {
                    throw new IllegalArgumentException("renamed methods must have different names");
                }
            }
            case CLASS_RENAMED -> {
                ApiClass oldClass = requireSymbol(oldSymbol, ApiClass.class, "old class");
                ApiClass newClass = requireSymbol(newSymbol, ApiClass.class, "new class");
                if (oldClass.qualifiedName().equals(newClass.qualifiedName())) {
                    throw new IllegalArgumentException("renamed classes must have different names");
                }
            }
            case PARAMETER_ADDED -> {
                MethodPair pair = requireMethods(oldSymbol, newSymbol);
                if (pair.oldMethod().signature().parameters().size()
                        >= pair.newMethod().signature().parameters().size()) {
                    throw new IllegalArgumentException("parameter-added change must increase arity");
                }
            }
            case PARAMETER_REMOVED -> {
                MethodPair pair = requireMethods(oldSymbol, newSymbol);
                if (pair.oldMethod().signature().parameters().size()
                        <= pair.newMethod().signature().parameters().size()) {
                    throw new IllegalArgumentException("parameter-removed change must decrease arity");
                }
            }
            case PARAMETER_TYPE_CHANGED -> {
                MethodPair pair = requireMethods(oldSymbol, newSymbol);
                List<MethodParameter> oldParameters = pair.oldMethod().signature().parameters();
                List<MethodParameter> newParameters = pair.newMethod().signature().parameters();
                if (oldParameters.size() != newParameters.size()
                        || oldParameters.equals(newParameters)
                        || noParameterTypeChanged(oldParameters, newParameters)) {
                    throw new IllegalArgumentException(
                            "parameter-type change requires equal arity and a changed parameter type");
                }
            }
            case RETURN_TYPE_CHANGED -> {
                MethodPair pair = requireMethods(oldSymbol, newSymbol);
                if (pair.oldMethod().signature().returnType()
                        .equals(pair.newMethod().signature().returnType())) {
                    throw new IllegalArgumentException("return-type change requires different return types");
                }
            }
            case VISIBILITY_REDUCED -> {
                ApiSymbol oldApiSymbol = requireAnySymbol(oldSymbol, "old symbol");
                ApiSymbol newApiSymbol = requireAnySymbol(newSymbol, "new symbol");
                if (oldApiSymbol.kind() != newApiSymbol.kind()) {
                    throw new IllegalArgumentException("visibility comparison requires the same symbol kind");
                }
                if (!newApiSymbol.visibility().isReducedFrom(oldApiSymbol.visibility())) {
                    throw new IllegalArgumentException("new visibility must be lower than old visibility");
                }
            }
        }
    }

    private static boolean noParameterTypeChanged(
            List<MethodParameter> oldParameters,
            List<MethodParameter> newParameters
    ) {
        for (int index = 0; index < oldParameters.size(); index++) {
            if (!oldParameters.get(index).type().equals(newParameters.get(index).type())
                    || oldParameters.get(index).varargs() != newParameters.get(index).varargs()) {
                return false;
            }
        }
        return true;
    }

    private static void requireRemoval(
            Optional<ApiSymbol> oldSymbol,
            Optional<ApiSymbol> newSymbol,
            Class<? extends ApiSymbol> expectedType,
            String label
    ) {
        requireSymbol(oldSymbol, expectedType, "old " + label);
        if (newSymbol.isPresent()) {
            throw new IllegalArgumentException("removed " + label + " must not have a new symbol");
        }
    }

    private static MethodPair requireMethods(
            Optional<ApiSymbol> oldSymbol,
            Optional<ApiSymbol> newSymbol
    ) {
        return new MethodPair(
                requireSymbol(oldSymbol, ApiMethod.class, "old method"),
                requireSymbol(newSymbol, ApiMethod.class, "new method")
        );
    }

    private static ApiSymbol requireAnySymbol(Optional<ApiSymbol> symbol, String label) {
        return symbol.orElseThrow(() -> new IllegalArgumentException(label + " is required"));
    }

    private static <T extends ApiSymbol> T requireSymbol(
            Optional<ApiSymbol> symbol,
            Class<T> expectedType,
            String label
    ) {
        ApiSymbol value = requireAnySymbol(symbol, label);
        if (!expectedType.isInstance(value)) {
            throw new IllegalArgumentException(label + " has the wrong symbol kind");
        }
        return expectedType.cast(value);
    }

    private record MethodPair(ApiMethod oldMethod, ApiMethod newMethod) {
    }
}

