# Migration engine

The planner separates mechanically safe work from semantic decisions. Reviewed callable and keyword
renames and positional-to-keyword labeling are eligible for LibCST patches. Required values, behavior
changes, annotation changes, and removed defaults require review. CanaryGraph never invents values.

Generated patches are previews and do not modify the repository. Validation copies the repository to
a temporary directory, applies the candidate text there, parses it, and runs `compileall`. Mypy and
pytest are explicit opt-ins because pytest executes project code. Every subprocess has a timeout and
a minimal environment.

