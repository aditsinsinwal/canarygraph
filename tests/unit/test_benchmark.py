from canarygraph.benchmark import run_benchmark


def test_benchmark_reports_measured_pipeline_metrics() -> None:
    result = run_benchmark(modules=3, functions_per_module=2)

    assert result.metrics["files"] == 4
    assert result.metrics["functions"] == 6
    assert result.metrics["graph_edges"] == 2
    assert result.breaking_changes == 1
    assert result.affected_findings == 1
    assert result.peak_memory_bytes > 0
