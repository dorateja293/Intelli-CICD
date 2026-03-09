"""
AI CI Log Analyzer — rule-based NLP pattern matching engine.

Analyzes raw CI log text and returns:
  - error_type       : classified error category
  - root_cause       : human readable root cause
  - suggested_fix    : actionable fix steps
  - confidence       : 0.0 – 1.0
  - matched_lines    : log lines that triggered the classification
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ── Error patterns ─────────────────────────────────────────────────────────────

@dataclass
class ErrorPattern:
    error_type: str
    patterns: list[str]
    root_cause_template: str
    suggested_fix: str
    confidence: float


_PATTERNS: list[ErrorPattern] = [
    ErrorPattern(
        error_type="dependency_error",
        patterns=[
            r"ModuleNotFoundError: No module named '([^']+)'",
            r"ImportError: cannot import name '([^']+)'",
            r"Cannot find module '([^']+)'",
            r"npm ERR! 404.*'([^']+)'",
            r"ERROR: Could not find a version that satisfies the requirement (\S+)",
            r"Package '([^']+)' is not installed",
            r"requirement '([^']+)' not found",
            r"error: package '([^']+)' not found",
        ],
        root_cause_template="Missing or uninstalled package: {match}",
        suggested_fix=(
            "1. Run `pip install <package>` or `npm install <package>`\n"
            "2. Check your requirements.txt / package.json includes this dependency\n"
            "3. Ensure your virtual environment is activated before running the build"
        ),
        confidence=0.92,
    ),
    ErrorPattern(
        error_type="compilation_error",
        patterns=[
            r"SyntaxError: (.*)",
            r"error: expected (.*)",
            r"CompileError: (.*)",
            r"error TS\d+: (.*)",
            r"Build error: (.*)",
            r"ERROR in (.*\.(?:ts|tsx|js|jsx))\(",
            r"Traceback \(most recent call last\)",
        ],
        root_cause_template="Compilation or syntax error detected: {match}",
        suggested_fix=(
            "1. Check the flagged file for syntax errors\n"
            "2. Run `tsc --noEmit` (TypeScript) or `python -m py_compile <file>` locally\n"
            "3. Review the failing line in the stack trace"
        ),
        confidence=0.88,
    ),
    ErrorPattern(
        error_type="test_failure",
        patterns=[
            r"FAILED (\S+) - AssertionError",
            r"AssertionError: (.*)",
            r"Expected (.*) to equal (.*)",
            r"(\d+) test(?:s)? failed",
            r"FAIL\s+(\S+)\s+\(.*\)",
            r"● (.*) › (.*)",
            r"pytest.*\d+ failed",
            r"E\s+assert (.*)",
        ],
        root_cause_template="Test assertion failed: {match}",
        suggested_fix=(
            "1. Run the failing test locally: `pytest <test_file>::<test_name> -v`\n"
            "2. Check if recent code changes broke the expected behaviour\n"
            "3. Review mock/fixture data — expected values may need updating"
        ),
        confidence=0.91,
    ),
    ErrorPattern(
        error_type="timeout_error",
        patterns=[
            r"TimeoutError",
            r"Job exceeded the maximum time limit",
            r"timed out after (\d+)",
            r"Error: Timeout of (\d+)ms exceeded",
            r"ETIMEDOUT",
            r"connect ETIMEDOUT",
            r"Read timeout",
        ],
        root_cause_template="Process or network timeout: {match}",
        suggested_fix=(
            "1. Increase the timeout value in your CI configuration\n"
            "2. Check for slow external API calls or database queries in tests\n"
            "3. Use mocks/stubs for external services in unit tests\n"
            "4. Investigate if the runner is resource-constrained"
        ),
        confidence=0.85,
    ),
    ErrorPattern(
        error_type="infrastructure_error",
        patterns=[
            r"Connection refused",
            r"ECONNREFUSED",
            r"Cannot connect to (?:database|Redis|Postgres|MySQL)",
            r"OOM killer",
            r"Out of memory",
            r"Killed",
            r"No space left on device",
            r"FATAL: (?:database|role) .* does not exist",
            r"docker: Error response from daemon",
        ],
        root_cause_template="Infrastructure or environment failure: {match}",
        suggested_fix=(
            "1. Verify service dependencies are running (DB, Redis, cache)\n"
            "2. Check memory limits on the CI runner — increase if hitting OOM\n"
            "3. Ensure environment variables (DATABASE_URL, REDIS_URL) are set\n"
            "4. Add health-check steps before running tests"
        ),
        confidence=0.83,
    ),
    ErrorPattern(
        error_type="permission_error",
        patterns=[
            r"PermissionError: \[Errno 13\]",
            r"Permission denied",
            r"EACCES",
            r"403 Forbidden",
            r"Access denied",
            r"Unauthorized",
        ],
        root_cause_template="Permission or authorization failure: {match}",
        suggested_fix=(
            "1. Check file/directory permissions in the runner environment\n"
            "2. Ensure CI secrets (tokens, keys) are correctly configured\n"
            "3. Verify the service account has required IAM/RBAC permissions"
        ),
        confidence=0.87,
    ),
    ErrorPattern(
        error_type="network_error",
        patterns=[
            r"curl: \((\d+)\)",
            r"Failed to fetch",
            r"getaddrinfo ENOTFOUND",
            r"Name or service not known",
            r"SSL certificate problem",
            r"certificate verify failed",
            r"HTTPSConnectionPool.*Max retries exceeded",
        ],
        root_cause_template="Network or DNS resolution failure: {match}",
        suggested_fix=(
            "1. Check if the target host is reachable from the CI runner\n"
            "2. Verify DNS settings and proxy configuration\n"
            "3. If SSL error, update CA certificates or disable strict checking in dev\n"
            "4. Add retry logic for flaky network calls"
        ),
        confidence=0.82,
    ),
    ErrorPattern(
        error_type="docker_error",
        patterns=[
            r"docker build.*failed",
            r"failed to solve: (.*)",
            r"COPY failed: (.*)",
            r"RUN.*returned a non-zero code",
            r"manifest for .* not found",
        ],
        root_cause_template="Docker build or runtime failure: {match}",
        suggested_fix=(
            "1. Run `docker build` locally to reproduce the error\n"
            "2. Check the Dockerfile for missing files or incorrect paths\n"
            "3. Verify the base image tag exists and is accessible\n"
            "4. Review `.dockerignore` — required files may be excluded"
        ),
        confidence=0.86,
    ),
]

_FALLBACK_PATTERN = ErrorPattern(
    error_type="unknown_error",
    patterns=[r"error|ERROR|Error|FAILED|failed|exception|Exception"],
    root_cause_template="Unclassified error in CI log",
    suggested_fix=(
        "1. Scroll to the first ERROR or FAILED line in the log for the root cause\n"
        "2. Search the error message on GitHub Issues / Stack Overflow\n"
        "3. Run the failing step locally to get a cleaner stack trace"
    ),
    confidence=0.40,
)


# ── Analysis result ────────────────────────────────────────────────────────────

@dataclass
class LogAnalysisResult:
    error_type: str
    root_cause: str
    suggested_fix: str
    confidence: float
    matched_lines: list[str] = field(default_factory=list)
    severity: str = "medium"   # low | medium | high | critical


# ── Core analyzer ──────────────────────────────────────────────────────────────

def _severity_from_type(error_type: str) -> str:
    critical = {"infrastructure_error", "docker_error"}
    high = {"compilation_error", "dependency_error"}
    low = {"test_failure"}
    if error_type in critical:
        return "critical"
    if error_type in high:
        return "high"
    if error_type in low:
        return "low"
    return "medium"


def analyze_log(log_text: str) -> LogAnalysisResult:
    """
    Main entry point. Analyzes CI log text and returns a structured result.
    """
    lines = log_text.splitlines()
    best_result: Optional[LogAnalysisResult] = None
    best_confidence = 0.0

    for ep in _PATTERNS:
        matched_lines = []
        first_match_text = ""

        for line in lines:
            for pattern in ep.patterns:
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    matched_lines.append(line.strip())
                    if not first_match_text:
                        first_match_text = m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0)
                    break

        if matched_lines:
            root_cause = ep.root_cause_template.format(match=first_match_text or "see matched lines")
            confidence = min(ep.confidence + 0.02 * min(len(matched_lines), 3), 0.99)
            result = LogAnalysisResult(
                error_type=ep.error_type,
                root_cause=root_cause,
                suggested_fix=ep.suggested_fix,
                confidence=round(confidence, 3),
                matched_lines=matched_lines[:5],
                severity=_severity_from_type(ep.error_type),
            )
            if confidence > best_confidence:
                best_confidence = confidence
                best_result = result

    if best_result:
        return best_result

    # Fallback — look for any error keyword
    fallback_lines = [
        l.strip() for l in lines
        if re.search(r"error|ERROR|FAILED|failed|exception", l)
    ][:5]

    return LogAnalysisResult(
        error_type="unknown_error",
        root_cause="Could not classify the error automatically — review the full log",
        suggested_fix=_FALLBACK_PATTERN.suggested_fix,
        confidence=0.35 if fallback_lines else 0.10,
        matched_lines=fallback_lines,
        severity="medium",
    )


def suggest_fix(log_text: str) -> dict:
    """
    Convenience wrapper — returns a dict suitable for the /fix-error API response.
    """
    result = analyze_log(log_text)
    return {
        "error_type": result.error_type,
        "root_cause": result.root_cause,
        "suggested_fix": result.suggested_fix,
        "confidence": result.confidence,
        "severity": result.severity,
        "matched_lines": result.matched_lines,
    }
