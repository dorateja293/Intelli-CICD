"""
Standalone commit analyzer — wraps the same logic as backend/services/llm_service.py
but works as an independent library without FastAPI.

Can be used from CI scripts, GitHub Actions steps, or imported directly.

Usage:
  python -m llm-engine.commit_analysis.analyzer \
    --message "fix: critical auth bypass" \
    --files "auth/login.py,auth/middleware.py" \
    --diff_file diff.txt
"""
import argparse
import asyncio
import json
import re
from dataclasses import asdict, dataclass
from typing import Optional

import httpx


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class CommitAnalysis:
    risk_level: str           # LOW | MEDIUM | HIGH
    confidence: float
    affected_modules: list
    reasoning: str
    provider: str             # openai | ollama | rule-based


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior software engineer evaluating CI risk.
Given commit details, respond ONLY with JSON:
{
  "risk_level": "LOW"|"MEDIUM"|"HIGH",
  "confidence": 0.0-1.0,
  "affected_modules": ["mod1"],
  "reasoning": "brief explanation"
}"""


# ── Rule-based fallback ───────────────────────────────────────────────────────

_HIGH = re.compile(
    r"(schema|migration|auth|payment|security|critical|hotfix|breaking|"
    r"rewrite|vulnerabilit|database|core)",
    re.I,
)
_LOW = re.compile(
    r"(readme|doc|comment|whitespace|typo|lint|format|chore|bump|version)",
    re.I,
)


def rule_based(
    message: str, files: list, lines_added: int = 0, lines_deleted: int = 0
) -> CommitAnalysis:
    churn = lines_added + lines_deleted
    if _HIGH.search(message) or churn > 300 or len(files) > 10:
        level, conf = "HIGH", 0.75
    elif _LOW.search(message) or (churn < 20 and len(files) <= 2):
        level, conf = "LOW", 0.80
    else:
        level, conf = "MEDIUM", 0.65
    modules = list({f.split("/")[0] for f in files if "/" in f})[:5] or ["root"]
    return CommitAnalysis(
        risk_level=level,
        confidence=conf,
        affected_modules=modules,
        reasoning=f"Rule-based: {len(files)} files, {churn} lines changed.",
        provider="rule-based",
    )


# ── LLM helpers ───────────────────────────────────────────────────────────────

def _build_prompt(message: str, files: list, diff: str) -> str:
    snippet = diff[:2000] + ("…" if len(diff) > 2000 else "")
    return (
        f"Commit message: {message}\n\n"
        f"Files ({len(files)}): {', '.join(files[:20])}\n\n"
        f"Diff:\n{snippet}"
    )


def _parse(raw: str) -> dict:
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise


async def _call_openai(prompt: str, api_key: str, model: str = "gpt-4o-mini") -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 256,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _call_ollama(
    prompt: str, base_url: str = "http://localhost:11434", model: str = "llama3"
) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
        )
        r.raise_for_status()
        return r.json()["message"]["content"]


# ── Public API ────────────────────────────────────────────────────────────────

async def analyze(
    message: str,
    files: list,
    diff: str = "",
    lines_added: int = 0,
    lines_deleted: int = 0,
    provider: str = "rule-based",
    openai_api_key: str = "",
    openai_model: str = "gpt-4o-mini",
    ollama_base_url: str = "http://localhost:11434",
    ollama_model: str = "llama3",
) -> CommitAnalysis:
    if provider == "none" or (provider == "openai" and not openai_api_key):
        return rule_based(message, files, lines_added, lines_deleted)

    prompt = _build_prompt(message, files, diff)
    raw = ""
    try:
        if provider == "openai":
            raw = await _call_openai(prompt, openai_api_key, openai_model)
        elif provider == "ollama":
            raw = await _call_ollama(prompt, ollama_base_url, ollama_model)
        else:
            return rule_based(message, files, lines_added, lines_deleted)

        data = _parse(raw)
        return CommitAnalysis(
            risk_level=data.get("risk_level", "MEDIUM").upper(),
            confidence=float(data.get("confidence", 0.5)),
            affected_modules=data.get("affected_modules", []),
            reasoning=data.get("reasoning", ""),
            provider=provider,
        )
    except Exception as exc:
        return rule_based(message, files, lines_added, lines_deleted)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os

    ap = argparse.ArgumentParser(description="Analyze a commit for CI risk")
    ap.add_argument("--message", required=True)
    ap.add_argument("--files", default="", help="Comma-separated file paths")
    ap.add_argument("--diff_file", default="", help="Path to a diff file")
    ap.add_argument("--lines_added", type=int, default=0)
    ap.add_argument("--lines_deleted", type=int, default=0)
    ap.add_argument("--provider", default=os.getenv("LLM_PROVIDER", "rule-based"))
    ap.add_argument("--openai_key", default=os.getenv("OPENAI_API_KEY", ""))
    ap.add_argument("--openai_model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    ap.add_argument("--ollama_url", default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ap.add_argument("--ollama_model", default=os.getenv("OLLAMA_MODEL", "llama3"))
    args = ap.parse_args()

    diff_content = ""
    if args.diff_file:
        with open(args.diff_file) as f:
            diff_content = f.read()

    result = asyncio.run(
        analyze(
            message=args.message,
            files=[f.strip() for f in args.files.split(",") if f.strip()],
            diff=diff_content,
            lines_added=args.lines_added,
            lines_deleted=args.lines_deleted,
            provider=args.provider,
            openai_api_key=args.openai_key,
            openai_model=args.openai_model,
            ollama_base_url=args.ollama_url,
            ollama_model=args.ollama_model,
        )
    )
    print(json.dumps(asdict(result), indent=2))
