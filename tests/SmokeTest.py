import sys
import subprocess
import json
import os
import re
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd, cwd=None):
    """Run a shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def _user_management_dir():
    """Return the absolute path to the user-management directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    # Walk up until we find user-management/ or give up after 5 levels
    candidate = here
    for _ in range(6):
        target = os.path.join(candidate, "user-management")
        if os.path.isdir(target):
            return target
        candidate = os.path.dirname(candidate)
    # Fallback: assume tests run from repo root
    return os.path.join(os.getcwd(), "user-management")


UM_DIR = _user_management_dir()
PACKAGE_JSON_PATH = os.path.join(UM_DIR, "package.json")


def _load_package_json():
    with open(PACKAGE_JSON_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# 1. Runtime / toolchain version assertions
# ---------------------------------------------------------------------------

class TestNodeVersion:
    """Verify that Node.js 20 LTS is the active runtime."""

    def test_node_is_installed(self):
        rc, stdout, stderr = _run(["node", "--version"])
        assert rc == 0, f"node --version failed: {stderr}"

    def test_node_major_version_is_20(self):
        rc, stdout, _ = _run(["node", "--version"])
        assert rc == 0
        version_str = stdout.strip()  # e.g. "v20.11.0"
        assert version_str.startswith("v"), f"Unexpected node version format: {version_str}"
        major = int(version_str.lstrip("v").split(".")[0])
        assert major == 20, (
            f"Expected Node.js major version 20, got {major} ({version_str}). "
            "Upgrade Node.js to 20 LTS as specified in the upgrade goal."
        )


class TestJestVersion:
    """Verify that Jest 29.7.0 is resolvable in the user-management workspace."""

    def test_jest_version_resolves(self):
        rc, stdout, stderr = _run(["npx", "jest", "--version"], cwd=UM_DIR)
        assert rc == 0, f"npx jest --version failed:\nstdout: {stdout}\nstderr: {stderr}"

    def test_jest_version_is_29(self):
        rc, stdout, _ = _run(["npx", "jest", "--version"], cwd=UM_DIR)
        assert rc == 0
        version_str = stdout.strip()  # e.g. "29.7.0"
        major = int(version_str.split(".")[0])
        assert major == 29, (
            f"Expected Jest major version 29, got {major} ({version_str})."
        )

    def test_jest_exact_version_in_package_json(self):
        pkg = _load_package_json()
        jest_version = pkg.get("devDependencies", {}).get("jest", "")
        assert jest_version != "", "jest not found in devDependencies"
        # Accept "^29.x.x" or "29.x.x"
        assert "29" in jest_version, (
            f"Expected jest 29.x in devDependencies, found: {jest_version}"
        )


# ---------------------------------------------------------------------------
# 2. package.json — coverage configuration keys introduced by the upgrade
# ---------------------------------------------------------------------------

class TestPackageJsonCoverageConfig:
    """Verify that all new Jest coverage configuration keys are present."""

    def test_package_json_exists(self):
        assert os.path.isfile(PACKAGE_JSON_PATH), (
            f"package.json not found at {PACKAGE_JSON_PATH}"
        )

    def test_jest_key_present(self):
        pkg = _load_package_json()
        assert "jest" in pkg, "Top-level 'jest' key missing from package.json"

    def test_coverage_directory_configured(self):
        pkg = _load_package_json()
        jest_cfg = pkg.get("jest", {})
        assert "coverageDirectory" in jest_cfg, (
            "'coverageDirectory' key missing from jest config in package.json"
        )
        assert jest_cfg["coverageDirectory"] == "coverage", (
            f"Expected coverageDirectory='coverage', got '{jest_cfg['coverageDirectory']}'"
        )

    def test_collect_coverage_from_configured(self):
        pkg = _load_package_json()
        jest_cfg = pkg.get("jest", {})
        assert "collectCoverageFrom" in jest_cfg, (
            "'collectCoverageFrom' key missing from jest config"
        )
        patterns = jest_cfg["collectCoverageFrom"]
        assert isinstance(patterns, list) and len(patterns) > 0, (
            "'collectCoverageFrom' must be a non-empty list"
        )
        # Must include src/**/*.js
        assert any("src/**/*.js" in p for p in patterns), (
            "'collectCoverageFrom' must include 'src/**/*.js'"
        )
        # Must exclude test files
        assert any("__tests__" in p for p in patterns), (
            "'collectCoverageFrom' must exclude src/__tests__/** (e.g. '!src/__tests__/**')"
        )

    def test_coverage_reporters_configured(self):
        """New key introduced by this upgrade."""
        pkg = _load_package_json()
        jest_cfg = pkg.get("jest", {})
        assert "coverageReporters" in jest_cfg, (
            "'coverageReporters' key missing from jest config — "
            "this key must be added as part of the coverage reporting upgrade."
        )
        reporters = jest_cfg["coverageReporters"]
        assert isinstance(reporters, list), "'coverageReporters' must be a list"
        required_reporters = {"text", "lcov", "html", "json-summary"}
        actual = set(reporters)
        missing = required_reporters - actual
        assert not missing, (
            f"'coverageReporters' is missing required reporters: {missing}. "
            f"Current reporters: {actual}"
        )

    def test_coverage_provider_configured(self):
        """New key introduced by this upgrade (V8 native coverage engine)."""
        pkg = _load_package_json()
        jest_cfg = pkg.get("jest", {})
        assert "coverageProvider" in jest_cfg, (
            "'coverageProvider' key missing from jest config — "
            "must be set to 'v8' for Node.js 20 native coverage."
        )
        assert jest_cfg["coverageProvider"] == "v8", (
            f"Expected coverageProvider='v8', got '{jest_cfg['coverageProvider']}'"
        )

    def test_coverage_thresholds_configured(self):
        """New key introduced by this upgrade."""
        pkg = _load_package_json()
        jest_cfg = pkg.get("jest", {})
        assert "coverageThreshold" in jest_cfg, (
            "'coverageThreshold' key missing from jest config — "
            "thresholds must be set as part of the coverage reporting upgrade."
        )
        thresholds = jest_cfg["coverageThreshold"]
        assert "global" in thresholds, (
            "'coverageThreshold.global' block missing"
        )
        global_thresholds = thresholds["global"]
        required_metrics = {"lines", "branches", "functions", "statements"}
        missing = required_metrics - set(global_thresholds.keys())
        assert not missing, (
            f"'coverageThreshold.global' is missing metrics: {missing}"
        )
        for metric, value in global_thresholds.items():
            assert isinstance(value, (int, float)), (
                f"Threshold for '{metric}' must be numeric, got {type(value)}"
            )
            assert 0 <= value <= 100, (
                f"Threshold for '{metric}' must be between 0 and 100, got {value}"
            )


# ---------------------------------------------------------------------------
# 3. npm scripts — new and updated scripts introduced by the upgrade
# ---------------------------------------------------------------------------

class TestNpmScripts:
    """Verify that the npm scripts are correctly configured after the upgrade."""

    def test_test_script_includes_coverage_flag(self):
        pkg = _load_package_json()
        test_script = pkg.get("scripts", {}).get("test", "")
        assert "--coverage" in test_script, (
            f"'test' script must include '--coverage' flag, got: '{test_script}'"
        )
        assert "jest" in test_script, (
            f"'test' script must invoke jest, got: '{test_script}'"
        )

    def test_test_coverage_script_exists(self):
        """New script introduced by this upgrade."""
        pkg = _load_package_json()
        scripts = pkg.get("scripts", {})
        assert "test:coverage" in scripts, (
            "'test:coverage' script missing from package.json scripts — "
            "this explicit coverage-only script must be added by the upgrade."
        )

    def test_test_coverage_script_has_force_exit(self):
        pkg = _load_package_json()
        coverage_script = pkg.get("scripts", {}).get("test:coverage", "")
        assert "--coverage" in coverage_script, (
            f"'test:coverage' script must include '--coverage', got: '{coverage_script}'"
        )
        assert "--forceExit" in coverage_script, (
            f"'test:coverage' script must include '--forceExit', got: '{coverage_script}'"
        )
        assert "jest" in coverage_script, (
            f"'test:coverage' script must invoke jest, got: '{coverage_script}'"
        )


# ---------------------------------------------------------------------------
# 4. Deprecated API / replaced configuration — old patterns must not appear
# ---------------------------------------------------------------------------

class TestDeprecatedConfigAbsent:
    """Verify that deprecated or replaced configuration patterns are not present."""

    def test_no_babel_jest_coverage_provider(self):
        """babel coverage provider is deprecated in favour of v8 on Node 20."""
        pkg = _load_package_json()
        jest_cfg = pkg.get("jest", {})
        provider = jest_cfg.get("coverageProvider", "")
        assert provider != "babel", (
            "coverageProvider='babel' is deprecated for Node.js 20; must be 'v8'."
        )

    def test_no_istanbul_explicit_dependency(self):
        """istanbul (v1) is superseded by @jest/coverage-provider v8; must not be a direct dep."""
        pkg = _load_package_json()
        all_deps = {
            **pkg.get("dependencies", {}),
            **pkg.get("devDependencies", {}),
        }
        assert "istanbul" not in all_deps, (
            "'istanbul' (v1) must not be a direct dependency; "
            "coverage is handled by Jest's built-in V8 provider."
        )

    def test_no_nyc_dependency(self):
        """nyc is the istanbul CLI wrapper; must not be present when using Jest coverage."""
        pkg = _load_package_json()
        all_deps = {
            **pkg.get("dependencies", {}),
            **pkg.get("devDependencies", {}),
        }
        assert "nyc" not in all_deps, (
            "'nyc' must not be a direct dependency; "
            "coverage is handled by Jest's built-in V8 provider."
        )


# ---------------------------------------------------------------------------
# 5. Critical application paths — test suite runs and coverage artefacts emitted
# ---------------------------------------------------------------------------

class TestTestSuiteExecution:
    """Verify that the test suite runs successfully and coverage artefacts are produced."""

    @pytest.fixture(scope="class")
    def run_jest_coverage(self):
        """Run 'npm run test:coverage' once per class and return the result."""
        rc, stdout, stderr = _run(
            ["npm", "run", "test:coverage"],
            cwd=UM_DIR,
        )
        return rc, stdout, stderr

    def test_test_suite_exits_zero(self, run_jest_coverage):
        rc, stdout, stderr = run_jest_coverage
        assert rc == 0, (
            f"Test suite exited with code {rc}.\n"
            f"stdout:\n{stdout}\n"
            f"stderr:\n{stderr}"
        )

    def test_coverage_directory_created(self, run_jest_coverage):
        coverage_dir = os.path.join(UM_DIR, "coverage")
        assert os.path.isdir(coverage_dir), (
            f"Coverage directory '{coverage_dir}' was not created after running tests."
        )

    def test_lcov_info_emitted(self, run_jest_coverage):
        lcov_path = os.path.join(UM_DIR, "coverage", "lcov.info")
        assert os.path.isfile(lcov_path), (
            f"lcov.info not found at '{lcov_path}'. "
            "Ensure 'lcov' is listed in coverageReporters."
        )

    def test_html_report_emitted(self, run_jest_coverage):
        html_index = os.path.join(UM_DIR, "coverage", "lcov-report", "index.html")
        # Some Jest versions emit to coverage/index.html directly
        html_alt = os.path.join(UM_DIR, "coverage", "index.html")
        assert os.path.isfile(html_index) or os.path.isfile(html_alt), (
            f"HTML coverage report not found at '{html_index}' or '{html_alt}'. "
            "Ensure 'html' is listed in coverageReporters."
        )

    def test_json_summary_emitted(self, run_jest_coverage):
        summary_path = os.path.join(UM_DIR, "coverage", "coverage-summary.json")
        assert os.path.isfile(summary_path), (
            f"coverage-summary.json not found at '{summary_path}'. "
            "Ensure 'json-summary' is listed in coverageReporters."
        )

    def test_json_summary_is_valid_json(self, run_jest_coverage):
        summary_path = os.path.join(UM_DIR, "coverage", "coverage-summary.json")
        if not os.path.isfile(summary_path):
            pytest.skip("coverage-summary.json not present; covered by prior test.")
        with open(summary_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert "total" in data, (
            "coverage-summary.json must contain a 'total' key."
        )
        total = data["total"]
        for metric in ("lines", "branches", "functions", "statements"):
            assert metric in total, (
                f"coverage-summary.json 'total' block missing metric: '{metric}'"
            )

    def test_coverage_summary_lines_pct_above_zero(self, run_jest_coverage):
        summary_path = os.path.join(UM_DIR, "coverage", "coverage-summary.json")
        if not os.path.isfile(summary_path):
            pytest.skip("coverage-summary.json not present.")
        with open(summary_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        lines_pct = data.get("total", {}).get("lines", {}).get("pct", 0)
        assert lines_pct > 0, (
            f"Line coverage is 0% — tests may not be collecting coverage correctly. "
            f"Got: {lines_pct}%"
        )

    def test_use_case_files_appear_in_coverage(self, run_jest_coverage):
        """Critical application paths (use cases) must appear in coverage data."""
        summary_path = os.path.join(UM_DIR, "coverage", "coverage-summary.json")
        if not os.path.isfile(summary_path):
            pytest.skip("coverage-summary.json not present.")
        with open(summary_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        # Keys in coverage-summary.json are file paths; check at least one use case is present
        covered_files = " ".join(data.keys())
        assert "usecases" in covered_files or "RegisterUser" in covered_files or \
               "LoginUser" in covered_files or "RecoverPassword" in covered_files, (
            "No use-case source files found in coverage-summary.json. "
            "Verify 'collectCoverageFrom' includes 'src/**/*.js'."
        )


# ---------------------------------------------------------------------------
# 6. New configuration keys load without errors (package.json schema integrity)
# ---------------------------------------------------------------------------

class TestConfigIntegrity:
    """Verify that the upgraded package.json is well-formed and all new keys are valid."""

    def test_package_json_is_valid_json(self):
        try:
            pkg = _load_package_json()
        except json.JSONDecodeError as exc:
            pytest.fail(f"package.json is not valid JSON: {exc}")

    def test_jest_config_has_no_unknown_top_level_typos(self):
        pkg = _load_package_json()
        jest_cfg = pkg.get("jest", {})
        known_keys = {
            "testEnvironment", "testMatch", "coverageDirectory",
            "collectCoverageFrom", "coverageReporters", "coverageProvider",
            "coverageThreshold", "testPathIgnorePatterns", "setupFilesAfterFramework",
            "setupFiles", "setupFilesAfterFramework", "transform", "moduleNameMapper",
            "globals", "reporters", "verbose", "forceExit", "testTimeout",
        }
        for key in jest_cfg:
            # Warn (not fail) on unexpected keys — they may be valid Jest options
            # but flag obvious typos of the new keys
            if key.startswith("coverage"):
                assert key in known_keys, (
                    f"Unexpected coverage-related key '{key}' in jest config — "
                    "possible typo of a required coverage key."
                )

    def test_coverage_threshold_values_are_numeric(self):
        pkg = _load_package_json()
        thresholds = pkg.get("jest", {}).get("coverageThreshold", {}).get("global", {})
        for metric, value in thresholds.items():
            assert isinstance(value, (int, float)), (
                f"coverageThreshold.global.{metric} must be numeric, got {type(value).__name__}"
            )

    def test_coverage_reporters_values_are_strings(self):
        pkg = _load_package_json()
        reporters = pkg.get("jest", {}).get("coverageReporters", [])
        for reporter in reporters:
            assert isinstance(reporter, str), (
                f"Each entry in coverageReporters must be a string, got {type(reporter).__name__}: {reporter}"
            )