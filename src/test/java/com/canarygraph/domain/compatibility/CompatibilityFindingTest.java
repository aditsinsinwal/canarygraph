package com.canarygraph.domain.compatibility;

import com.canarygraph.DomainFixtures;
import com.canarygraph.domain.api.ApiMethod;
import com.canarygraph.domain.api.MethodSignature;
import com.canarygraph.domain.common.JavaType;
import com.canarygraph.domain.common.QualifiedName;
import com.canarygraph.domain.common.SourcePosition;
import com.canarygraph.domain.common.SourceRange;
import com.canarygraph.domain.common.VersionNumber;
import com.canarygraph.domain.repository.RepositoryId;
import com.canarygraph.domain.repository.SourceFileId;
import com.canarygraph.domain.usage.ApiUsage;
import com.canarygraph.domain.usage.ApiUsageId;
import com.canarygraph.domain.usage.CallSite;
import com.canarygraph.domain.usage.ResolutionConfidence;
import com.canarygraph.domain.usage.UsageKind;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CompatibilityFindingTest {

    @Test
    void countsUniqueAffectedFilesAndCallSites() {
        ApiMethod removedMethod = DomainFixtures.method("createPayment", "void", "int");
        RepositoryId repositoryId = RepositoryId.newId();
        SourceFileId sourceFileId = SourceFileId.newId();
        ApiUsage first = usage(removedMethod, repositoryId, sourceFileId, 10);
        ApiUsage second = usage(removedMethod, repositoryId, sourceFileId, 20);

        CompatibilityFinding finding = new CompatibilityFinding(
                FindingId.newId(),
                removedMethodChange(removedMethod),
                List.of(first, second),
                new RiskAssessment(
                        63,
                        RiskLevel.HIGH,
                        "v1",
                        List.of(new RiskFactor("severity", 55, "High-severity API change"))
                ),
                MigrationDisposition.REVIEW_REQUIRED
        );

        assertThat(finding.affectedFileCount()).isOne();
        assertThat(finding.affectedCallSiteCount()).isEqualTo(2);
    }

    @Test
    void rejectsAUsageTargetingAnotherApiMethod() {
        ApiMethod removedMethod = DomainFixtures.method("createPayment", "void", "int");
        ApiMethod otherMethod = DomainFixtures.method("refundPayment", "void", "int");

        assertThatThrownBy(() -> new CompatibilityFinding(
                FindingId.newId(),
                removedMethodChange(removedMethod),
                List.of(usage(otherMethod, RepositoryId.newId(), SourceFileId.newId(), 10)),
                new RiskAssessment(10, RiskLevel.LOW, "v1", List.of()),
                MigrationDisposition.UNSUPPORTED
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("must match the old API symbol");
    }

    private BreakingChange removedMethodChange(ApiMethod method) {
        return new BreakingChange(
                BreakingChangeId.newId(),
                BreakingChangeType.METHOD_REMOVED,
                DomainFixtures.paymentLibrary(),
                new VersionNumber("1.0"),
                new VersionNumber("2.0"),
                Optional.of(method),
                Optional.empty(),
                ChangeSeverity.HIGH,
                "Public method was removed"
        );
    }

    private ApiUsage usage(
            ApiMethod target,
            RepositoryId repositoryId,
            SourceFileId sourceFileId,
            int line
    ) {
        QualifiedName service = new QualifiedName("com.example.CheckoutService");
        MethodSignature processPayment = new MethodSignature(
                service,
                "processPayment",
                List.of(),
                JavaType.VOID,
                false
        );
        CallSite callSite = new CallSite(
                sourceFileId,
                service,
                Optional.of(processPayment),
                new SourceRange(new SourcePosition(line, 9), new SourcePosition(line, 34))
        );
        return new ApiUsage(
                ApiUsageId.newId(),
                repositoryId,
                callSite,
                UsageKind.METHOD_CALL,
                Optional.of(target),
                ResolutionConfidence.EXACT
        );
    }
}

