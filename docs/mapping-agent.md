# AI Mapping Assistant Agent (Lot 4)

## Purpose

When a trace file is imported, its raw fields don't necessarily match the field names
expected by the domain (`session_id`, `occurred_at`, `input_tokens`, and the rest of
`domain/mapping/contract.py`). Rather than forcing every source to follow a fixed format,
this agent proposes a mapping between the fields observed in the file and the fields the
domain expects.

Two core design rules:

1. **The AI proposes, it never writes to the database.** It returns a proposal; it's up
   to the import engine, after user validation, to apply the transformation.
2. **An unresolved mapping stays explicit.** A target field with no proposed match is
   `null`, never a guess.

## Configuration

The AI provider is chosen via the `AI_PROVIDER` environment variable, in
`backend/.env` (see `backend/.env.example`).

| `AI_PROVIDER` | Use case                                              | Required variables                        |
|----------------|--------------------------------------------------------|--------------------------------------------|
| `fake`         | Automated tests, no network call                       | none                                       |
| `ollama`       | Local development, free, model runs on your machine    | `AI_MODEL`, `AI_BASE_URL` (optional, defaults to `http://localhost:11434/v1`) |
| `groq`         | Free cloud provider, OpenAI-compatible, no local install needed — lets anyone (teammates, reviewers) test the agent without running a model locally | `AI_MODEL`, `AI_API_KEY`, `AI_BASE_URL` (optional, defaults to `https://api.groq.com/openai/v1`) |
| `anthropic`    | Remote provider, paid                                   | `AI_MODEL`, `AI_API_KEY`                   |

By default (`AI_PROVIDER=fake`), no additional configuration is needed — this is what
the automated tests use.

Neither the model id nor the key is written in the code. A real provider configured
without `AI_MODEL` is refused at startup, with a message naming the variable to set —
rather than silently falling back to a model that may not exist any more.

### The real providers ask the same question

`infrastructure/llm/prompt.py` builds the prompt and reads the answer back for every
real provider — Ollama, Groq and Anthropic. That is not line-saving: it is what makes
the providers comparable. A difference between their proposals comes from the model, not
from a differently worded question.

The list of target fields in that prompt is read from
`domain/mapping/contract.py` — the same list the import engine enforces. Copied into an
adapter, it would drift, and the model would dutifully propose fields the engine rejects.
A proposal aimed at a field outside the contract is dropped and reported in
`unresolved_notes` rather than silently kept.

### A provider that does not answer is not an empty proposal

If the provider cannot be reached — Ollama not running, key refused, network down — the
adapter raises `MappingProposalUnavailable` and the route answers **502**. Returning an
empty proposal instead would tell the user their file matches nothing, and they would go
and fix the wrong problem.

## Testing locally with Ollama (free, runs on your machine)

1. Install [Ollama](https://ollama.com/)
2. Download a model: `ollama pull llama3.2` (or `mistral`)
3. In `backend/.env`:

```dotenv
AI_PROVIDER=ollama
AI_MODEL=llama3.2
AI_BASE_URL=http://localhost:11434/v1
```

4. Start the API: `uvicorn agentscope.main:app --reload`
5. Call the route (see below)

## Testing with Groq (free, cloud-hosted)

1. Create a free account at [console.groq.com](https://console.groq.com/) (no credit
   card required) and generate an API key
2. In `backend/.env`:

```dotenv
AI_PROVIDER=groq
AI_MODEL=openai/gpt-oss-120b
AI_API_KEY=<your Groq key>
```

3. Start the API and call the route the same way as with Ollama

Groq exposes an OpenAI-compatible API, just like Ollama — only the endpoint, the
credentials and the model catalog differ. Groq's model catalog changes over time; check
[console.groq.com/docs/models](https://console.groq.com/docs/models) if `AI_MODEL`
returns a "model not found" error.

Two local models (llama3.2 and mistral) and two independent providers — one local
(Ollama), one cloud-hosted (Groq) — were tested end-to-end (real API call, real
response) to confirm the agent works with genuinely different configurations, not just
different model names. Proposals aren't expected to be identical between providers:
smaller local models can reason less reliably about field mapping than larger cloud
models, and may occasionally return a response that isn't valid JSON. In that case the
adapter reports it in `unresolved_notes` instead of crashing or guessing — the
analyze → validate → import flow stays correct either way, which is what matters.

## HTTP routes

| Route | What it does |
|---|---|
| `GET /api/v1/mapping/fields` | The closed list of target fields, read from the domain contract |
| `POST /api/v1/mapping/propose` | Ask the configured AI provider for a mapping |
| `POST /api/v1/mapping/preview` | Dry-run a mapping on a sample — writes nothing |
| `GET`/`POST /api/v1/mappings` | The library of saved mappings |
| `DELETE /api/v1/mappings/{id}` | Remove one |

The proposal is one step of a longer journey — propose, correct, dry-run, save, import —
described end to end in [`mappings.md`](mappings.md). The AI never writes to the database,
and never gets the last word: the user corrects every cell, and the dry-run shows the values
actually read before anything is imported.

### Proposing

`POST /api/v1/mapping/propose`

**Request:**
```json
{
  "source_format": "jsonl",
  "records": [
    {"session": "sess-1", "tool": "bash"},
    {"session": "sess-2", "tool": "read_file"}
  ]
}
```

**Response:**
```json
{
  "mappings": [
    {
      "target_field": "session_id",
      "source_field": "session",
      "confidence": 0.9,
      "note": "Similar name and values consistent with a session identifier"
    },
    {
      "target_field": "cache_creation_tokens",
      "source_field": null,
      "confidence": null,
      "note": "This source does not publish the measure"
    }
  ],
  "unresolved_notes": [
    "cache_creation_tokens : This source does not publish the measure"
  ]
}
```

The `note` field explains the AI's choice (or lack of one). `unresolved_notes` collects
the notes for fields with no match, so they can be spotted without scanning every
mapping individually.

## Extending with a new provider

1. Create a class in `backend/src/agentscope/infrastructure/llm/`, implementing
   `MappingProposalPort` (see `application/ports/mapping_proposal.py`). Reuse
   `prompt.build_prompt` and `prompt.parse_proposal` so the new provider stays comparable
   with the existing ones.
2. Wire it into `build_mapping_proposal()` (`backend/src/agentscope/composition.py`),
   based on the value of `settings.ai_provider`, and add its name to `AI_PROVIDERS`
3. No other file needs to change — that's the whole point of the port

The Anthropic and Groq adapters are each about forty lines, most of them the failure
case. That is the measure of how much the port actually costs to extend.

## Tests

- `tests/application/test_build_import_sample.py`: the function that builds a sample
  from raw records
- `tests/infrastructure/test_llm_prompt.py`: the shared prompt and the reading of the
  answer — including a JSON reply wrapped in prose, an unreadable reply, and a proposal
  aimed at a field outside the contract
- `tests/infrastructure/test_ollama_mapping_proposal.py`,
  `tests/infrastructure/test_groq_mapping_proposal.py`,
  `tests/infrastructure/test_anthropic_mapping_proposal.py`: each adapter, with the
  model's response simulated (`monkeypatch`) — no network call, no key, runs in CI
- `tests/infrastructure/test_composition_ai_provider.py`: the provider choice itself, and
  the two ways of misconfiguring it
- `tests/application/test_preview_mapping.py`: the dry-run, driven by the **real**
  normalizer — the one the import uses
- `tests/application/test_saved_mappings.py`,
  `tests/infrastructure/test_sqlalchemy_mapping_store.py`: the library, in memory and
  against a real PostgreSQL
- `tests/interfaces/test_mapping_router.py`: the HTTP routes, using the `fake` test double,
  and the 502 raised by an unreachable provider

On the front, `features/import/mapping/mappingDraft.test.ts` covers the rules that matter
without mounting a screen — an empty field stays `null` rather than becoming an empty
string, and an AI proposal cannot introduce a field outside the contract.