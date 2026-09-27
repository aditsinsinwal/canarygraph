"""Add normalized API, breaking-change, finding, and blast-radius records."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260927_0002"
down_revision: str | None = "20260823_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "api_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.String(36),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(8), nullable=False),
        sa.Column("library", sa.String(255), nullable=False),
        sa.Column("version", sa.String(100), nullable=False),
        sa.UniqueConstraint("analysis_id", "role"),
    )
    op.create_index("ix_api_versions_analysis_id", "api_versions", ["analysis_id"])
    op.create_table(
        "breaking_changes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.String(36),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("change_id", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint("analysis_id", "change_id"),
    )
    op.create_index("ix_breaking_changes_analysis_id", "breaking_changes", ["analysis_id"])
    op.create_index("ix_breaking_changes_kind", "breaking_changes", ["kind"])
    op.create_index("ix_breaking_changes_symbol", "breaking_changes", ["symbol"])
    op.create_table(
        "findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.String(36),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("finding_id", sa.String(64), nullable=False),
        sa.Column("change_id", sa.String(64), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint("analysis_id", "finding_id"),
    )
    op.create_index("ix_findings_analysis_id", "findings", ["analysis_id"])
    op.create_index("ix_findings_finding_id", "findings", ["finding_id"])
    op.create_index("ix_findings_risk_level", "findings", ["risk_level"])
    op.create_table(
        "blast_radius_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "finding_record_id",
            sa.String(36),
            sa.ForeignKey("findings.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("direct_count", sa.Integer(), nullable=False),
        sa.Column("transitive_count", sa.Integer(), nullable=False),
        sa.Column("endpoint_count", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("blast_radius_results")
    op.drop_index("ix_findings_risk_level", table_name="findings")
    op.drop_index("ix_findings_finding_id", table_name="findings")
    op.drop_index("ix_findings_analysis_id", table_name="findings")
    op.drop_table("findings")
    op.drop_index("ix_breaking_changes_symbol", table_name="breaking_changes")
    op.drop_index("ix_breaking_changes_kind", table_name="breaking_changes")
    op.drop_index("ix_breaking_changes_analysis_id", table_name="breaking_changes")
    op.drop_table("breaking_changes")
    op.drop_index("ix_api_versions_analysis_id", table_name="api_versions")
    op.drop_table("api_versions")
