# In-house code assistant — RAG over our GitHub repos

Python. Retrieval-augmented code assistant: index our repos, answer questions
with citations. Self-hosted models, our infrastructure, no code leaves it.

<!-- Maintainer note: this file holds decisions that differ from sensible defaults.
     Don't add things Claude can read from the codebase. Keep under ~100 lines. -->

## Architecture

Backend/RAG + Qdrant run separately from the model box. Models are two
stateless llama.cpp servers on one Azure NC4as T4 v3 (single Tesla T4, 16 GB).

- LLM: Qwen3.5-9B (GGUF quant) — OpenAI-compatible, `LLM_BASE_URL`, model id `qwen3.5-9b`
- Embedder: Qwen3-Embedding-0.6B — **1024 dims**, cosine
- Vector store: Qdrant Cloud, hybrid (dense + BM25 sparse, RRF fusion)

Never hardcode base URLs or API keys. Always `os.environ`.

## Hard constraints — these are decided, don't re-litigate

**Do NOT use vLLM.** The T4 is Turing (SM75). vLLM has no supported attention
backend for this model family on Turing; FlashAttention needs Ampere+. llama.cpp
is the only working engine here. Same for anything requiring bf16 or Marlin kernels.

**Do NOT use fixed-size / recursive character chunking.** Chunk with tree-sitter
on AST boundaries (`function_definition`, `class_definition`). A chunk must be a
complete, meaningful code unit. `RecursiveCharacterTextSplitter` and friends are wrong here.

**Do NOT disable the LLM's thinking mode globally.** Measured: disabling it drops
quality hard on reasoning and agentic coding tasks. Thinking is deliberate. Route
cheap queries away from the model instead of making the model dumber — e.g. chitchat
doesn't need the model at all.

**Always stream LLM calls** (`stream=True`). An Azure Application Gateway sits in
front and 504s on slow non-streamed responses. Thinking responses take 20-35s.

**After a local-mode write tool succeeds (create/edit/delete/run_local_command),
the final answer must NOT re-print the file's full code/content.** Confirm
briefly — what changed, file path — and stop. The code is already saved in the
file itself; repeating it in the chat is redundant noise, not a citation.

## Performance reality — design against these numbers

- Decode ~22 tok/s. A thinking request burns 400-800 tokens → **20-35s per request**.
- One T4 ≈ **5-8 concurrent users** with thinking on. This is the product ceiling.
- Assume the GPU is the scarce resource. Never move work onto it casually.
- Bulk indexing and live chat compete. Index incrementally, off-peak.
- Hard multi-file reasoning is beyond a 9B — escalate those to a frontier model
  rather than trying to squeeze it locally.

## Embedding rules — getting these wrong silently ruins retrieval

- Qwen3-Embedding 0.4 is **instruction-aware**: queries get the query prompt/prefix,
  documents do NOT. Mismatch between index-time and query-time = degraded recall.
- Dimensions (1024) and normalization must be identical at index time and query time.
- Don't index with one runtime and query with another (safetensors vs GGUF differ slightly).
- Embedder runs on CPU. Keep it there — the GPU is for generation.

## Chunk metadata is the citation

Every chunk carries `file_path`, `symbol`, `kind`, `start_line`, `end_line`.
Answers cite file + line range. A chunk without this metadata is a bug.

Large classes exceed useful chunk size — split into methods rather than emitting
one giant chunk.

## Indexing / webhook

- Point IDs are **deterministic** (hash of `file_path` + `symbol`) so re-indexing
  upserts cleanly instead of duplicating.
- On push: re-chunk only changed files; delete points for symbols that disappeared.
- The indexing pipeline must be a rerunnable script, never a manual notebook —
  the Qdrant free-tier cluster deletes itself after 4 weeks idle and we re-index.

## Qdrant

- Free tier: 1 GB RAM / 4 GB disk → ceiling ~100K chunks at 1024 dims with payload.
- Store chunk text in payload with `on_disk: true`; keep vectors in RAM.
- Currently on AWS us-east-1 while the GPU is on Azure — cross-cloud hop is known
  tech debt, not a bug to "fix" incidentally.

