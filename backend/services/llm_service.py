"""
LLM commit analysis service.

Supports three modes (controlled by LLM_PROVIDER env var):
  openai  — OpenAI Chat Completions API (default)
  ollama  — local Ollama instance
  none    — rule-based fallback (no external calls)
"""
import json
import re
from dataclasses import dataclass
from typing import Optional

import httpx

from backend.core.config import get_settings

_settings = get_settings()

SYSTEM_PROMPT = """You are a senior software engineer evaluating the risk of a commit
causing CI pipeline failures. Given the commit message, list of changed files, and code
diff, respond with ONLY a JSON object in this exact format:

{
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "confidence": 0.0-1.0,
  "affected_modules": ["module1", "module2"],
  "reasoning": "one sentence explanation"
}

Risk criteria:
- LOW: docs, config, comments, minor refactors, single isolated file.
- MEDIUM: feature additions, moderate logic changes, < 5 files.
- HIGH: core business logic, auth, payments, DB schema, large diffs > 300 lines, many files.
"""


@dataclass
class LLMResult:
    risk_level: str          # LOW | MEDIUM | HIGH
    confidence: float
    affected_modules: list[str]
    reasoning: str
    raw_response: str = ""


# ── Rule-based fallback ───────────────────────────────────────────────────────

_HIGH_RISK_PATTERNS = re.compile(
    r"(schema|migration|auth|payment|security|critical|hotfix|database|"
    r"breaking|refactor\s+core|rewrite|vulnerabilit)",
    re.IGNORECASE,
)
_LOW_RISK_PATTERNS = re.compile(
    r"(readme|docs?|comment|whitespace|typo|lint|format|chore|bump version)",
    re.IGNORECASE,
)


def _rule_based_analysis(
    message: str, files: list[str], lines_added: int, lines_deleted: int
) -> LLMResult:
    churn = lines_added + lines_deleted
    num_files = len(files)

    if _HIGH_RISK_PATTERNS.search(message) or churn > 300 or num_files > 10:
        level, conf = "HIGH", 0.75
    elif _LOW_RISK_PATTERNS.search(message) or (churn < 20 and num_files <= 2):
        level, conf = "LOW", 0.80
    else:
        level, conf = "MEDIUM", 0.65

    affected = list({f.split("/")[0] for f in files if "/" in f})[:5] or ["root"]
    return LLMResult(
        risk_level=level,
        confidence=conf,
        affected_modules=affected,
        reasoning=f"Rule-based: {num_files} files, {churn} lines changed.",
    )


# ── JSON parse helper ─────────────────────────────────────────────────────────

def _parse_llm_json(raw: str) -> dict:
    # Strip markdown code fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON object from surrounding text
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise


# ── OpenAI ────────────────────────────────────────────────────────────────────

async def _openai_analyze(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {_settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": _settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 256,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ── Ollama ────────────────────────────────────────────────────────────────────

async def _ollama_analyze(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{_settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": _settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.2},
            },
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]


# ── Public API ────────────────────────────────────────────────────────────────

async def analyze_commit(
    message: str,
    files: list[str],
    diff: str = "",
    lines_added: int = 0,
    lines_deleted: int = 0,
) -> LLMResult:
    """Analyze a commit and return its risk assessment."""

    if _settings.LLM_PROVIDER == "none" or (
        _settings.LLM_PROVIDER == "openai" and not _settings.OPENAI_API_KEY
    ):
        return _rule_based_analysis(message, files, lines_added, lines_deleted)

    # Truncate diff to avoid huge prompts (max ~2000 chars)
    diff_snippet = diff[:2000] + ("…" if len(diff) > 2000 else "")
    prompt = (
        f"Commit message: {message}\n\n"
        f"Files changed ({len(files)}): {', '.join(files[:20])}\n\n"
        f"Diff snippet:\n{diff_snippet}"
    )

    raw = ""
    try:
        if _settings.LLM_PROVIDER == "openai":
            raw = await _openai_analyze(prompt)
        elif _settings.LLM_PROVIDER == "ollama":
            raw = await _ollama_analyze(prompt)
        else:
            return _rule_based_analysis(message, files, lines_added, lines_deleted)

        data = _parse_llm_json(raw)
        return LLMResult(
            risk_level=data.get("risk_level", "MEDIUM").upper(),
            confidence=float(data.get("confidence", 0.5)),
            affected_modules=data.get("affected_modules", []),
            reasoning=data.get("reasoning", ""),
            raw_response=raw,
        )
    except Exception:
        # Never crash the pipeline because of LLM errors
        return _rule_based_analysis(message, files, lines_added, lines_deleted)
