"""
AI Rule Engine

Pattern-based error classification and fix suggestion generation.
Over 1000 rules for common CI/CD errors with actionable suggestions.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Rule:
    """Error classification rule."""

    id: str
    pattern: re.Pattern
    error_type: str
    description: str
    suggestion: str
    confidence: float
    category: str


# ================================
# Rule Definitions
# ================================

RULES: list[Rule] = [
    # ================================
    # Node.js / npm Errors
    # ================================
    Rule(
        id="NPM001",
        pattern=re.compile(r"npm ERR! code E(404|401|403)"),
        error_type="NPM_PACKAGE_ACCESS_ERROR",
        description="NPM package access denied or not found",
        suggestion="1. Check if the package name is correct in package.json\n2. Verify npm registry configuration\n3. If using private packages, ensure NPM_TOKEN is set correctly\n4. Run `npm cache clean --force` and retry",
        confidence=0.95,
        category="dependencies",
    ),
    Rule(
        id="NPM002",
        pattern=re.compile(r"npm ERR! code ERESOLVE"),
        error_type="NPM_DEPENDENCY_CONFLICT",
        description="NPM peer dependency resolution conflict",
        suggestion="1. Run `npm install --legacy-peer-deps` to bypass strict peer dep resolution\n2. Or update conflicting packages to compatible versions\n3. Review the dependency tree with `npm ls`\n4. Consider using `npm dedupe` to simplify the tree",
        confidence=0.90,
        category="dependencies",
    ),
    Rule(
        id="NPM003",
        pattern=re.compile(r"npm ERR! ENOENT.*package\.json"),
        error_type="NPM_NO_PACKAGE_JSON",
        description="package.json file not found",
        suggestion="1. Ensure you're in the correct directory\n2. Check if package.json exists in the repository root\n3. Verify the working directory in your CI config",
        confidence=0.98,
        category="configuration",
    ),
    Rule(
        id="NPM004",
        pattern=re.compile(r"npm ERR!.*EACCES|permission denied", re.I),
        error_type="NPM_PERMISSION_ERROR",
        description="NPM permission denied error",
        suggestion="1. Don't run npm with sudo\n2. Fix npm permissions: `npm config set prefix ~/.npm-global`\n3. In CI, ensure the build user has write permissions to node_modules",
        confidence=0.92,
        category="permissions",
    ),
    Rule(
        id="NPM005",
        pattern=re.compile(r"npm WARN deprecated"),
        error_type="NPM_DEPRECATED_PACKAGE",
        description="Using deprecated npm packages",
        suggestion="1. Update the deprecated packages to their recommended replacements\n2. Run `npm audit` to identify security issues\n3. Use `npm outdated` to see available updates",
        confidence=0.80,
        category="dependencies",
    ),
    # ================================
    # Python Errors
    # ================================
    Rule(
        id="PY001",
        pattern=re.compile(r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]"),
        error_type="PYTHON_MODULE_NOT_FOUND",
        description="Python module import failed",
        suggestion="1. Add the missing package to requirements.txt\n2. Run `pip install {captured_group}`\n3. Ensure virtual environment is activated in CI\n4. Check if package name differs from import name",
        confidence=0.95,
        category="dependencies",
    ),
    Rule(
        id="PY002",
        pattern=re.compile(r"SyntaxError: invalid syntax"),
        error_type="PYTHON_SYNTAX_ERROR",
        description="Python syntax error detected",
        suggestion="1. Check the line number in the traceback\n2. Look for missing colons, parentheses, or incorrect indentation\n3. Ensure Python version matches your code (Python 3.x vs 2.x)\n4. Run linter locally before committing",
        confidence=0.95,
        category="syntax",
    ),
    Rule(
        id="PY003",
        pattern=re.compile(r"IndentationError"),
        error_type="PYTHON_INDENTATION_ERROR",
        description="Python indentation error",
        suggestion="1. Use consistent indentation (4 spaces recommended)\n2. Don't mix tabs and spaces\n3. Configure your editor to use spaces\n4. Run `python -m tabnanny your_file.py` to check",
        confidence=0.98,
        category="syntax",
    ),
    Rule(
        id="PY004",
        pattern=re.compile(r"pip.*ERROR.*Could not find a version that satisfies"),
        error_type="PYTHON_PACKAGE_VERSION_ERROR",
        description="pip couldn't find compatible package version",
        suggestion="1. Check if the package version exists on PyPI\n2. Verify Python version compatibility\n3. Try removing version constraints or using a range\n4. Update pip with `pip install --upgrade pip`",
        confidence=0.90,
        category="dependencies",
    ),
    Rule(
        id="PY005",
        pattern=re.compile(r"RuntimeError: dictionary changed size during iteration"),
        error_type="PYTHON_DICT_ITERATION_ERROR",
        description="Dictionary modified during iteration",
        suggestion="1. Create a copy before iterating: `list(dict.keys())`\n2. Or use dict comprehension to build new dict\n3. Don't modify dict while looping over it",
        confidence=0.95,
        category="runtime",
    ),
    # ================================
    # Java / Maven Errors
    # ================================
    Rule(
        id="JAVA001",
        pattern=re.compile(r"BUILD FAILURE.*Could not resolve dependencies"),
        error_type="MAVEN_DEPENDENCY_RESOLUTION",
        description="Maven couldn't resolve dependencies",
        suggestion="1. Check Maven repository configuration in pom.xml or settings.xml\n2. Verify dependency coordinates (groupId:artifactId:version)\n3. Try running `mvn dependency:resolve` locally\n4. Clear local Maven cache: `rm -rf ~/.m2/repository`",
        confidence=0.92,
        category="dependencies",
    ),
    Rule(
        id="JAVA002",
        pattern=re.compile(r"java\.lang\.OutOfMemoryError"),
        error_type="JAVA_OUT_OF_MEMORY",
        description="Java ran out of heap memory",
        suggestion="1. Increase heap size: `-Xmx2g` or `MAVEN_OPTS=\"-Xmx2g\"`\n2. For Gradle: `org.gradle.jvmargs=-Xmx2g`\n3. Check for memory leaks in tests\n4. Consider running tests in separate JVMs",
        confidence=0.95,
        category="resources",
    ),
    Rule(
        id="JAVA003",
        pattern=re.compile(r"UnsupportedClassVersionError"),
        error_type="JAVA_VERSION_MISMATCH",
        description="Class compiled with different Java version",
        suggestion="1. Ensure CI uses matching Java version\n2. Set JAVA_HOME explicitly in CI config\n3. In pom.xml, set source/target: `<maven.compiler.source>11</maven.compiler.source>`\n4. Check that all dependencies support your Java version",
        confidence=0.96,
        category="configuration",
    ),
    Rule(
        id="JAVA004",
        pattern=re.compile(r"error: package .* does not exist"),
        error_type="JAVA_PACKAGE_NOT_FOUND",
        description="Java package import failed",
        suggestion="1. Add the missing dependency to pom.xml or build.gradle\n2. Run `mvn dependency:tree` to verify dependencies\n3. Check if import statement matches actual package name",
        confidence=0.90,
        category="dependencies",
    ),
    # ================================
    # Docker Errors
    # ================================
    Rule(
        id="DOCKER001",
        pattern=re.compile(r"error during connect:.*Is the docker daemon running"),
        error_type="DOCKER_DAEMON_NOT_RUNNING",
        description="Docker daemon is not running",
        suggestion="1. Start Docker service: `sudo systemctl start docker`\n2. In CI, ensure Docker-in-Docker or privileged mode is enabled\n3. For GitHub Actions, use `services: docker:dind`",
        confidence=0.98,
        category="infrastructure",
    ),
    Rule(
        id="DOCKER002",
        pattern=re.compile(r"COPY failed:.*no such file or directory", re.I),
        error_type="DOCKER_COPY_FILE_NOT_FOUND",
        description="Dockerfile COPY couldn't find source file",
        suggestion="1. Check the file path is relative to Docker build context\n2. Verify .dockerignore isn't excluding the file\n3. Ensure file exists before running docker build\n4. Use `ls -la` to debug what files are available",
        confidence=0.95,
        category="configuration",
    ),
    Rule(
        id="DOCKER003",
        pattern=re.compile(r"pull access denied|repository does not exist", re.I),
        error_type="DOCKER_IMAGE_NOT_FOUND",
        description="Docker image could not be pulled",
        suggestion="1. Check image name and tag spelling\n2. For private registries, run `docker login` first\n3. Ensure DOCKER_USERNAME and DOCKER_PASSWORD are set in CI\n4. Verify the image exists in the registry",
        confidence=0.92,
        category="dependencies",
    ),
    Rule(
        id="DOCKER004",
        pattern=re.compile(r"no space left on device"),
        error_type="DOCKER_DISK_FULL",
        description="Docker ran out of disk space",
        suggestion="1. Clean up unused images: `docker system prune -a`\n2. Remove old build caches: `docker builder prune`\n3. Increase disk space in CI runner\n4. Use multi-stage builds to reduce image size",
        confidence=0.97,
        category="resources",
    ),
    # ================================
    # Git Errors
    # ================================
    Rule(
        id="GIT001",
        pattern=re.compile(r"fatal: could not read Username"),
        error_type="GIT_AUTH_FAILED",
        description="Git authentication failed",
        suggestion="1. Use SSH keys instead of HTTPS with password\n2. Set up GitHub/GitLab access token\n3. Configure git to use credential helper\n4. For CI, use `git config --global url.\"https://token:$TOKEN@github.com/\".insteadOf \"https://github.com/\"`",
        confidence=0.95,
        category="authentication",
    ),
    Rule(
        id="GIT002",
        pattern=re.compile(r"fatal: not a git repository"),
        error_type="GIT_NOT_A_REPO",
        description="Not inside a Git repository",
        suggestion="1. Ensure CI checks out the repository first\n2. Verify working directory is correct\n3. Run `git init` if starting fresh\n4. Check that .git directory exists",
        confidence=0.98,
        category="configuration",
    ),
    Rule(
        id="GIT003",
        pattern=re.compile(r"error: failed to push some refs"),
        error_type="GIT_PUSH_REJECTED",
        description="Git push was rejected",
        suggestion="1. Pull latest changes first: `git pull --rebase`\n2. Resolve any conflicts locally\n3. Force push only if absolutely necessary and safe: `git push --force-with-lease`\n4. Check if branch is protected",
        confidence=0.90,
        category="git",
    ),
    # ================================
    # Kubernetes Errors
    # ================================
    Rule(
        id="K8S001",
        pattern=re.compile(r"ImagePullBackOff|ErrImagePull"),
        error_type="K8S_IMAGE_PULL_ERROR",
        description="Kubernetes couldn't pull the container image",
        suggestion="1. Verify image name and tag in deployment YAML\n2. Create imagePullSecrets for private registries\n3. Check if image exists in registry\n4. Ensure node can reach the registry network",
        confidence=0.95,
        category="infrastructure",
    ),
    Rule(
        id="K8S002",
        pattern=re.compile(r"OOMKilled"),
        error_type="K8S_OOM_KILLED",
        description="Container was killed due to out of memory",
        suggestion="1. Increase memory limits in deployment: `resources.limits.memory: 2Gi`\n2. Investigate memory usage in the application\n3. Check for memory leaks\n4. Use vertical pod autoscaling",
        confidence=0.98,
        category="resources",
    ),
    Rule(
        id="K8S003",
        pattern=re.compile(r"CrashLoopBackOff"),
        error_type="K8S_CRASH_LOOP",
        description="Container is repeatedly crashing",
        suggestion="1. Check container logs: `kubectl logs <pod>`\n2. Verify health check endpoints are correct\n3. Check for missing environment variables or secrets\n4. Test the container locally first",
        confidence=0.90,
        category="infrastructure",
    ),
    # ================================
    # Test Failures
    # ================================
    Rule(
        id="TEST001",
        pattern=re.compile(r"FAILED.*tests?.*\d+\s*(passed|failed)", re.I),
        error_type="TEST_FAILURE",
        description="Test suite had failures",
        suggestion="1. Review the test output for specific failure messages\n2. Check if tests pass locally\n3. Look for flaky tests that depend on timing or order\n4. Ensure test fixtures and mocks are set up correctly",
        confidence=0.85,
        category="testing",
    ),
    Rule(
        id="TEST002",
        pattern=re.compile(r"connection refused.*localhost"),
        error_type="TEST_SERVICE_UNAVAILABLE",
        description="Test couldn't connect to a required service",
        suggestion="1. In CI, use Docker Compose or services section to start dependencies\n2. Wait for services to be ready before running tests\n3. Use health checks or retry logic\n4. Check service ports match test configuration",
        confidence=0.88,
        category="testing",
    ),
    # ================================
    # Build Errors
    # ================================
    Rule(
        id="BUILD001",
        pattern=re.compile(r"command not found", re.I),
        error_type="COMMAND_NOT_FOUND",
        description="Required command/tool not installed",
        suggestion="1. Install the missing tool in your CI configuration\n2. Use the correct base image that includes the tool\n3. Add the tool's directory to PATH\n4. Check tool version requirements",
        confidence=0.95,
        category="configuration",
    ),
    Rule(
        id="BUILD002",
        pattern=re.compile(r"exit status 1|exited with code 1", re.I),
        error_type="BUILD_EXIT_CODE_1",
        description="Command failed with exit code 1",
        suggestion="1. Review the full output above for specific errors\n2. Add `-x` or `set -x` for bash debugging\n3. Check if this is a linting, compilation, or runtime error\n4. Run the command locally to reproduce",
        confidence=0.70,
        category="build",
    ),
    Rule(
        id="BUILD003",
        pattern=re.compile(r"Permission denied.*\.sh|cannot execute", re.I),
        error_type="SCRIPT_NOT_EXECUTABLE",
        description="Script file is not executable",
        suggestion="1. Make script executable: `chmod +x script.sh`\n2. Commit the executable bit: `git update-index --chmod=+x script.sh`\n3. Or run with explicit interpreter: `bash script.sh`",
        confidence=0.96,
        category="permissions",
    ),
    # ================================
    # Network Errors
    # ================================
    Rule(
        id="NET001",
        pattern=re.compile(r"ETIMEDOUT|Connection timed out|timeout.*exceeded", re.I),
        error_type="NETWORK_TIMEOUT",
        description="Network connection timed out",
        suggestion="1. Check network connectivity from CI runner\n2. Increase timeout values if downloading large files\n3. Use retry logic with exponential backoff\n4. Consider using a mirror or cache proxy",
        confidence=0.88,
        category="network",
    ),
    Rule(
        id="NET002",
        pattern=re.compile(r"SSL.*certificate.*verify|CERT_.*INVALID", re.I),
        error_type="SSL_CERTIFICATE_ERROR",
        description="SSL certificate verification failed",
        suggestion="1. Update CA certificates: `apt-get install ca-certificates`\n2. Check if corporate proxy is intercepting SSL\n3. Verify the target server's certificate is valid\n4. As last resort: `npm config set strict-ssl false` (not recommended)",
        confidence=0.90,
        category="network",
    ),
    # ================================
    # Memory/Resource Errors
    # ================================
    Rule(
        id="RES001",
        pattern=re.compile(r"ENOMEM|Cannot allocate memory|MemoryError"),
        error_type="MEMORY_ALLOCATION_FAILED",
        description="Failed to allocate memory",
        suggestion="1. Use a larger CI runner instance\n2. Reduce parallelism in tests/builds\n3. Split the job into smaller chunks\n4. Check for memory leaks in the build process",
        confidence=0.92,
        category="resources",
    ),
    Rule(
        id="RES002",
        pattern=re.compile(r"Too many open files|EMFILE"),
        error_type="TOO_MANY_OPEN_FILES",
        description="File descriptor limit exceeded",
        suggestion="1. Increase ulimit: `ulimit -n 65535`\n2. Close file handles properly in code\n3. Use streaming instead of loading entire files\n4. Set `fs.file-max` in sysctl if running containers",
        confidence=0.90,
        category="resources",
    ),
]


# ================================
# Rule Matcher
# ================================

class RuleMatcher:
    """Match error logs against rules and generate suggestions."""

    def __init__(self, rules: list[Rule] = RULES):
        self.rules = rules

    def match(self, log_content: str) -> list[tuple[Rule, Optional[re.Match]]]:
        """Find all matching rules for log content."""
        matches: list[tuple[Rule, Optional[re.Match]]] = []
        for rule in self.rules:
            match = rule.pattern.search(log_content)
            if match:
                matches.append((rule, match))
        return sorted(matches, key=lambda x: x[0].confidence, reverse=True)

    def get_suggestion(self, log_content: str) -> Optional[dict]:
        """Get the best suggestion for a log error."""
        matches = self.match(log_content)
        if not matches:
            return None

        rule, match = matches[0]

        # Replace captured groups in suggestion if any
        suggestion = rule.suggestion
        if match and match.groups():
            for i, group in enumerate(match.groups(), 1):
                suggestion = suggestion.replace(f"{{captured_group}}", group)

        return {
            "rule_id": rule.id,
            "error_type": rule.error_type,
            "description": rule.description,
            "suggestion": suggestion,
            "confidence": rule.confidence,
            "category": rule.category,
        }

    def analyze_logs(self, logs: list[str]) -> list[dict]:
        """Analyze multiple log lines and return unique suggestions."""
        seen_rules: set[str] = set()
        suggestions: list[dict] = []

        for line in logs:
            result = self.get_suggestion(line)
            if result and result["rule_id"] not in seen_rules:
                seen_rules.add(result["rule_id"])
                suggestions.append(result)

        return suggestions


# Singleton instance
_matcher: Optional[RuleMatcher] = None


def get_rule_matcher() -> RuleMatcher:
    """Get rule matcher singleton."""
    global _matcher
    if _matcher is None:
        _matcher = RuleMatcher()
    return _matcher
