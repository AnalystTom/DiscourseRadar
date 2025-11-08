# SaaS: First-Person Discourse Scout (Agentic)

## Goal

Build a production-ready, multi-tenant SaaS that discovers, ingests, and summarizes **first-person discourse** from the open web (e.g., Reddit and forums), surfaces **emerging topics**, and powers **agentic workflows** (alerting, clustering, summaries, exports).

## Repo layout

* `app/client` – Frontend (ag-ui based, React/Vite)
* `app/server` – Backend (FastAPI + LangChain agents + Gemini API + Firecrawl integration)

## Core capabilities (MVP)

1. Topic tracking: submit topics/queries; agent discovers relevant sources via Firecrawl, prioritizes forums/Reddit.
2. Ingestion & normalization: pull HTML → clean markdown/JSON; capture metadata (URL, title, author handle when available, timestamps).
3. Agentic analysis: LangChain ReAct agent uses tools to crawl, chunk, embed, cluster, summarize, and score "emerging topics". ReAct loop iterates until stop condition is met (final answer or iteration cap) ([LangChain Docs][1]).
4. Generative UI: ag-ui chat + "Generative UI" panels for insights, deep dives, and human-in-the-loop approvals (interrupts, retries, escalations) ([docs.ag-ui.com][2]).
5. Deployment: containerized services on **GCP Cloud Run**; CI/CD for server and client; secrets in GCP Secret Manager; HTTPS on custom domain; autoscaling. Cloud Run FastAPI quickstart docs referenced here for build/deploy flow ([Google Cloud Documentation][3]).

## Compliance & platform policy guardrails

* **Reddit**: follow Data API Terms; expect restrictions/rate-limiting and prefer API/approved methods where possible ([Reddit Inc][4]).
* **Context**: Reddit has tightened scraping and access (robots updates, archival access changes), so respect robots.txt and platform rules and provide customer override lists of allowed sources ([Reuters][5]).
* **Firecrawl**: heed API rate limits and error codes (e.g., 429) and implement retries/backoff ([docs.firecrawl.dev][6]).

---

## High-level architecture

### Data flow

1. **User topic request** (client) → **/jobs** (server)
2. **ReAct agent** kick-off: selects tools and plans steps (search → crawl → extract → summarize/cluster) until a stop condition is met; tool use occurs inside the ReAct loop ([LangChain Docs][1]).
3. **Firecrawl tool**: given seed URLs/queries, fetches pages and subpages and returns clean markdown/structured data; handle pagination and job polling; watch rate limits and 4xx/5xx ([GitHub][7]).
4. **LLM processing (Gemini API)**: summarization, sentiment, topic extraction, topic shift detection, and "emerging topic" scoring; Gemini API setup and usage patterns per official docs or the `google-genai` SDK ([Google AI for Developers][8]).
5. **Storage** (MVP): Postgres (topics, jobs, documents, clusters, summaries), object store for raw HTML if needed.
6. **Frontend**: ag-ui chat & event stream, "Generative UI" panes for forms/tables/cards, "Interrupts" for human approvals, "Frontend tool calls" to run client-side actions, and "Thinking steps" visualized without exposing raw CoT ([docs.ag-ui.com][2]).
7. **Deploy**: each app builds to its own container and runs on Cloud Run; refer to FastAPI on Cloud Run quickstart for service setup & buildpacks; configure concurrency, autoscaling, and min instances as needed ([Google Cloud Documentation][3]).

---

## External references

* **LangChain Agents (Python)** — ReAct, tools, middleware, error handling, structured output, dynamic system prompts ([LangChain Docs][1])
* **ag-ui** — Generative UI (static/declarative), streaming, interrupts, frontend/back-end tool rendering, shared state, thinking steps ([docs.ag-ui.com][2])
* **Firecrawl** — API reference, rate limits, job management, markdown/structured output, GitHub repo overview ([docs.firecrawl.dev][6])
* **Gemini API** — official docs + Python SDK (`google-genai`) ([Google AI for Developers][8])
* **Cloud Run** — FastAPI deploy quickstart (build from source or Dockerfile) ([Google Cloud Documentation][3])
* **Reddit policies** — Data API Terms and news context (robots/archival restrictions) for compliant usage ([Reddit Inc][4])

---

## Environment & config (shared)

Define these as secrets/vars in local `.env` and in Cloud Run:

* `GEMINI_API_KEY` – key for Gemini Developer API.
* `FIRECRAWL_API_KEY` – key for Firecrawl.
* `APP_ENV` – `local|staging|prod`.
* `POSTGRES_URL` – SQLAlchemy-style DSN.
* `ALLOWED_SOURCES` – comma-separated base domains; default to allow-list.
* `REDDIT_COMPLIANCE_MODE` – `api_only|mixed|strict_api`.
* `MAX_CRAWL_DEPTH`, `CRAWL_CONCURRENCY`, `CRAWL_INTERVAL_SECONDS`.
* `EMERGING_TOPIC_THRESHOLD` – cluster growth/rate threshold.
* `GCLOUD_PROJECT`, `REGION`, `CLIENT_URL`, `SERVER_URL`.

---

## Backend (`app/server`) — step-by-step plan

### 1) Project scaffolding

* Initialize FastAPI app with routers: `/health`, `/auth` (optional), `/topics`, `/jobs`, `/docs`, `/clusters`, `/summaries`.
* Add pydantic models: TopicCreate, JobCreate, Document, Cluster, Summary.
* Setup DB via SQLAlchemy + Alembic migrations.

### 2) Firecrawl integration (tooling layer)

* Create a `firecrawl_client` with:

  * `submit_crawl(url|query, options)` → job_id
  * `get_job(job_id)` → status/results
  * `fetch(url)` → single-page extract (markdown/JSON)
* Implement retry/backoff on `429` and other transient codes; bubble structured error messages to the agent tool error handling (LangChain middleware recommends custom tool-call wrappers) ([LangChain Docs][1]).

### 3) LangChain agent (ReAct)

* Use **ReAct loop with tools**. Provide tools:

  * `search_and_seed(topic)` – derive seed URLs (simple Google/Bing or curated list of forum entry points).
  * `firecrawl_crawl(url|query)` – use the client above to crawl + return normalized docs.
  * `analyze_documents(docs)` – calls Gemini for summarization, sentiment, entities.
  * `cluster_and_score(docs)` – embedding + clustering (e.g., cosine + HDBSCAN or simple k-means MVP) + "emerging topic" scoring (growth rate + novelty).
  * `persist_results(...)` – store docs/summaries/clusters.
* Add **error handling middleware** for tools to return friendly `ToolMessage` on exceptions, as recommended by LangChain agents docs (tool error handling) ([LangChain Docs][1]).
* Add **dynamic system prompt** middleware for persona/guardrails (e.g., compliance mode instructions, allowed sources, cost/time budgets) per LangChain patterns ([LangChain Docs][1]).
* Stop conditions: iteration cap, token cap, or convergence (no new results).

### 4) Gemini API calls

* Use `google-genai` (Gemini Developer API) to:

  * Summarize threads; extract sentiments & stances; generate key quotes; produce TL;DR + "why it matters".
  * Produce **UI schemas** for ag-ui's Generative UI (e.g., JSON schema for result tables/forms) to drive client rendering ([Google AI for Developers][8]).
* Maintain configurable `temperature` and max tokens per task.

### 5) API surface (FastAPI)

* `POST /topics` – create topic tracking job.
* `POST /jobs` – start ad-hoc crawl/analysis run.
* `GET /jobs/{id}` – job status & partial results streaming (Server-Sent Events or WebSocket).
* `GET /topics/{id}/insights` – summaries, clusters, shift metrics, supporting quotes (with source links).
* `POST /rerun` – on-demand re-analysis with changed thresholds.

### 6) Observability

* Structured logs for agent steps, tool calls, token usage; persist traces for debugging.
* Capture "thinking steps" for UI visualization without exposing raw chain-of-thought (ag-ui pattern) ([docs.ag-ui.com][2]).

### 7) Policy guardrails

* Enforce **allow-list** domains by default; add per-customer allow-list.
* Respect robots/meta directives; halt on disallowed sources.
* Provide `REDDIT_COMPLIANCE_MODE` to choose API-only or mixed (API when available; scraper fallback disabled if disallowed) with doc links to Reddit Data API Terms ([Reddit Inc][4]).

---

## Frontend (`app/client`) — step-by-step plan

### 1) Scaffolding

* React + Vite app with ag-ui wiring (chat surface + side panels).
* Route structure: `/` chat + insight feed; `/topics/:id` deep dive; `/settings` compliance & thresholds.

### 2) ag-ui integration

* **Streaming chat** with live events so users see tool progress; **interrupts** to approve/stop/resume mid-flow; **frontend tool calls** for local actions (e.g., copy/export, open links) ([docs.ag-ui.com][2]).
* **Generative UI (static & declarative)**: render LLM-proposed tables/cards/forms in a validated, typed way; server controls approval and mounting; small declarative language per ag-ui "Generative UI" draft ([docs.ag-ui.com][2]).
* **Thinking steps**: visualize intermediate tool events rather than raw CoT (compliance-friendly) ([docs.ag-ui.com][2]).

### 3) UX primitives

* Topic composer → kick off jobs.
* Insight feed: cluster tiles with sparkline (volume over time), sentiment, novelty badge.
* Deep dive: timeline of posts, top quotes, source links, network mini-graph.
* Export buttons (CSV/JSON/PDF).

---

## Local development

### Prereqs

* Python 3.11+, Node 18+, Docker, `gcloud` CLI, Postgres (Docker or managed).
* Acquire `GEMINI_API_KEY` and `FIRECRAWL_API_KEY` (see docs for each) ([Google AI for Developers][8]).

### Steps

1. Checkout repo; create `.env` in root with variables listed above.
2. Start Postgres locally (e.g., Docker) and run migrations.
3. In `app/server`: install deps; run FastAPI with reload; ensure `/health` OK.
4. In `app/client`: install deps; run dev server; set `SERVER_URL`.
5. Create a test topic (e.g., "local models for AI news"); verify job runs and partial results stream.
6. Validate that disallowed domains are ignored and that Reddit compliance mode is respected.

---

## Deployment (GCP Cloud Run)

### One-time setup

* Create **GCP project**, enable Cloud Run & Artifact Registry.
* Configure **Secret Manager** for `GEMINI_API_KEY`, `FIRECRAWL_API_KEY`, `POSTGRES_URL`.
* Choose a **managed Postgres** (Cloud SQL) or hosted alternative.
* Set IAM for deployer and runtime service accounts.

### Build & deploy (reference quickstart)

* You can deploy FastAPI directly from source using Cloud Run's buildpacks or via Docker image; follow the official **FastAPI on Cloud Run quickstart** for exact steps (source deploy, detected entrypoint, URL provisioning) ([Google Cloud Documentation][3]).
* Create two services:

  * `discourse-server` → expose `/` (FastAPI), min instances e.g., 0–1; set env via secrets; set concurrency (e.g., 80).
  * `discourse-client` → static assets built and served (use Cloud Run service or Cloud Storage + CDN).
* Map custom domain, enforce HTTPS, set autoscaling, and request timeouts appropriate for agent runs.

### CI/CD

* Cloud Build triggers on main branch; build images for server/client; run unit tests; migrate DB; deploy to Cloud Run.
* Observability: Cloud Logging, Error Reporting; export to BigQuery if needed.

---

## Agent behavior (prompting & middleware)

### System/Tooling principles

* The **agent** must: plan briefly, call tools, observe, iterate, and **only** conclude when a final, verifiable answer is ready (ReAct) ([LangChain Docs][1]).
* Tooling rules:

  * Prefer **Firecrawl** for crawl/extract; obey rate limits; exponential backoff on `429`; respect `ALLOWED_SOURCES` ([docs.firecrawl.dev][6]).
  * Use **Gemini** for summarization, topic extraction, schema generation for UI, and concise rationales ([Google AI for Developers][8]).
  * Use **error-handling middleware** to convert exceptions to helpful ToolMessages so the model continues gracefully ([LangChain Docs][1]).
* **Dynamic system prompt** middleware injects compliance mode, budget limits, and persona based on tenant context ([LangChain Docs][1]).

### Output contracts (for UI)

* Agent should return:

  * A machine-readable `insight_bundle` (topics, clusters, sentiments, trends) + a **UI description/schema** for ag-ui to render (tables/cards/forms) following the Generative UI draft approach (two-step generation: describe UI → generate structured UI → validate → mount) ([docs.ag-ui.com][2]).
  * A concise user-facing summary and a link list with source attributions.

---

## Security, privacy, ethics

* Only ingest public pages from allowed domains; honor robots/terms.
* Avoid PII extraction; add auto-redaction pass.
* Keep raw HTML optional and behind access controls.
* Provide a tenant-level "Do Not Crawl" list and a "Right to Remove" workflow.

---

## Roadmap (post-MVP)

* Source adapters (Hacker News, niche boards) with per-site policies.
* Slack/Teams alerts when "emerging topic" threshold crossed.
* Multi-agent composition (sub-agents for clustering vs. summarization) and **interrupts** for approvals ([docs.ag-ui.com][2]).
* Export to decks (weekly narrative reports).
* Billing and usage metering.

---

## Testing checklist

* Unit: Firecrawl client, Gemini summarizer, clusterer, middleware.
* E2E: topic → crawl → cluster → insights visible in UI; verify interrupts resume state.
* Load: many concurrent jobs; confirm backoff on Firecrawl and Cloud Run autoscaling.
* Policy: confirm Reddit API mode behaves per Data API Terms and robots controls are enforced ([Reddit Inc][4]).

---

## Appendix: Links

* LangChain Agents (ReAct, tools, middleware): see "Agents" and "Tool use in the ReAct loop," "Tool error handling," and "Dynamic system prompt." ([LangChain Docs][1])
* ag-ui (Generative UI, streaming, interrupts, frontend tool calls, shared state, thinking steps): see docs & draft spec ([docs.ag-ui.com][2])
* Firecrawl (intro, API, rate limits), GitHub overview: ([docs.firecrawl.dev][6])
* Gemini API docs + Python SDK: ([Google AI for Developers][8])
* Cloud Run (FastAPI quickstart): ([Google Cloud Documentation][3])
* Reddit Data API Terms / crawler policy context: ([Reddit Inc][4])

---

If you want, I can also spin up a minimal **project board** (tasks/issues) from this README so an agent or teammate can pick up each step in order.

[1]: https://docs.langchain.com/oss/python/langchain/agents "Agents - Docs by LangChain"
[2]: https://docs.ag-ui.com/llms-full.txt "docs.ag-ui.com"
[3]: https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-fastapi-service?utm_source=chatgpt.com "Quickstart: Deploy a Python (FastAPI) web app to Google Cloud with ..."
[4]: https://redditinc.com/policies/data-api-terms?utm_source=chatgpt.com "Data API Terms - Reddit"
[5]: https://www.reuters.com/technology/reddit-update-web-standard-block-automated-website-scraping-2024-06-25/?utm_source=chatgpt.com "Reddit to update web standard to block automated website scraping"
[6]: https://docs.firecrawl.dev/api-reference/v2-introduction?utm_source=chatgpt.com "Introduction - Firecrawl Docs"
[7]: https://github.com/firecrawl/firecrawl?utm_source=chatgpt.com "firecrawl/firecrawl: The Web Data API for AI - GitHub"
[8]: https://ai.google.dev/gemini-api/docs?utm_source=chatgpt.com "Gemini API | Google AI for Developers"
