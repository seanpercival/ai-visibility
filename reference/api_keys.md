# API Keys — for live AI measurement (Mode B)

The URL **scan** (Mode A) needs no keys. Only **Mode B** — measuring how often a
brand actually appears in AI answers — calls the model APIs, and even then it's
optional (without keys, `prompt_panel.py` prints the panel for manual testing).

**Any single engine is enough to start.** Perplexity is the most representative
because its API retrieves the live web; the base OpenAI/Anthropic/Gemini APIs
reflect training-knowledge visibility, not live-search citations.

## Where to get each key

| Engine | Env var | Get a key |
|---|---|---|
| ChatGPT / OpenAI | `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| Perplexity | `PERPLEXITY_API_KEY` | https://www.perplexity.ai/settings/api |
| Claude / Anthropic | `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys |
| Google Gemini | `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey |

Run `python3 scripts/prompt_panel.py keys` to print this list plus which keys are
currently set.

## How to store them

Create a `.env` file in the folder you run the scripts from, one key per line:

```
OPENAI_API_KEY=sk-...
PERPLEXITY_API_KEY=pplx-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
```

`prompt_panel.py` auto-loads `.env` on every run. You can also just `export` the
vars in your shell instead.

## Security

- `.env` is **gitignored** — never commit it.
- Keys are not written to memory or logs; mask them if you ever print one (`sk-abc…`).
- Delete `.env` anytime to revoke local access.
- Optional model overrides (advanced): `OPENAI_MODEL`, `PERPLEXITY_MODEL`,
  `ANTHROPIC_MODEL`, `GEMINI_MODEL`.
