"""Non-executing Python source scanner and AST parser."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

from canarygraph.domain import (
    CallSite,
    FunctionSignature,
    ImportBinding,
    Parameter,
    ParameterKind,
    ProjectRepository,
    PythonClass,
    PythonFunction,
    PythonModule,
    SourceFile,
    SourceLocation,
    WebEndpoint,
    relative_module,
)
from canarygraph.exceptions import InvalidRepositoryError, SourceParseError

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
}


def _text(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except (ValueError, RecursionError):
        return None


def _dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return _dotted(node.func)
    return None


class SourceScanner:
    """Discover Python files without following symlinks outside the repository."""

    def __init__(self, *, max_file_bytes: int = 2_000_000) -> None:
        self.max_file_bytes = max_file_bytes

    def scan(self, root: str | Path) -> ProjectRepository:
        base = Path(root).expanduser().resolve()
        if not base.is_dir():
            raise InvalidRepositoryError(f"Repository is not a directory: {base}")
        files: list[SourceFile] = []
        for path in base.rglob("*.py"):
            if any(part in IGNORED_DIRECTORIES for part in path.parts):
                continue
            if path.is_symlink():
                try:
                    path.resolve().relative_to(base)
                except ValueError:
                    continue
            size = path.stat().st_size
            if size <= self.max_file_bytes:
                files.append(SourceFile(str(path), size))
        return ProjectRepository(str(base), tuple(sorted(files, key=lambda item: item.path)))


class _FunctionVisitor(ast.NodeVisitor):
    def __init__(self, caller: str, path: str) -> None:
        self.caller = caller
        self.path = path
        self.calls: list[CallSite] = []
        self.local_types: dict[str, str] = {}
        self.attribute_types: dict[str, str] = {}

    def visit_Call(self, node: ast.Call) -> None:
        expression = _dotted(node.func)
        if expression:
            self.calls.append(
                CallSite(
                    caller=self.caller,
                    expression=expression,
                    location=SourceLocation(self.path, node.lineno, node.col_offset),
                    positional_arguments=len(node.args),
                    keyword_arguments=tuple(
                        keyword.arg for keyword in node.keywords if keyword.arg is not None
                    ),
                )
            )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Call):
            type_name = _dotted(node.value.func)
            if type_name:
                for target in node.targets:
                    dotted = _dotted(target)
                    if dotted and dotted.startswith("self."):
                        self.attribute_types[dotted.removeprefix("self.")] = type_name
                    elif isinstance(target, ast.Name):
                        self.local_types[target.id] = type_name
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target = _dotted(node.target)
        annotation = _text(node.annotation)
        if target and annotation:
            if target.startswith("self."):
                self.attribute_types[target.removeprefix("self.")] = annotation
            elif isinstance(node.target, ast.Name):
                self.local_types[target] = annotation
        self.generic_visit(node)


class PythonRepositoryParser:
    """Parse Python modules into a compact, typed intermediate representation."""

    def parse_repository(self, repository: ProjectRepository) -> tuple[PythonModule, ...]:
        root = Path(repository.root)
        return tuple(self.parse_file(root, Path(item.path)) for item in repository.files)

    def parse_file(self, root: Path, path: Path) -> PythonModule:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path), type_comments=True)
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise SourceParseError(f"Unable to parse {path}: {exc}") from exc

        module_name = relative_module(root, path)
        imports = tuple(self._imports(tree, path))
        functions: list[PythonFunction] = []
        classes: list[PythonClass] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._function(node, module_name, path))
            elif isinstance(node, ast.ClassDef):
                classes.append(self._class(node, module_name, path))
        return PythonModule(module_name, str(path), imports, tuple(functions), tuple(classes))

    def _imports(self, tree: ast.Module, path: Path) -> Iterable[ImportBinding]:
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    yield ImportBinding(
                        alias.asname or alias.name.split(".")[0],
                        alias.name,
                        SourceLocation(str(path), node.lineno, node.col_offset),
                    )
            elif isinstance(node, ast.ImportFrom):
                prefix = "." * node.level + (node.module or "")
                for alias in node.names:
                    if alias.name != "*":
                        qualified = f"{prefix}.{alias.name}" if prefix else alias.name
                        yield ImportBinding(
                            alias.asname or alias.name,
                            qualified,
                            SourceLocation(str(path), node.lineno, node.col_offset),
                        )

    def _class(self, node: ast.ClassDef, module: str, path: Path) -> PythonClass:
        class_name = f"{module}.{node.name}" if module else node.name
        methods: list[PythonFunction] = []
        attribute_types: dict[str, str] = {}
        enum_members: list[str] = []
        bases = tuple(filter(None, (_dotted(base) for base in node.bases)))
        is_enum = any(base in {"Enum", "IntEnum", "StrEnum", "enum.Enum"} for base in bases)
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function = self._function(item, class_name, path, is_method=True)
                methods.append(function)
                attribute_types.update(dict(function.local_types))
                visitor = _FunctionVisitor(function.qualified_name, str(path))
                for statement in item.body:
                    visitor.visit(statement)
                attribute_types.update(visitor.attribute_types)
            elif is_enum and isinstance(item, (ast.Assign, ast.AnnAssign)):
                targets = item.targets if isinstance(item, ast.Assign) else [item.target]
                enum_members.extend(target.id for target in targets if isinstance(target, ast.Name))
        return PythonClass(
            class_name,
            SourceLocation(str(path), node.lineno, node.col_offset),
            tuple(methods),
            tuple(sorted(attribute_types.items())),
            bases,
            tuple(enum_members),
        )

    def _function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        owner: str,
        path: Path,
        *,
        is_method: bool = False,
    ) -> PythonFunction:
        qualified_name = f"{owner}.{node.name}" if owner else node.name
        visitor = _FunctionVisitor(qualified_name, str(path))
        for statement in node.body:
            visitor.visit(statement)
        signature = self._signature(node, is_method=is_method)
        endpoint = self._endpoint(node.decorator_list, qualified_name)
        return PythonFunction(
            qualified_name,
            signature,
            SourceLocation(str(path), node.lineno, node.col_offset),
            tuple(visitor.calls),
            tuple(sorted(visitor.local_types.items())),
            endpoint,
        )

    def _signature(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, *, is_method: bool
    ) -> FunctionSignature:
        args = node.args
        parameters: list[Parameter] = []
        positional = list(args.posonlyargs) + list(args.args)
        defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
        for index, (argument, default) in enumerate(zip(positional, defaults, strict=True)):
            if is_method and index == 0 and argument.arg in {"self", "cls"}:
                continue
            kind = (
                ParameterKind.POSITIONAL_ONLY
                if index < len(args.posonlyargs)
                else ParameterKind.POSITIONAL_OR_KEYWORD
            )
            parameters.append(
                Parameter(argument.arg, kind, _text(argument.annotation), _text(default))
            )
        if args.vararg:
            parameters.append(
                Parameter(
                    args.vararg.arg, ParameterKind.VAR_POSITIONAL, _text(args.vararg.annotation)
                )
            )
        for argument, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
            parameters.append(
                Parameter(
                    argument.arg,
                    ParameterKind.KEYWORD_ONLY,
                    _text(argument.annotation),
                    _text(default),
                )
            )
        if args.kwarg:
            parameters.append(
                Parameter(args.kwarg.arg, ParameterKind.VAR_KEYWORD, _text(args.kwarg.annotation))
            )
        return FunctionSignature(
            node.name,
            tuple(parameters),
            _text(node.returns),
            isinstance(node, ast.AsyncFunctionDef),
            tuple(
                filter(
                    None,
                    (
                        _dotted(item.func if isinstance(item, ast.Call) else item)
                        for item in node.decorator_list
                    ),
                )
            ),
        )

    def _endpoint(self, decorators: list[ast.expr], function: str) -> WebEndpoint | None:
        for decorator in decorators:
            if not isinstance(decorator, ast.Call):
                continue
            name = _dotted(decorator.func) or ""
            route = (
                decorator.args[0].value
                if decorator.args and isinstance(decorator.args[0], ast.Constant)
                else None
            )
            if not isinstance(route, str):
                continue
            method = name.rsplit(".", 1)[-1].upper()
            if method in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
                return WebEndpoint(function, "FastAPI", method, route)
            if method == "ROUTE":
                methods = next(
                    (item.value for item in decorator.keywords if item.arg == "methods"), None
                )
                if isinstance(methods, (ast.List, ast.Tuple)) and methods.elts:
                    value = methods.elts[0]
                    method = str(value.value).upper() if isinstance(value, ast.Constant) else "ANY"
                else:
                    method = "ANY"
                return WebEndpoint(function, "Flask", method, route)
        return None
