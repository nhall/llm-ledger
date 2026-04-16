# llm-ledger

I got tired of losing track of what my scripts were sending to Claude. Which prompt version produced that weird output last Tuesday? How much did that batch job actually cost? This wrapper logs every API call to a JSONL file so I can answer those questions later.

It also keeps prompts in plain `.txt` files. I wanted to tweak wording without redeploying code, and I wanted prompt changes to show up in git diffs.

## Install

```bash
pip install anthropic python-dotenv
```

This isn't packaged—just drop `llm_ledger.py` somewhere in your project (I keep mine in a `lib/` folder). Then set up your API key:

```bash
cp .env.example .env
# add your Anthropic API key to .env
```

## Usage

```python
import os
from dotenv import load_dotenv
from llm_ledger import LLMClient

load_dotenv()

client = LLMClient(
    prompts_dir="prompts/",
    audit_log="logs/llm_audit.jsonl",
)
```

### Prompt from a string

```python
response = client.reason(
    context="Summarize the following: ...",
    system_prompt="You are a concise summarizer.",
    prompt_name="summarize",
    model="claude-sonnet-4-6",  # see anthropic.com/pricing for current model IDs
)
print(response)
```

### Prompt from a file

Put your system prompt in `prompts/summarize.txt`, then:

```python
response = client.reason_with_prompt(
    context="Summarize the following: ...",
    prompt_name="summarize",
    model="claude-sonnet-4-6",
)
```

### Audit log

Every call appends a line to `logs/llm_audit.jsonl`. Here's what an actual entry looks like (I ran this against a short article):

```json
{
	"ts": "2024-03-15T12:00:00+00:00",
	"model": "claude-sonnet-4-6",
	"prompt": "summarize",
	"context_preview": "Summarize the following: The comp",
	"response_preview": "The article discusses three } main",
	"input_tokens": 312,
	"output_tokens": 87,
	"cost_est": 0.00231
}
```

The previews truncate at 200 characters—enough to identify the call, not enough to bloat the file.

I mostly use this for two things: figuring out which prompt version caused a bad output (grep for the timestamp, check the `prompt` field, look at the git history for that file), and sanity-checking costs before I let a batch job run overnight.

## API

### `LLMClient(prompts_dir, audit_log, api_key=None)`

If you omit `api_key`, it reads `ANTHROPIC_API_KEY` from the environment.

| Method                                                              | What it does                                                                                                                                                                       |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reason(context, system_prompt, *, prompt_name, model, max_tokens)` | Sends a message to Claude and logs the call. Returns the response text, or `None` if the API call fails (it swallows exceptions so your batch jobs don't die on transient errors). |
| `reason_with_prompt(context, prompt_name, **kwargs)`                | Same as `reason()`, but loads the system prompt from `{prompts_dir}/{prompt_name}.txt` instead of taking it as an argument.                                                        |
| `load_prompt(name)`                                                 | Just reads `{prompts_dir}/{name}.txt` and returns the string. Useful if you need the prompt text for something else.                                                               |

### Models and pricing

Cost estimates come from `MODEL_PRICING` at the top of `llm_ledger.py`. I update it manually when Anthropic changes their rates—check [anthropic.com/pricing](https://www.anthropic.com/pricing) if the numbers look off.

## Try it

```bash
python3 example.py
```

This makes two API calls and prints the resulting log entries.
