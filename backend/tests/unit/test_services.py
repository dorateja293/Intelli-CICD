"""
Unit tests for Webhook Service.
"""

import hashlib
import hmac

import pytest


class TestHMACValidation:
    """Test HMAC signature validation."""

    def test_github_signature_valid(self):
        """Test valid GitHub HMAC signature passes."""
        from services.webhook.main import validate_github_signature

        payload = b'{"test": "payload"}'
        secret = "test-secret"
        expected_sig = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        assert validate_github_signature(payload, secret, expected_sig) is True

    def test_github_signature_invalid(self):
        """Test invalid GitHub HMAC signature fails."""
        from services.webhook.main import validate_github_signature

        payload = b'{"test": "payload"}'
        secret = "test-secret"
        wrong_sig = "sha256=invalid"

        assert validate_github_signature(payload, secret, wrong_sig) is False

    def test_github_signature_missing(self):
        """Test missing signature header fails."""
        from services.webhook.main import validate_github_signature

        payload = b'{"test": "payload"}'
        secret = "test-secret"

        assert validate_github_signature(payload, secret, None) is False

    def test_gitlab_token_valid(self):
        """Test valid GitLab token passes."""
        from services.webhook.main import validate_gitlab_token

        token = "test-token"
        stored_secret = "test-token"

        assert validate_gitlab_token(token, stored_secret) is True

    def test_gitlab_token_invalid(self):
        """Test invalid GitLab token fails."""
        from services.webhook.main import validate_gitlab_token

        token = "wrong-token"
        stored_secret = "test-token"

        assert validate_gitlab_token(token, stored_secret) is False


class TestPayloadNormalization:
    """Test payload normalization functions."""

    def test_github_push_normalization(self):
        """Test GitHub push payload normalization."""
        from services.webhook.main import normalize_github_push

        payload = {
            "repository": {
                "id": 123,
                "clone_url": "https://github.com/test/repo.git",
            },
            "ref": "refs/heads/main",
            "after": "a" * 40,
            "head_commit": {
                "message": "Test commit",
                "author": {
                    "email": "test@example.com",
                    "name": "Test User",
                },
            },
        }
        repo_id = "test-repo-id"

        event = normalize_github_push(payload, repo_id)

        assert event.trigger_type == "push"
        assert event.provider == "github"
        assert event.repo_id == repo_id
        assert event.branch == "main"
        assert event.commit_sha == "a" * 40
        assert event.commit_message == "Test commit"
        assert event.author_email == "test@example.com"


class TestDAGBuilder:
    """Test DAG building and topological sort."""

    def test_single_stage_dag(self):
        """Test DAG with single stage - all jobs in one wave."""
        from services.orchestrator.main import JobConfig, build_dag

        jobs = {
            "job1": JobConfig(stage="build", commands=["echo 1"]),
            "job2": JobConfig(stage="build", commands=["echo 2"]),
            "job3": JobConfig(stage="build", commands=["echo 3"]),
        }
        stages = ["build"]

        waves = build_dag(jobs, stages)

        assert len(waves) == 1
        assert set(waves[0]) == {"job1", "job2", "job3"}

    def test_multi_stage_ordering(self):
        """Test DAG with multiple stages in correct order."""
        from services.orchestrator.main import JobConfig, build_dag

        jobs = {
            "install": JobConfig(stage="install", commands=["npm ci"]),
            "test": JobConfig(stage="test", commands=["npm test"]),
            "deploy": JobConfig(stage="deploy", commands=["deploy"]),
        }
        stages = ["install", "test", "deploy"]

        waves = build_dag(jobs, stages)

        assert len(waves) == 3
        assert "install" in waves[0]
        assert "test" in waves[1]
        assert "deploy" in waves[2]

    def test_circular_dependency_detection(self):
        """Test circular dependency raises error."""
        from services.orchestrator.main import JobConfig, build_dag

        jobs = {
            "a": JobConfig(stage="build", commands=["echo"], depends_on=["b"]),
            "b": JobConfig(stage="build", commands=["echo"], depends_on=["a"]),
        }
        stages = ["build"]

        with pytest.raises(ValueError, match="Circular dependency"):
            build_dag(jobs, stages)

    def test_unknown_dependency_detection(self):
        """Test unknown dependency raises error."""
        from services.orchestrator.main import JobConfig, build_dag

        jobs = {
            "a": JobConfig(stage="build", commands=["echo"], depends_on=["nonexistent"]),
        }
        stages = ["build"]

        with pytest.raises(ValueError, match="unknown job"):
            build_dag(jobs, stages)


class TestRuleEngine:
    """Test AI rule engine."""

    def test_npm_error_detection(self):
        """Test NPM error is correctly detected."""
        from ai.rule_engine import get_rule_matcher

        matcher = get_rule_matcher()
        log = "npm ERR! code E404"

        result = matcher.get_suggestion(log)

        assert result is not None
        assert result["error_type"] == "NPM_PACKAGE_ACCESS_ERROR"
        assert result["category"] == "dependencies"

    def test_python_module_error_detection(self):
        """Test Python module not found error."""
        from ai.rule_engine import get_rule_matcher

        matcher = get_rule_matcher()
        log = "ModuleNotFoundError: No module named 'flask'"

        result = matcher.get_suggestion(log)

        assert result is not None
        assert result["error_type"] == "PYTHON_MODULE_NOT_FOUND"

    def test_docker_daemon_error_detection(self):
        """Test Docker daemon error detection."""
        from ai.rule_engine import get_rule_matcher

        matcher = get_rule_matcher()
        log = "error during connect: Is the docker daemon running"

        result = matcher.get_suggestion(log)

        assert result is not None
        assert result["error_type"] == "DOCKER_DAEMON_NOT_RUNNING"

    def test_no_match_returns_none(self):
        """Test unrecognized error returns None."""
        from ai.rule_engine import get_rule_matcher

        matcher = get_rule_matcher()
        log = "Everything is fine, no errors here!"

        result = matcher.get_suggestion(log)

        assert result is None

    def test_log_level_detection(self):
        """Test log level detection from content."""
        from services.worker.main import detect_log_level

        assert detect_log_level("ERROR: something failed") == "ERROR"
        assert detect_log_level("Warning: deprecated") == "WARN"
        assert detect_log_level("DEBUG: trace info") == "DEBUG"
        assert detect_log_level("CRITICAL: system down") == "CRITICAL"
        assert detect_log_level("normal log line") == "INFO"


class TestBackoffCalculation:
    """Test retry backoff calculation."""

    def test_fixed_backoff(self):
        """Test fixed backoff strategy."""
        from services.orchestrator.main import compute_backoff

        assert compute_backoff(1, 30, "fixed") == 30.0
        assert compute_backoff(2, 30, "fixed") == 30.0
        assert compute_backoff(3, 30, "fixed") == 30.0

    def test_linear_backoff(self):
        """Test linear backoff strategy."""
        from services.orchestrator.main import compute_backoff

        assert compute_backoff(1, 30, "linear") == 30.0
        assert compute_backoff(2, 30, "linear") == 60.0
        assert compute_backoff(3, 30, "linear") == 90.0

    def test_exponential_backoff_capped(self):
        """Test exponential backoff is capped at 300s."""
        from services.orchestrator.main import compute_backoff

        # Should be capped
        result = compute_backoff(10, 30, "exponential")
        assert result <= 300
