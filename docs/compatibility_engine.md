# Compatibility engine

API source is normalized into classes, functions, methods, enum members, parameters, defaults,
parameter kinds, annotations, decorators, and returns. Formatting and comments do not influence the
diff.

Rules cover removals; configured callable/class/parameter renames; required additions; parameter
removal and annotation changes; positional-to-keyword-only changes; removed defaults; and removed
enum members. Optional parameter additions are non-breaking. `*args` and `**kwargs` are modeled but
do not justify optimistic migration assumptions.

Rename inference is not automatic: a reviewed JSON mapping supplies semantic identity. Behavioral
changes use reviewed JSON fixtures and are labeled as configured facts, never inferred behavior.

