# Development Tasks - First-Person Discourse Scout

Tasks organized in sequential order for building the application.

---

## Phase 1: Project Setup & Infrastructure

### 1.1 Repository Structure
- [ ] Create `apps/server` and `apps/client` directories
- [ ] Initialize `.env.example` with all required environment variables
- [ ] Setup `.gitignore` for Python and Node artifacts

### 1.2 Database Setup
- [ ] Setup local Postgres (Docker Compose recommended)
- [ ] Configure SQLAlchemy in `apps/server`
- [ ] Initialize Alembic for migrations
- [ ] Create initial migration

### 1.3 Environment Configuration
- [ ] Acquire Gemini API key
- [ ] Acquire Firecrawl API key
- [ ] Create local `.env` file with all secrets
- [ ] Document environment variable descriptions

---

## Phase 2: Backend Foundation (apps/server)

### 2.1 FastAPI Scaffolding
- [ ] Initialize FastAPI app with basic structure
- [ ] Create router modules: `health.py`, `topics.py`, `jobs.py`, `clusters.py`, `summaries.py`
- [ ] Setup CORS middleware for local development
- [ ] Implement `/health` endpoint

### 2.2 Database Models
- [ ] Create SQLAlchemy models: `Topic`, `Job`, `Document`, `Cluster`, `Summary`
- [ ] Define relationships between models
- [ ] Create Pydantic schemas: `TopicCreate`, `JobCreate`, `TopicResponse`, etc.
- [ ] Run migrations to create tables

### 2.3 Configuration Management
- [ ] Create `config.py` for environment variable loading
- [ ] Implement settings validation with Pydantic
- [ ] Setup structured logging configuration

---

## Phase 3: External Integrations

### 3.1 Firecrawl Client
- [ ] Create `clients/firecrawl_client.py`
- [ ] Implement `submit_crawl(url, options)` → returns job_id
- [ ] Implement `get_job(job_id)` → returns status/results
- [ ] Implement `fetch(url)` → single-page extract
- [ ] Add retry logic with exponential backoff for 429/5xx errors
- [ ] Add error handling and structured error messages

### 3.2 Gemini API Integration
- [ ] Install `google-genai` SDK
- [ ] Create `clients/gemini_client.py`
- [ ] Implement summarization function
- [ ] Implement sentiment/stance extraction
- [ ] Implement topic extraction and scoring
- [ ] Add configurable temperature and token limits

---

## Phase 4: LangChain Agent & Tools

### 4.1 Agent Tools
- [ ] Create `tools/search_and_seed.py` - derives seed URLs from topics
- [ ] Create `tools/firecrawl_crawl.py` - wraps Firecrawl client
- [ ] Create `tools/analyze_documents.py` - calls Gemini for analysis
- [ ] Create `tools/cluster_and_score.py` - embedding + clustering logic
- [ ] Create `tools/persist_results.py` - saves to database

### 4.2 ReAct Agent Setup
- [ ] Install LangChain dependencies
- [ ] Create `agent/react_agent.py` with tool registry
- [ ] Implement error handling middleware for tools
- [ ] Implement dynamic system prompt middleware
- [ ] Configure stop conditions (iteration cap, token cap, convergence)

### 4.3 Compliance & Policy Layer
- [ ] Create `compliance/source_validator.py` for allow-list enforcement
- [ ] Implement robots.txt checker
- [ ] Add Reddit compliance mode logic (api_only/mixed/strict_api)
- [ ] Create domain filtering logic

---

## Phase 5: Backend API Endpoints

### 5.1 Core Endpoints
- [ ] `POST /topics` - create topic tracking job
- [ ] `POST /jobs` - start ad-hoc crawl/analysis
- [ ] `GET /jobs/{id}` - job status and results
- [ ] `GET /topics/{id}/insights` - summaries, clusters, metrics
- [ ] `POST /jobs/{id}/rerun` - re-analyze with new thresholds

### 5.2 Streaming Support
- [ ] Implement Server-Sent Events for job progress
- [ ] Add WebSocket support (optional, for real-time updates)
- [ ] Create event serialization for agent steps

### 5.3 Observability
- [ ] Add structured logging for all agent steps
- [ ] Log tool calls, token usage, and errors
- [ ] Capture "thinking steps" for UI visualization
- [ ] Setup log persistence strategy

---

## Phase 6: Frontend Foundation (apps/client)

### 6.1 React + Vite Setup
- [ ] Initialize Vite app with React and TypeScript
- [ ] Install ag-ui dependencies
- [ ] Setup React Router with routes: `/`, `/topics/:id`, `/settings`
- [ ] Configure API client (Axios/Fetch) pointing to backend

### 6.2 ag-ui Integration
- [ ] Setup ag-ui chat surface component
- [ ] Implement streaming event handler
- [ ] Create message display components
- [ ] Setup interrupt handling (approve/stop/resume)

### 6.3 UI Components Library
- [ ] Create base component library (buttons, cards, inputs)
- [ ] Implement topic composer form
- [ ] Create loading/skeleton states
- [ ] Setup error boundary components

---

## Phase 7: Frontend Features

### 7.1 Main Dashboard
- [ ] Build chat interface with ag-ui streaming
- [ ] Create insight feed with cluster tiles
- [ ] Add sparkline charts for volume over time
- [ ] Implement sentiment and novelty badges

### 7.2 Deep Dive View
- [ ] Create `/topics/:id` page layout
- [ ] Build timeline of posts component
- [ ] Display top quotes with source links
- [ ] Add network mini-graph visualization (optional for MVP)

### 7.3 Generative UI Components
- [ ] Implement declarative UI renderer for LLM-proposed tables
- [ ] Create validated form renderer
- [ ] Add card/tile dynamic renderer
- [ ] Implement thinking steps visualization

### 7.4 Settings & Controls
- [ ] Create settings page for compliance configuration
- [ ] Add threshold adjustment controls
- [ ] Implement export functionality (CSV/JSON/PDF)
- [ ] Add source allow-list management UI

---

## Phase 8: Integration & Testing

### 8.1 Integration Testing
- [ ] Test end-to-end flow: topic creation → crawl → analysis → UI display
- [ ] Verify compliance mode enforcement
- [ ] Test interrupt/resume functionality
- [ ] Validate export features

### 8.2 Unit Testing
- [ ] Write tests for Firecrawl client (mock API responses)
- [ ] Write tests for Gemini integration
- [ ] Write tests for clustering logic
- [ ] Write tests for compliance/policy layer

### 8.3 Load & Performance Testing
- [ ] Test concurrent job handling
- [ ] Verify backoff logic under rate limits
- [ ] Test database query performance with large datasets
- [ ] Profile agent execution times

---

## Phase 9: GCP Cloud Run Deployment

### 9.1 GCP Setup
- [ ] Create GCP project
- [ ] Enable Cloud Run, Artifact Registry, Secret Manager APIs
- [ ] Setup Cloud SQL Postgres instance (or alternative)
- [ ] Configure IAM roles and service accounts

### 9.2 Secret Management
- [ ] Upload `GEMINI_API_KEY` to Secret Manager
- [ ] Upload `FIRECRAWL_API_KEY` to Secret Manager
- [ ] Upload `POSTGRES_URL` to Secret Manager
- [ ] Configure secret access permissions

### 9.3 Backend Deployment
- [ ] Create Dockerfile for `apps/server` (or use buildpacks)
- [ ] Build and push server image to Artifact Registry
- [ ] Deploy `discourse-server` to Cloud Run
- [ ] Configure environment variables and secrets
- [ ] Set autoscaling (min/max instances, concurrency)
- [ ] Test `/health` endpoint

### 9.4 Frontend Deployment
- [ ] Build production bundle for `apps/client`
- [ ] Create Dockerfile for static serving (or use Cloud Storage)
- [ ] Deploy `discourse-client` to Cloud Run
- [ ] Configure `SERVER_URL` environment variable
- [ ] Setup custom domain and HTTPS

### 9.5 CI/CD Pipeline
- [ ] Create Cloud Build configuration
- [ ] Setup triggers for main branch
- [ ] Add build steps: test → migrate → deploy
- [ ] Configure deployment notifications

---

## Phase 10: Post-MVP Enhancements (Optional)

- [ ] Add Slack/Teams webhook alerts for emerging topics
- [ ] Implement billing and usage metering
- [ ] Add support for additional sources (Hacker News, niche forums)
- [ ] Create weekly narrative report exports (PDF/slide deck)
- [ ] Implement multi-agent composition for specialized tasks
- [ ] Add tenant-level "Do Not Crawl" and "Right to Remove" workflows

---

## Notes

**Dependencies:**
- Phase 2 requires Phase 1 completion
- Phase 4 requires Phase 3 completion
- Phase 5 requires Phase 4 completion
- Phase 6 can start in parallel with Phase 4-5
- Phase 7 requires Phase 5 (for API integration)
- Phase 9 requires Phase 8 (testing before production deploy)

**Critical Path:**
Setup → Backend Foundation → Integrations → Agent → API → Frontend → Testing → Deployment

**Estimated Duration:**
- MVP (Phases 1-8): 6-8 weeks with dedicated team
- Production Deployment (Phase 9): 1-2 weeks
- Post-MVP features: Ongoing
