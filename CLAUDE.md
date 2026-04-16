# llm-ledger

Single-file Claude API wrapper with prompt loading and JSONL audit logging.
The entire implementation is in `llm_ledger.py`.

## What it does

- `LLMClient.reason()` — calls Claude, logs every call to a JSONL file
- `LLMClient.load_prompt()` — loads system prompts from .txt files on disk
- `LLMClient.reason_with_prompt()` — convenience: load + call in one step
- `LLMClient._audit()` — appends timestamp, model, tokens, cost estimate to JSONL

## Key design decisions

- Paths (prompts_dir, audit_log) are constructor arguments — no hardcoded paths
- API key is optional in constructor; falls back to ANTHROPIC_API_KEY env var
- `reason()` returns None on failure (never raises) — callers decide how to handle
- Pricing lives in `MODEL_PRICING` dict at module level — easy to update
- `context_preview` and `response_preview` are capped at 200 chars in the log

## Do not

- Add async support without being asked — sync is intentionally simple
- Add dependencies beyond `anthropic`
- Parse or post-process the response — that's the caller's job
