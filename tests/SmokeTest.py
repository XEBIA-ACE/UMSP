"""Smoke tests for the Python 3.8 -> 3.10 runtime upgrade (JTT-3255)."""

from __future__ import annotations

import asyncio
import importlib
import subprocess
import sys
import textwrap
import warnings
from pathlib import Path

import pytest

from migration import CompatibilityHelper

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestRuntimeVersion:
    def test_python_is_at_least_3_10(self):
        assert sys.version_info[:2] >= (3, 10), f"Expected Python 3.10+, got {sys.version}"

    def test_python_is_not_3_8(self):
        assert sys.version_info[:2] != (3, 8), "Python 3.8 is EOL and no longer supported."

    def test_pyproject_requires_python_3_10(self):
        text = (REPO_ROOT / "pyproject.toml").read_text()
        assert 'requires-python = ">=3.10"' in text

    def test_dockerfile_uses_python_3_10_image(self):
        text = (REPO_ROOT / "Dockerfile").read_text()
        assert "python:3.8" not in text
        assert "python:3.10" in text

    def test_ci_pins_python_3_10(self):
        text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()
        assert '"3.8"' not in text
        assert 'PYTHON_VERSION: "3.10"' in text


class TestApplicationInitialises:
    def test_package_imports(self):
        umsp = importlib.import_module("umsp")
        assert umsp.runtime_info()["python"].startswith("3.10") or sys.version_info[:2] > (3, 10)

    def test_module_entrypoint_runs(self):
        proc = subprocess.run(
            [sys.executable, "-m", "umsp"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert '"python"' in proc.stdout

    def test_no_syntax_errors_in_tree(self):
        proc = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", "umsp", "migration", "tests"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr


class TestPython310Features:
    def test_structural_pattern_matching(self):
        def kind(value):
            match value:
                case {"type": "user", "id": int(uid)}:
                    return f"user:{uid}"
                case [first, *_]:
                    return f"seq:{first}"
                case _:
                    return "other"

        assert kind({"type": "user", "id": 7}) == "user:7"
        assert kind([1, 2]) == "seq:1"
        assert kind(None) == "other"

    def test_union_type_operator(self):
        def f(x: int | None) -> str | None:
            return None if x is None else str(x)

        assert f(1) == "1" and f(None) is None
        assert isinstance(1, int | str)

    def test_parenthesized_context_managers(self):
        import contextlib
        with (
            contextlib.nullcontext(1) as a,
            contextlib.nullcontext(2) as b,
        ):
            assert (a, b) == (1, 2)

    def test_zip_strict(self):
        with pytest.raises(ValueError):
            list(zip([1, 2], [1], strict=True))

    def test_builtin_generic_aliases(self):
        assert list[int] is not None and dict[str, int] is not None


class TestNoDeprecatedRuntimeBehaviour:
    def test_collections_abc_aliases_removed(self):
        import collections
        import collections.abc
        assert not hasattr(collections, "Mapping")
        assert collections.abc.Mapping is not None

    def test_no_deprecation_warnings_importing_app(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            for name in ("umsp", "umsp.__main__", "migration.CompatibilityHelper"):
                sys.modules.pop(name, None)
                importlib.import_module(name)

    def test_asyncio_run_without_loop_param(self):
        async def work():
            await asyncio.sleep(0)
            return 42

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            assert asyncio.run(work()) == 42

    def test_scanner_finds_no_issues_in_repo(self):
        findings = CompatibilityHelper.scan_tree(REPO_ROOT)
        assert findings == [], "\n".join(findings)


class TestCompatibilityHelperScanner:
    def _scan(self, tmp_path: Path, source: str) -> list[str]:
        target = tmp_path / "legacy.py"
        target.write_text(textwrap.dedent(source))
        return CompatibilityHelper.scan_file(target)

    def test_detects_collections_alias(self, tmp_path):
        findings = self._scan(tmp_path, "from collections import Mapping\n")
        assert any("collections.Mapping" in f for f in findings)

    def test_detects_deprecated_module(self, tmp_path):
        findings = self._scan(tmp_path, "import distutils.core\n")
        assert any("distutils" in f for f in findings)

    def test_detects_asyncio_loop_param(self, tmp_path):
        findings = self._scan(tmp_path, "import asyncio\nasyncio.sleep(1, loop=None)\n")
        assert any("loop" in f for f in findings)

    def test_detects_deprecated_attribute(self, tmp_path):
        findings = self._scan(tmp_path, "import threading\nthreading.currentThread()\n")
        assert any("current_thread" in f for f in findings)

    def test_detects_invalid_escape(self, tmp_path):
        findings = self._scan(tmp_path, 'x = "\\d+"\n')
        assert any("invalid escape" in f for f in findings)

    def test_detects_syntax_error(self, tmp_path):
        findings = self._scan(tmp_path, "print 'hello'\n")
        assert any("SyntaxError" in f for f in findings)

    def test_clean_file_has_no_findings(self, tmp_path):
        findings = self._scan(tmp_path, "from collections.abc import Mapping\nx = r'\\d+'\n")
        assert findings == []

    def test_cli_reports_runtime(self):
        assert CompatibilityHelper.main([]) == 0
