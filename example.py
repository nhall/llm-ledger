"""
Example usage of llm-ledger.

Requires ANTHROPIC_API_KEY in your environment or a .env file.
See .env.example.

Run:
    python3 example.py
"""

import json
import os
from dotenv import load_dotenv
from llm_ledger import LLMClient

load_dotenv()

client = LLMClient(
    prompts_dir="prompts/",
    audit_log="logs/llm_audit.jsonl",
)

# --- 1. Inline system prompt ---
print("1. Inline prompt")
response = client.reason(
    context="What is 2 + 2?",
    system_prompt="You are a concise assistant.",
    prompt_name="math",
    model="claude-haiku-4-5",
)
print(f"   {response}\n")

# --- 2. System prompt loaded from prompts/test.txt ---
print("2. Prompt from file (prompts/test.txt)")
response = client.reason_with_prompt(
    context="Say hello in one word.",
    prompt_name="test",
    model="claude-haiku-4-5",
)
print(f"   {response}\n")

# --- 3. Inspect the audit log ---
print("3. Audit log (logs/llm_audit.jsonl)")
with open("logs/llm_audit.jsonl") as f:
    entries = [json.loads(line) for line in f]
for e in entries:
    print(f"   [{e['prompt']}] {e['input_tokens']} in / {e['output_tokens']} out — cost_est ${e['cost_est']}")
