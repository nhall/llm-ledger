"""
llm-ledger: Claude API wrapper with prompt loading and audit logging.

Every call to `reason()` is appended to a JSONL audit log with timestamp,
model, token counts, and estimated cost. Prompts are loaded from .txt files
on disk so they can be versioned and edited without touching code.

Usage:
    from llm_ledger import LLMClient

    client = LLMClient(
        prompts_dir="prompts/",
        audit_log="logs/llm_audit.jsonl",
    )
    response = client.reason(
        context="Analyze this text...",
        system_prompt="You are a concise summarizer.",
        prompt_name="summarize",
        model="claude-sonnet-4-6",
    )
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import anthropic

log = logging.getLogger(__name__)

# Token pricing per million — update as needed.
# See https://www.anthropic.com/pricing for current rates.
MODEL_PRICING = {
    "claude-opus-4-6":   {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6": {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5":  {"input":  0.80, "output":  4.00},
}
# No default model — callers must specify. See https://www.anthropic.com/pricing for current model IDs.


class LLMClient:
    """Claude API client with prompt loading and JSONL audit logging.

    Args:
        prompts_dir: Directory containing system prompt .txt files.
        audit_log:   Path to the JSONL audit log file. Created if it
                     doesn't exist.
        api_key:     Anthropic API key. If omitted, reads ANTHROPIC_API_KEY
                     from the environment.
    """

    def __init__(self, prompts_dir, audit_log, api_key=None):
        self.prompts_dir = Path(prompts_dir)
        self.audit_log = Path(audit_log)
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    def load_prompt(self, name: str) -> str:
        """Load a system prompt from {prompts_dir}/{name}.txt.

        Raises FileNotFoundError if the file doesn't exist — a missing
        prompt is a code bug, not a transient error.
        """
        return (self.prompts_dir / f"{name}.txt").read_text().strip()

    def reason(
        self,
        context: str,
        system_prompt: str = "",
        *,
        prompt_name: str = "",
        model: str,
        max_tokens: int = 1000,
    ) -> str | None:
        """Send context to Claude and return the response text.

        Args:
            context:       The user message / input to reason about.
            system_prompt: System prompt string. Use load_prompt() to load
                           from disk, or pass a string directly.
            prompt_name:   Label for this call in the audit log.
            model:         Claude model ID.
            max_tokens:    Maximum tokens in the response.

        Returns:
            Response text, or None if the API call failed.
        """
        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": context}],
            )
        except Exception as e:
            log.warning("API error (prompt=%s): %s", prompt_name, e)
            return None

        text = response.content[0].text
        self._audit(
            model=model,
            prompt_name=prompt_name,
            context=context,
            response=text,
            usage=response.usage,
        )
        return text

    def reason_with_prompt(
        self,
        context: str,
        prompt_name: str,
        **kwargs,
    ) -> str | None:
        """Load a prompt by name and call reason().

        Convenience method — equivalent to:
            client.reason(context, client.load_prompt(name), prompt_name=name)
        """
        system_prompt = self.load_prompt(prompt_name)
        return self.reason(context, system_prompt, prompt_name=prompt_name, **kwargs)

    def _audit(self, *, model, prompt_name, context, response, usage):
        """Append one entry to the JSONL audit log."""
        pricing = MODEL_PRICING.get(model)
        if pricing:
            cost = round(
                usage.input_tokens  * pricing["input"]  / 1_000_000
                + usage.output_tokens * pricing["output"] / 1_000_000,
                5,
            )
        else:
            cost = None  # model not in pricing dict — update MODEL_PRICING to estimate cost
        entry = {
            "ts":               datetime.now(timezone.utc).isoformat(),
            "model":            model,
            "prompt":           prompt_name,
            "context_preview":  context[:200],
            "response_preview": response[:200],
            "input_tokens":     usage.input_tokens,
            "output_tokens":    usage.output_tokens,
            "cost_est":         cost,
        }
        try:
            self.audit_log.parent.mkdir(parents=True, exist_ok=True)
            with open(self.audit_log, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as e:
            log.warning("Failed to write audit log: %s", e)
