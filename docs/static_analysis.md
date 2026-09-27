# Static analysis

CanaryGraph parses source with `ast.parse`; it never imports an analyzed module. It extracts public
syntax and a compact intermediate representation rather than retaining full ASTs.

Resolution handles direct imports, `from` imports, aliases, package re-exports, module-qualified
calls, local and module-level constructor assignments, annotated parameters/locals, factory return
annotations, inherited service attributes, and constructor assignments to `self` attributes. Unique
simple-name and factory-return matches are medium confidence; unresolved dynamic dispatch is excluded
rather than reported as fact.

Known limits include monkey patching, reflective calls, runtime-generated imports, factory return
types, ambiguous multiple inheritance, and type changes hidden by unannotated container access. These
are soundness/completeness tradeoffs, not runtime guarantees. Every resolved SDK usage carries a
confidence and explanation.

The scanner ignores dependency/cache/build directories, rejects non-directories, caps individual
file size, total source size, and file count, and does not follow files symlinked outside the selected
repository.
