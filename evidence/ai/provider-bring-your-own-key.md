# Bring-your-own-AI-provider — current state, gaps, and the minimal build

**Author:** `opencode` · **Date:** 2026-10-06 · **Status:** review, no code change
**Scope:** can a user type a base URL + API key + model name and have the tool talk to that
provider? Read-only audit of `app/engine/ai/**` and `app/api/main.py` against `docs/10`
§2–§3, `docs/13` §11, `ADR-010`.

## 1. Answer

**Yes — and roughly 85% of it is already implemented.** The user-facing flow *"paste a base
URL, paste a key, name a model, verify the connection"* is the designed flow of `docs/10` §3,
not a feature request. The remaining work is hardening and persistence, not capability.

## 2. What already exists (verified at file:line)

| Capability | Where | Note |
|---|---|---|
| Provider/base-URL/key/model config object | `app/engine/ai/client.py:42-57` | `provider` ∈ {`none`, `openai_compatible`, `azure_openai`}, `base_url`, `api_key`, `model`, `api_version`, `temperature`, `timeout_seconds` (30 s), `max_retries` (2), redaction switches |
| Enabled/disabled + credential check | `client.py:962-970` (`is_configured`) | keyless ⇒ rule-based fallback, never a failed call |
| URL + header construction | `client.py:1008-1036` (`_build_request_params`) | Azure: `api-key` header + `/openai/deployments/{model}/chat/completions?api-version=…`; otherwise `Authorization: Bearer` + `{base_url}/chat/completions`; tolerates a pasted base URL that already ends in `/chat/completions`; sends `response_format: {"type":"json_object"}` |
| Retry / backoff / error classification | `client.py:1124-1157` | 429 and ≥500 retried; 401/403 terminal; timeout vs network distinguished; every failure ends in rule-based fallback with a warning |
| Data-free connection probe | `client.py:972-1006` (`test_connection`) | the `10` §3.2 "verify against the provider" action |
| Settings read/update API, key masked | `app/api/main.py:1539-1575` | `GET/POST /api/v1/ai/config`; response returns `key[:6]…key[-4:]` or `••••••••`, never the raw key |
| Connection-test API | `app/api/main.py:1577-1597` | `POST /api/v1/ai/test-connection` |
| Payload redaction + injection defence | `client.py:88-307` (`RedactionEngine`) | vendor pseudonymisation (stable `Vendor A/B/…` mapping, reversed locally), description masking (email/URL/phone/long-digit runs), confidential amounts, custom regex masks, and sanitisation of `</data>` delimiter escapes, control chars, zero-width and bidi-override characters |
| Output validation pipeline | `client.py:315-485`, `1038-1274` | strict JSON parse → `jsonschema` against the template `output_schema` → banned verdict phrases → evidence-ID stripping → **DEC-026 sentence-level number reconciliation** → deterministic fallback if the whole draft was stripped |
| Deterministic rule-based fallback for all four prompts | `client.py:630-930` | labelled *"Rule-based summary"*, never presented as AI (`10` §2.4) |
| Prompt template registry | `client.py:530-623` + `engine/ai/prompts/PROMPT-0*.v1.md` | `prompt_id`, `version`, `feature_code`, input/output schemas, token caps; refuses unresolved `{{TOKEN}}` |
| Model pinning | `app/engine/ai/pinning.py` | satisfies `10` §10 pinning intent |
| Token / cost caps and usage log | `app/engine/ai/usage.py`, `guardrails.py:758-763` | per-call and monthly caps (`10` §9) |

**Provider coverage today:** everything that speaks the OpenAI chat-completions shape —
Gemini (via `https://generativelanguage.googleapis.com/v1beta/openai/`, verified in Google's
own OpenAI-compatibility docs, which also documents structured output and embeddings on that
endpoint), Groq, Together, Fireworks, DeepSeek, OpenRouter, Mistral, xAI, Perplexity,
Azure OpenAI (special-cased), and locally Ollama (`/v1`), llama.cpp `llama-server`, LM Studio,
vLLM. Providers that are *not* OpenAI-shaped (Anthropic Messages API, Cohere, some enterprise
gateways) need a small adapter each: one branch in `_build_request_params` plus response
parsing — roughly 20 lines and one test apiece.

## 3. Gaps between the code and `docs/10` / `docs/13`

| # | Gap | Evidence | Consequence |
|---|---|---|---|
| **G1** | **API key is stored in an environment variable, not DPAPI** | `app/api/main.py:1568` sets `os.environ["FPA_AI_API_KEY"]`; read back via `AIConfig.from_env()` (`main.py:1545`). A grep for `DPAPI` / `CryptProtect` / `AppSetting` across `app/engine/ai` returns nothing | The key **does not survive a restart** (retyped every launch), and env vars leak into child processes and crash dumps. `13` §11 and `09` §10 require the AI key in machine-level SQLite under Windows DPAPI / Credential Manager |
| **G2** | **No HTTPS-unless-localhost validation** | no scheme check anywhere in `_build_request_params`; `10` §3.2 requires "validated as HTTPS; non-HTTPS is refused unless it is `localhost`" | A typo'd or malicious base URL receives the Bearer token. Inherent to BYO-provider, so it must be mitigated explicitly |
| **G3** | **No egress policy** | nothing in `AIConfig` distinguishes deployments that may not reach the internet | For a bank client this is the blocker: there is no supported way to say "AI must stay on this machine" |
| **G4** | **No per-call audit row** | `AiUsageLog` (`usage.py:20-47`) records tokens/cost/outcome but not `prompt_id`, version, payload hash, latency | `10` §9.3 requires every call logged locally; a security reviewer will ask for exactly this |
| **G5** | **Model name must be typed blind** | no `GET {base}/models` probe, no provider presets | Typos surface only as a fallback with a vague warning |
| **G6** | **AI calls are synchronous with a 30 s timeout** | `client.py:1124-1157` blocking `httpx` call inside the request path | A 300–400 exception grouping call (`PROMPT-03`) can exceed it; no progress, no cancellation. `app/jobs/` (TB-025) is the intended home |

Not a gap, worth recording: `response_format` is sent as `{"type":"json_object"}`, not
`json_schema`, so structured output relies on prompt discipline plus the strict post-validation
and fallback. That is defensible (the validator is the real guarantee), but it means more
wasted tokens on malformed drafts than a schema-constrained request would cost.

## 4. Minimal build that turns demo into product

Ordered by value per hour. No new dependency, no model download, no R9 event — all of it
inside the existing architecture.

| # | Change | Closes | Est. |
|---|---|---|---|
| 1 | Persist settings in SQLite `AppSetting` (machine layer); key encrypted with DPAPI; per-provider key slots so switching providers never clobbers another provider's key | G1 | ½ day |
| 2 | Validate scheme (HTTPS unless `localhost`/`127.0.0.1`) before the first call; show the resolved host in the save dialog | G2 | 2 h |
| 3 | Add `local_only` / `cloud_allowed` egress policy to `AIConfig`; refuse non-localhost endpoints when `local_only` | G3 | 2 h |
| 4 | Per-call audit row: timestamp, `prompt_id`+version, model, provider, token counts, **payload hash (never payload)**, response hash, latency, outcome | G4 | ½ day |
| 5 | Provider presets that prefill base URL (Gemini / Ollama / llama.cpp / LM Studio / Azure) + "fetch available models" button | G5 | 2 h |
| 6 | Route long AI calls through the jobs registry (progress, cancel, and a per-job timeout that is not the HTTP default) | G6 | ½ day |

Items 1–3 are the demo-to-product delta and, in my judgement, items 2–3 are what make the
feature sellable to a financial client rather than merely usable.

## 5. Security notes specific to user-entered endpoints

- **The key is a bearer token to a user-chosen host.** Unavoidable for BYO-provider; therefore
  the HTTPS-unless-localhost rule, the visible resolved host, per-provider key storage, and
  never logging the key are all mandatory rather than nice-to-have.
- **Keys must never reach the repository or a project file.** `13` §11: keys live in machine-level
  storage only, never in project files, backups, logs or exports; backups must carry no secrets
  (`FR-PRJ-008`, which has its own test).
- **Payload minimisation before any cloud endpoint.** Send engine-derived aggregates (counts,
  thresholds, top-N lines, rule ids), not row-level vendor/bank detail. The redaction engine
  already exists; the policy decision is what goes in the payload at all.
- **Localhost is already permitted by spec** (`10` §3.2, documented "for a local gateway"), which
  is what lets a llama.cpp/Ollama sidecar work with zero code change and zero new dependency.

## 6. Recommended sequence

1. Land gaps **G1–G3** (secure persistence, scheme validation, egress policy).
2. Point a Gemini free-tier key at `https://generativelanguage.googleapis.com/v1beta/openai/`
   with a pinned model, and run the four `PROMPT-0*` templates over the **sample** corpus.
   Score on the guardrail metrics that already exist: number-mismatch rate, schema-fallback
   rate, banned-phrase hits, and "accepted without edit" by a human reviewer. Decide on the
   numbers, not on the benchmark tables.
3. Add the surface area (`local_only` per deployment for bank clients, optional cloud for
   clients whose data-processing terms allow it), and keep the keyless rule-based fallback as
   the always-available path.

## 7. Governance

No new runtime dependency is introduced by any item above, so **R9 is not triggered**. `ADR-010`
("OpenAI-compatible HTTP interface over `httpx`, no vendor SDK") remains satisfied — Gemini,
Ollama and llama.cpp are all reached through the same `chat/completions` shape. Any change that
adds a *native* vendor adapter (Anthropic Messages, Cohere) is an ADR amendment and goes to the
leader as an ADR + DEC row (`docs/09`, `docs/18`).

## 8. Limits of this review

Verified by reading `app/engine/ai/client.py`, `usage.py`, `pinning.py`, `guardrails.py` and
`app/api/main.py`, plus greps for scheme validation and secret storage. **Not** verified: live
calls to any provider (no key was available and none was used), the Gemini OpenAI-compatibility
endpoint's behaviour against this specific client (the docs confirm the endpoint exists and
supports structured output), and any quota or pricing figure — those must be read from the
provider's own dashboard/console for the account in question.