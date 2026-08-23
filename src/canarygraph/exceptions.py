"""Application exceptions with stable error codes."""


class CanaryGraphError(Exception):
    code = "CANARYGRAPH_ERROR"


class InvalidRepositoryError(CanaryGraphError):
    code = "INVALID_REPOSITORY"


class SourceParseError(CanaryGraphError):
    code = "SOURCE_PARSE_ERROR"


class AnalysisNotFoundError(CanaryGraphError):
    code = "ANALYSIS_NOT_FOUND"


class FindingNotFoundError(CanaryGraphError):
    code = "FINDING_NOT_FOUND"
