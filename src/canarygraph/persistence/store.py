"""Small repository adapter keeping SQLAlchemy out of the analysis core."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from canarygraph.domain import CompatibilityReport
from canarygraph.exceptions import AnalysisNotFoundError, FindingNotFoundError
from canarygraph.persistence.models import AnalysisRecord, MigrationRecord, RepositoryRecord


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
        self.session.commit()
        return record

    def get(self, analysis_id: str) -> AnalysisRecord:
        record = self.session.get(AnalysisRecord, analysis_id)
        if record is None:
            raise AnalysisNotFoundError(f"Analysis {analysis_id!r} does not exist")
        return record

    def finding(self, finding_id: str) -> tuple[AnalysisRecord, dict[str, object]]:
        records = self.session.scalars(
            select(AnalysisRecord).order_by(AnalysisRecord.created_at.desc())
        )
        for record in records:
            for finding in record.report.get("findings", []):
                if finding.get("id") == finding_id:
                    return record, finding
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
