"""Crawler service for orchestrating web crawling and analysis."""

import logging
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.clients.firecrawl_client import FirecrawlClient, FirecrawlError
from app.clients.gemini_client import GeminiClient, GeminiError
from app.models.job import Job
from app.models.document import Document
from app.models.cluster import Cluster
from app.models.summary import Summary
from app.config import settings

logger = logging.getLogger(__name__)


class CrawlerService:
    """Service for crawling URLs and analyzing content."""

    def __init__(self, db: Session):
        """Initialize crawler service.

        Args:
            db: Database session
        """
        self.db = db
        self.firecrawl = None
        self.gemini = None

    def _init_clients(self):
        """Initialize API clients lazily."""
        if not self.firecrawl:
            self.firecrawl = FirecrawlClient()
        if not self.gemini:
            self.gemini = GeminiClient()

    def close(self):
        """Close API clients."""
        if self.firecrawl:
            self.firecrawl.close()

    def crawl_and_analyze(self, job_id: int, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Crawl a URL and analyze the content.

        Args:
            job_id: Database job ID
            url: URL to crawl
            options: Crawl options (maxDepth, limit, etc.)

        Returns:
            Dict with crawl results summary

        Raises:
            FirecrawlError: On crawl failures
            GeminiError: On analysis failures
        """
        self._init_clients()

        # Get job from database
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        try:
            # Update job status
            job.status = "running"
            job.started_at = datetime.utcnow()
            job.progress = 10
            self.db.commit()

            logger.info(f"Starting crawl for job {job_id}: {url}")

            # Prepare crawl options
            crawl_options = {
                "maxDepth": options.get("maxDepth", settings.max_crawl_depth) if options else settings.max_crawl_depth,
                "limit": options.get("limit", 50) if options else 50,
            }

            # Submit crawl job
            firecrawl_job_id = self.firecrawl.submit_crawl(url, crawl_options)

            job.progress = 30
            job.job_metadata = {"firecrawl_job_id": firecrawl_job_id}
            self.db.commit()

            # Wait for crawl to complete
            logger.info(f"Waiting for Firecrawl job {firecrawl_job_id}")
            job_data = self.firecrawl.wait_for_job(firecrawl_job_id, max_wait_seconds=600)

            job.progress = 50
            self.db.commit()

            # Extract documents
            documents = self.firecrawl.extract_documents(job_data)
            logger.info(f"Extracted {len(documents)} documents")

            # Store documents in database
            doc_ids = []
            for doc_data in documents:
                document = Document(
                    job_id=job_id,
                    url=doc_data["url"],
                    title=doc_data.get("title"),
                    content_markdown=doc_data.get("content_markdown"),
                    content_html=doc_data.get("content_html"),
                    crawled_at=doc_data.get("crawled_at", datetime.utcnow())
                )
                self.db.add(document)
                self.db.flush()
                doc_ids.append(document.id)

            self.db.commit()
            job.progress = 70
            self.db.commit()

            # Analyze documents if we have content
            document_texts = [doc.get("content_markdown", "") for doc in documents if doc.get("content_markdown")]

            if document_texts:
                logger.info(f"Analyzing {len(document_texts)} documents")

                # Generate summary
                summary_text = self.gemini.summarize_documents(document_texts)

                # Extract topics
                topics = self.gemini.extract_topics(document_texts, num_topics=5)

                job.progress = 85
                self.db.commit()

                # Create clusters from topics
                cluster_ids = []
                for topic in topics:
                    cluster = Cluster(
                        job_id=job_id,
                        name=topic.get("name", "Unknown Topic"),
                        description=topic.get("description", ""),
                        document_count=int(len(documents) * topic.get("prevalence", 0) / 100),
                        keywords=topic.get("keywords", []),
                        novelty_score=0.5  # Will be scored later
                    )
                    self.db.add(cluster)
                    self.db.flush()
                    cluster_ids.append(cluster.id)

                # Create overall summary
                summary = Summary(
                    job_id=job_id,
                    summary_type="overall",
                    title=f"Analysis of {url}",
                    content=summary_text,
                    confidence_score=0.8
                )
                self.db.add(summary)
                self.db.commit()

                job.progress = 100
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                self.db.commit()

                logger.info(f"Job {job_id} completed successfully")

                return {
                    "documents_count": len(documents),
                    "clusters_count": len(cluster_ids),
                    "summary": summary_text[:200] + "..." if len(summary_text) > 200 else summary_text
                }
            else:
                job.progress = 100
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                self.db.commit()

                logger.warning(f"No content extracted from documents for job {job_id}")

                return {
                    "documents_count": len(documents),
                    "clusters_count": 0,
                    "summary": "No content available for analysis"
                }

        except (FirecrawlError, GeminiError) as e:
            logger.error(f"Job {job_id} failed: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self.db.commit()
            raise

        except Exception as e:
            logger.error(f"Unexpected error in job {job_id}: {e}", exc_info=True)
            job.status = "failed"
            job.error_message = f"Unexpected error: {str(e)}"
            job.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def analyze_sentiment(self, document_id: int) -> Dict[str, Any]:
        """Analyze sentiment of a document.

        Args:
            document_id: Document ID

        Returns:
            Sentiment analysis results

        Raises:
            ValueError: If document not found
            GeminiError: On analysis failures
        """
        self._init_clients()

        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")

        if not document.content_markdown:
            raise ValueError(f"Document {document_id} has no content")

        sentiment_data = self.gemini.extract_sentiment(document.content_markdown)

        # Update document with sentiment score
        document.sentiment_score = sentiment_data.get("score", 0.0)
        self.db.commit()

        return sentiment_data

    def score_cluster_novelty(self, cluster_id: int, baseline_topics: List[str] = None) -> float:
        """Score how novel/emerging a cluster is.

        Args:
            cluster_id: Cluster ID
            baseline_topics: List of established topics for comparison

        Returns:
            Novelty score (0.0 - 1.0)

        Raises:
            ValueError: If cluster not found
            GeminiError: On scoring failures
        """
        self._init_clients()

        cluster = self.db.query(Cluster).filter(Cluster.id == cluster_id).first()
        if not cluster:
            raise ValueError(f"Cluster {cluster_id} not found")

        # Create description from cluster data
        description = f"{cluster.name}: {cluster.description}"

        novelty_score = self.gemini.score_novelty(description, baseline_topics or [])

        # Update cluster with novelty score
        cluster.novelty_score = novelty_score
        self.db.commit()

        return novelty_score
