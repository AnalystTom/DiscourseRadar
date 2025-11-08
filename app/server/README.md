# Discourse Radar - Backend Server

FastAPI backend for the Discourse Radar application.

## Setup

### 1. Install Dependencies

```bash
cd app/server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in `app/server/` based on `.env.example`:

```bash
cp ../../.env.example .env
```

Edit `.env` with your configuration:
- Set `GEMINI_API_KEY` with your Gemini API key
- Set `FIRECRAWL_API_KEY` with your Firecrawl API key
- Adjust `POSTGRES_URL` if needed

### 3. Start Database

Using Docker Compose from the project root:

```bash
cd ../..
docker compose up -d
```

This will start a Postgres database on port 5432.

### 4. Run Migrations

```bash
cd app/server
source venv/bin/activate
alembic upgrade head
```

### 5. Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## API Endpoints

### Topics
- `POST /topics` - Create a new topic
- `GET /topics` - List all topics
- `GET /topics/{id}` - Get specific topic
- `PATCH /topics/{id}` - Update topic
- `DELETE /topics/{id}` - Delete topic

### Jobs
- `POST /jobs` - Create a new job
- `GET /jobs` - List all jobs
- `GET /jobs/{id}` - Get job status
- `PATCH /jobs/{id}` - Update job
- `POST /jobs/{id}/rerun` - Rerun a job

### Documents
- `GET /documents` - List crawled documents
- `GET /documents/{id}` - Get specific document

### Clusters
- `GET /clusters` - List all clusters
- `GET /clusters/{id}` - Get specific cluster
- `GET /clusters/job/{job_id}/emerging` - Get emerging topics

### Summaries
- `GET /summaries` - List all summaries
- `GET /summaries/{id}` - Get specific summary

## Development

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

### Running Tests

```bash
pytest
```

## Project Structure

```
app/server/
├── alembic/              # Database migrations
│   └── versions/         # Migration files
├── app/
│   ├── models/           # SQLAlchemy models
│   ├── routers/          # API route handlers
│   ├── schemas/          # Pydantic schemas
│   ├── config.py         # Configuration management
│   ├── database.py       # Database connection
│   └── main.py           # FastAPI application
├── requirements.txt      # Python dependencies
└── README.md            # This file
```
