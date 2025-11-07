"""Firecrawl API client with retry logic and error handling.

Based on Firecrawl v2 API: https://docs.firecrawl.dev/api-reference/v2-introduction
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from app.config import settings

logger = logging.getLogger(__name__)


class FirecrawlError(Exception):
    """Base exception for Firecrawl client errors."""
    pass


class FirecrawlRateLimitError(FirecrawlError):
    """Raised when rate limit is hit (429)."""
    pass


class FirecrawlClient:
    """Client for Firecrawl API with retry logic and error handling."""

    def __init__(self, api_key: str = None, base_url: str = "https://api.firecrawl.dev"):
        """Initialize Firecrawl client.

        Args:
            api_key: Firecrawl API key (defaults to settings)
            base_url: Base URL for Firecrawl API
        """
        self.api_key = api_key or settings.firecrawl_api_key
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close HTTP client."""
        self.client.close()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate errors.

        Args:
            response: HTTP response from Firecrawl API

        Returns:
            Parsed JSON response

        Raises:
            FirecrawlRateLimitError: On 429 status
            FirecrawlError: On other error statuses
        """
        if response.status_code == 429:
            logger.warning("Firecrawl rate limit hit (429)")
            raise FirecrawlRateLimitError("Rate limit exceeded")

        if response.status_code >= 400:
            error_msg = f"Firecrawl API error {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise FirecrawlError(error_msg)

        try:
            return response.json()
        except Exception as e:
            logger.error(f"Failed to parse Firecrawl response: {e}")
            raise FirecrawlError(f"Invalid JSON response: {e}")

    @retry(
        retry=retry_if_exception_type(FirecrawlRateLimitError),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def fetch(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fetch a single page and extract content.

        Args:
            url: URL to fetch
            options: Optional scraping options (formats, includeTags, etc.)

        Returns:
            Dict with extracted content (markdown, metadata, etc.)

        Raises:
            FirecrawlError: On API errors
        """
        payload = {
            "url": url,
            "formats": options.get("formats", ["markdown"]) if options else ["markdown"]
        }

        if options:
            # Add optional parameters
            if "includeTags" in options:
                payload["includeTags"] = options["includeTags"]
            if "excludeTags" in options:
                payload["excludeTags"] = options["excludeTags"]
            if "onlyMainContent" in options:
                payload["onlyMainContent"] = options["onlyMainContent"]

        logger.info(f"Fetching URL: {url}")
        response = self.client.post(f"{self.base_url}/v1/scrape", json=payload)
        data = self._handle_response(response)

        logger.info(f"Successfully fetched {url}")
        return data

    @retry(
        retry=retry_if_exception_type(FirecrawlRateLimitError),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def submit_crawl(
        self,
        url: str,
        options: Dict[str, Any] = None
    ) -> str:
        """Submit a crawl job to Firecrawl.

        Args:
            url: Starting URL for the crawl
            options: Crawl options (limit, maxDepth, etc.)

        Returns:
            Job ID for the crawl

        Raises:
            FirecrawlError: On API errors
        """
        payload = {"url": url}

        if options:
            if "limit" in options:
                payload["limit"] = options["limit"]
            if "maxDepth" in options:
                payload["maxDepth"] = options["maxDepth"]
            if "allowBackwardLinks" in options:
                payload["allowBackwardLinks"] = options["allowBackwardLinks"]
            if "allowExternalLinks" in options:
                payload["allowExternalLinks"] = options["allowExternalLinks"]

        logger.info(f"Submitting crawl for URL: {url}")
        response = self.client.post(f"{self.base_url}/v1/crawl", json=payload)
        data = self._handle_response(response)

        job_id = data.get("id")
        if not job_id:
            raise FirecrawlError("No job ID returned from crawl submission")

        logger.info(f"Crawl submitted successfully. Job ID: {job_id}")
        return job_id

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get the status and results of a crawl job.

        Args:
            job_id: Firecrawl job ID

        Returns:
            Dict with job status and results

        Raises:
            FirecrawlError: On API errors
        """
        logger.info(f"Checking job status: {job_id}")
        response = self.client.get(f"{self.base_url}/v1/crawl/{job_id}")
        data = self._handle_response(response)

        status = data.get("status", "unknown")
        logger.info(f"Job {job_id} status: {status}")

        return data

    def wait_for_job(
        self,
        job_id: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """Wait for a crawl job to complete.

        Args:
            job_id: Firecrawl job ID
            max_wait_seconds: Maximum time to wait in seconds
            poll_interval: Seconds between status checks

        Returns:
            Final job data with results

        Raises:
            FirecrawlError: If job fails or times out
        """
        import time

        start_time = time.time()
        logger.info(f"Waiting for job {job_id} to complete...")

        while time.time() - start_time < max_wait_seconds:
            job_data = self.get_job(job_id)
            status = job_data.get("status", "unknown")

            if status == "completed":
                logger.info(f"Job {job_id} completed successfully")
                return job_data
            elif status == "failed":
                error = job_data.get("error", "Unknown error")
                raise FirecrawlError(f"Job {job_id} failed: {error}")
            elif status in ["scraping", "pending"]:
                time.sleep(poll_interval)
            else:
                logger.warning(f"Unknown job status: {status}")
                time.sleep(poll_interval)

        raise FirecrawlError(f"Job {job_id} timed out after {max_wait_seconds}s")

    def extract_documents(self, job_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract documents from Firecrawl job results.

        Args:
            job_data: Job data from get_job()

        Returns:
            List of document dictionaries with normalized fields
        """
        documents = []
        data_list = job_data.get("data", [])

        for item in data_list:
            doc = {
                "url": item.get("url", ""),
                "title": item.get("metadata", {}).get("title", ""),
                "content_markdown": item.get("markdown", ""),
                "content_html": item.get("html", ""),
                "crawled_at": datetime.utcnow(),
                "metadata": item.get("metadata", {})
            }
            documents.append(doc)

        logger.info(f"Extracted {len(documents)} documents from job results")
        return documents
