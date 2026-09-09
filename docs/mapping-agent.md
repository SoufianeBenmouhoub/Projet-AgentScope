# AI Mapping Assistant Agent (Lot 4)

## Purpose

When a trace file is imported, its raw fields don't necessarily match the field names
expected by the domain (`session_id`, `started_at`, `input_tokens`, etc.). Rather than
forcing every source to follow a fixed format, this agent proposes a mapping between the
fields observed in the file and the fields expected by the domain.

Two core design rules:

1. **The AI proposes, it never writes to the database.** It returns a proposal; it's up
   to the import engine, after user validation, to apply the transformation.
2. **An unresolved mapping stays explicit.** A target field with no proposed match is
   `null`, never a guess.

## Configuration

The AI provider is chosen via the `AI_PROVIDER` environment variable, in
`backend/.env` (see `backend/.env.example`).

| `AI_PROVIDER` | Use case                                         | Required variables                        |
|----------------|---------------------------------------------------|--------------------------------------------|
| `fake`         | Automated tests, no network call                  | none                                       |
| `ollama`       | Local development, free, model runs on your machine | `AI_MODEL`, `AI_BASE_URL` (optional, defaults to `http://localhost:11434/v1`) |
| `anthropic`    | Paid provider (untested, no budget available)     | `AI_API_KEY`, `AI_MODEL`                   |

By default (`AI_PROVIDER=fake`), no additional configuration is needed — this is what
the automated tests use.

## Testing locally with Ollama (free)

1. Install [Ollama](https://ollama.com/)
2. Download a model: `ollama pull llama3.2` (or `mistral`)
3. In `backend/.env`:

  ```dotenv
  AI_PROVIDER=ollama
  AI_MODEL=llama3.2
  ```

4. Start the API: `uvicorn agentscope.main:app --reload`
5. Call the route (see below)

Two different local models (llama3.2 and mistral) were tested to confirm the agent
stays interchangeable across models.

## HTTP route

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
      "target_field": "latency_ms",
      "source_field": null,
      "confidence": null,
      "note": "No field in the sample appears to match"
    }
  ],
  "unresolved_notes": [
    "latency_ms : No field in the sample appears to match"
  ]
}
```

The `note` field explains the AI's choice (or lack of one). `unresolved_notes` collects
the notes for fields with no match, so they can be spotted without scanning every
mapping individually.

## Extending with a new provider

1. Create a class in `backend/src/agentscope/infrastructure/llm/`, implementing
   `MappingProposalPort` (see `application/ports/mapping_proposal.py`)
2. Wire it into `build_mapping_proposal()` (`backend/src/agentscope/composition.py`),
   based on the value of `settings.ai_provider`
3. No other file needs to change — that's the whole point of the port

## Tests

- `tests/application/test_build_import_sample.py`: the function that builds a sample
  from raw records
- `tests/infrastructure/test_ollama_mapping_proposal.py`: the Ollama adapter, with the
  model's response simulated (`monkeypatch`) — no network call, runs in CI
- `tests/interfaces/test_mapping_router.py`: the HTTP route, using the `fake` test double