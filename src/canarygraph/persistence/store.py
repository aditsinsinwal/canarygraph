"""Small repository adapter keeping SQLAlchemy out of the analysis core."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from canarygraph.domain import CompatibilityReport
from canarygraph.exceptions import AnalysisNotFoundError, FindingNotFoundError
from canarygraph.persistence.models import (
    AnalysisRecord,
    ApiVersionRecord,
    BlastRadiusRecord,
    BreakingChangeRecord,
    FindingRecord,
    MigrationRecord,
    RepositoryRecord,
)


class AnalysisStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, report: CompatibilityReport) -> AnalysisRecord:
        repository = self.session.scalar(
            select(RepositoryRecord).where(RepositoryRecord.path == report.repository)
        )
        if repository is None:
            repository = RepositoryRecord(path=report.repository)
            self.session.add(repository)
            self.session.flush()
        record = AnalysisRecord(
            id=report.id,
            repository_id=repository.id,
            library=report.library,
            old_version=report.old_version,
            new_version=report.new_version,
            report=report.to_dict(),
        )
        self.session.add(record)
        self.session.flush()
        self.session.add_all(
            [
                ApiVersionRecord(
                    analysis_id=report.id,
                    role="OLD",
                    library=report.library,
                    version=report.old_version,
                ),
                ApiVersionRecord(
                    analysis_id=report.id,
                    role="NEW",
                    library=report.library,
                    version=report.new_version,
                ),
            ]
        )
        for change, payload in zip(report.changes, record.report["changes"], strict=True):
            self.session.add(
                BreakingChangeRecord(
                    analysis_id=report.id,
                    change_id=change.id,
                    kind=change.kind.value,
                    symbol=change.symbol,
                    severity=change.severity,
                    payload=payload,
                )
            )
        for finding, payload in zip(report.findings, record.report["findings"], strict=True):
            finding_record = FindingRecord(
                analysis_id=report.id,
                finding_id=finding.id,
                change_id=finding.change.id,
                risk_score=finding.risk.score,
                risk_level=finding.risk.level.value,
                payload=payload,
            )
            self.session.add(finding_record)
            self.session.flush()
            radius = finding.blast_radius
            self.session.add(
                BlastRadiusRecord(
                    finding_record_id=finding_record.id,
                    direct_count=len(radius.direct_functions),
                    transitive_count=len(radius.transitive_functions),
                    endpoint_count=len(radius.affected_endpoints),
                    payload=payload["blast_radius"],
                )
            )
        self.session.commit()
        return record

    def get(self, analysis_id: str) -> AnalysisRecord:
        record = self.session.get(AnalysisRecord, analysis_id)
        if record is None:
            raise AnalysisNotFoundError(f"Analysis {analysis_id!r} does not exist")
        return record

    def finding(self, finding_id: str) -> tuple[AnalysisRecord, dict[str, object]]:
        finding = self.session.scalar(
            select(FindingRecord)
            .where(FindingRecord.finding_id == finding_id)
            .order_by(FindingRecord.id.desc())
        )
        if finding:
            analysis = self.get(finding.analysis_id)
            return analysis, finding.payload
        raise FindingNotFoundError(f"Finding {finding_id!r} does not exist")

    def save_migration(
        self, analysis: AnalysisRecord, finding: dict[str, object]
    ) -> MigrationRecord:
        migration = finding["migration"]
        assert isinstance(migration, dict)
        record = MigrationRecord(
            analysis_id=analysis.id,
            finding_id=str(finding["id"]),
            repository=str(analysis.report["repository"]),
            status=str(migration["status"]),
            patches=list(migration.get("patches", [])),
        )
        self.session.add(record)
        self.session.commit()
        return record

    def get_migration(self, migration_id: str) -> MigrationRecord:
        record = self.session.get(MigrationRecord, migration_id)
        if record is None:
            raise AnalysisNotFoundError(f"Migration {migration_id!r} does not exist")
        return record
