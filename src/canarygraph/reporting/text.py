"""Stable terminal report format."""

from __future__ import annotations

from canarygraph.domain import CompatibilityReport


def render_text(report: CompatibilityReport) -> str:
    affected = [item for item in report.findings if item.usages]
    direct = {function for item in affected for function in item.blast_radius.direct_functions}
    transitive = {
        function for item in affected for function in item.blast_radius.transitive_functions
    }
    endpoints = {
        (endpoint.method, endpoint.path)
        for item in affected
        for endpoint in item.blast_radius.affected_endpoints
    }
    lines = [
        "CANARYGRAPH COMPATIBILITY REPORT",
        "",
        f"Library: {report.library}",
        f"Upgrade: {report.old_version} -> {report.new_version}",
        f"Breaking changes detected: {len(report.changes)}",
        f"Direct call sites affected: {len(direct)}",
        f"Transitively affected functions: {len(transitive)}",
        f"Affected HTTP endpoints: {len(endpoints)}",
    ]
    for finding in affected:
        change = finding.change
        lines.extend(
            [
                "",
                f"{finding.risk.level.value} ({finding.risk.score}/100)",
                change.symbol,
                f"Change: {change.kind.value}",
                f"Old: {change.old_signature.render() if change.old_signature else '-'}",
                f"New: {change.new_signature.render() if change.new_signature else '-'}",
                "Direct callers: " + ", ".join(finding.blast_radius.direct_functions),
                "Transitive callers: " + ", ".join(finding.blast_radius.transitive_functions),
                "Affected endpoints: "
                + ", ".join(
                    f"{item.method} {item.path}" for item in finding.blast_radius.affected_endpoints
                ),
                "Affected background jobs: "
                + ", ".join(
                    item.function for item in finding.blast_radius.affected_background_jobs
                ),
                "Affected tests: " + ", ".join(finding.blast_radius.affected_tests),
                f"Migration: {finding.migration.status.value}",
                f"Reason: {finding.migration.reason}",
            ]
        )
    if not affected:
        lines.extend(["", "No detected application call sites use the changed symbols."])
    return "\n".join(lines) + "\n"
