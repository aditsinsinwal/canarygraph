# Static analysis

CanaryGraph parses source with `ast.parse`; it never imports an analyzed module. It extracts public
syntax and a compact intermediate representation rather than retaining full ASTs.

Resolution currently handles direct imports, `from` imports, aliases, module-qualified calls,
local constructor assignments, annotated locals, and constructor assignments to `self` attributes.
Unique simple-name matches are medium confidence; unresolved dynamic dispatch is excluded rather than
reported as fact.

Known limits include monkey patching, reflective calls, runtime-generated imports, factory return
types, ambiguous multiple inheritance, and type changes hidden by unannotated container access. These
are soundness/completeness tradeoffs, not runtime guarantees. Every resolved SDK usage carries a
confidence and explanation.

The scanner ignores dependency/cache/build directories, rejects non-directories, caps input file
size, and does not follow symlinks outside the selected repository.

