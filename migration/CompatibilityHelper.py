"""Python 3.8 -> 3.10 upgrade helper.

Import early (``import migration.CompatibilityHelper``) to enforce the runtime
guard, or run directly to scan a source tree for 3.8-era constructs that were
deprecated or removed in Python 3.10::

    python -m migration.CompatibilityHelper --scan .
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import warnings
from pathlib import Path

MIN_PYTHON = (3, 10)

# Aliases removed from ``collections`` in 3.10 (now only in collections.abc).
REMOVED_COLLECTIONS_ABC_ALIASES = frozenset(
    {
        "Awaitable", "Coroutine", "AsyncIterable", "AsyncIterator",
        "AsyncGenerator", "Hashable", "Iterable", "Iterator", "Generator",
        "Reversible", "Sized", "Container", "Callable", "Collection", "Set",
        "MutableSet", "Mapping", "MutableMapping", "MappingView", "KeysView",
        "ItemsView", "ValuesView", "Sequence", "MutableSequence", "ByteString",
    }
)

# Modules deprecated/removed between 3.8 and 3.10 with their replacements.
DEPRECATED_MODULES = {
    "parser": "use the ast module",
    "symbol": "use the ast module",
    "formatter": "removed in 3.10",
    "binhex": "deprecated in 3.9",
    "distutils": "deprecated in 3.10, use setuptools/packaging",
    "asynchat": "deprecated, use asyncio",
    "asyncore": "deprecated, use asyncio",
    "smtpd": "deprecated, use aiosmtpd",
    "imp": "deprecated, use importlib",
}

# Removed/deprecated attributes: (module, attribute) -> hint
DEPRECATED_ATTRIBUTES = {
    ("asyncio", "get_event_loop"): "emits DeprecationWarning without a running loop in 3.10; use asyncio.run()",
    ("threading", "currentThread"): "use threading.current_thread()",
    ("threading", "activeCount"): "use threading.active_count()",
    ("base64", "encodestring"): "removed in 3.9, use base64.encodebytes()",
    ("base64", "decodestring"): "removed in 3.9, use base64.decodebytes()",
    ("array", "tostring"): "removed in 3.9, use array.tobytes()",
    ("array", "fromstring"): "removed in 3.9, use array.frombytes()",
    ("sys", "getcheckinterval"): "removed in 3.9, use sys.getswitchinterval()",
    ("sys", "setcheckinterval"): "removed in 3.9, use sys.setswitchinterval()",
    ("random", "sample"): "passing a set is deprecated in 3.9, convert to a sequence",
}

# ``asyncio`` coroutine helpers that dropped the ``loop`` parameter in 3.10.
ASYNCIO_LOOP_PARAM_REMOVED = frozenset(
    {"sleep", "gather", "shield", "wait_for", "wait", "as_completed",
     "Lock", "Event", "Condition", "Semaphore", "BoundedSemaphore", "Queue"}
)

_INVALID_ESCAPE_RE = re.compile(r"(?<!\\)\\[^\\'\"abfnrtvxuUN0-7\n]")


def enforce_min_python(version: tuple[int, int] = MIN_PYTHON) -> None:
    """Emit a warning if the interpreter predates the supported runtime."""
    if sys.version_info[:2] < version:
        warnings.warn(
            f"UMSP targets Python {version[0]}.{version[1]}+; running "
            f"{sys.version.split()[0]}. Please upgrade your Python runtime.",
            DeprecationWarning,
            stacklevel=2,
        )


class _Py310Visitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[str] = []
        self._aliases: dict[str, str] = {}

    def _report(self, node: ast.AST, message: str) -> None:
        self.findings.append(f"{self.path}:{node.lineno}: {message}")

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            self._aliases[alias.asname or root] = root
            if root in DEPRECATED_MODULES:
                self._report(node, f"import of '{root}' - {DEPRECATED_MODULES[root]}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        root = module.split(".")[0]
        if root in DEPRECATED_MODULES:
            self._report(node, f"import from '{module}' - {DEPRECATED_MODULES[root]}")
        if module == "collections":
            for alias in node.names:
                if alias.name in REMOVED_COLLECTIONS_ABC_ALIASES:
                    self._report(
                        node,
                        f"'collections.{alias.name}' removed in 3.10 - "
                        f"import from collections.abc",
                    )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name):
            module = self._aliases.get(node.value.id, node.value.id)
            if module == "collections" and node.attr in REMOVED_COLLECTIONS_ABC_ALIASES:
                self._report(node, f"'collections.{node.attr}' removed in 3.10 - use collections.abc")
            hint = DEPRECATED_ATTRIBUTES.get((module, node.attr))
            if hint:
                self._report(node, f"'{module}.{node.attr}' - {hint}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and self._aliases.get(func.value.id, func.value.id) == "asyncio"
            and func.attr in ASYNCIO_LOOP_PARAM_REMOVED
            and any(kw.arg == "loop" for kw in node.keywords)
        ):
            self._report(node, f"asyncio.{func.attr}(loop=...) - 'loop' parameter removed in 3.10")
        self.generic_visit(node)


def scan_file(path: Path) -> list[str]:
    """Return a list of Python 3.10 compatibility findings for one file."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"{path}:{exc.lineno}: SyntaxError under Python 3.10 - {exc.msg}"]

    visitor = _Py310Visitor(path)
    visitor.visit(tree)
    findings = visitor.findings

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            segment = ast.get_source_segment(source, node) or ""
            if segment[:1] not in ("r", "R", "b", "B", "f", "F") and _INVALID_ESCAPE_RE.search(segment):
                findings.append(
                    f"{path}:{node.lineno}: invalid escape sequence in string literal "
                    f"(DeprecationWarning, will become SyntaxError) - use a raw string"
                )
    return findings


DEFAULT_EXCLUDES = (".git", ".venv", "venv", "build", "dist", "__pycache__")


def scan_tree(root: Path, exclude: tuple[str, ...] = DEFAULT_EXCLUDES) -> list[str]:
    """Scan every ``*.py`` file under ``root``."""
    findings: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in exclude for part in path.parts):
            continue
        findings.extend(scan_file(path))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scan", metavar="PATH", default=None, help="directory or file to scan")
    args = parser.parse_args(argv)

    if args.scan is None:
        enforce_min_python()
        print(f"Python {sys.version.split()[0]} detected; minimum supported is {MIN_PYTHON[0]}.{MIN_PYTHON[1]}.")
        return 0 if sys.version_info[:2] >= MIN_PYTHON else 1

    target = Path(args.scan)
    findings = scan_file(target) if target.is_file() else scan_tree(target)
    for line in findings:
        print(line)
    print(f"{len(findings)} finding(s).")
    return 1 if findings else 0


enforce_min_python()

if __name__ == "__main__":
    sys.exit(main())
