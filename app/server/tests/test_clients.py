"""Tests for external API clients."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx
import json

from app.clients.firecrawl_client import FirecrawlClient, FirecrawlError, FirecrawlRateLimitError
from app.clients.gemini_client import GeminiClient, GeminiError


class TestFirecrawlClient:
    """Tests for Firecrawl client."""

    def test_init(self):
        """Test client initialization."""
        client = FirecrawlClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.firecrawl.dev"
        client.close()

    @patch('httpx.Client.post')
    def test_fetch_success(self, mock_post):
        """Test successful fetch operation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "markdown": "# Test Content",
            "metadata": {"title": "Test Page"}
        }
        mock_post.return_value = mock_response

        client = FirecrawlClient(api_key="test-key")
        result = client.fetch("https://example.com")

        assert "markdown" in result
        assert result["markdown"] == "# Test Content"
        client.close()

    @patch('httpx.Client.post')
    def test_fetch_rate_limit(self, mock_post):
        """Test rate limit handling with retry logic."""
        from tenacity import RetryError

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        client = FirecrawlClient(api_key="test-key")

        # The retry decorator will retry 5 times, then raise RetryError
        with pytest.raises(RetryError):
            client.fetch("https://example.com")

        client.close()

    @patch('httpx.Client.post')
    def test_submit_crawl(self, mock_post):
        """Test crawl job submission."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "test-job-123"}
        mock_post.return_value = mock_response

        client = FirecrawlClient(api_key="test-key")
        job_id = client.submit_crawl("https://example.com", {"maxDepth": 2})

        assert job_id == "test-job-123"
        client.close()

    @patch('httpx.Client.get')
    def test_get_job(self, mock_get):
        """Test job status retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "test-job-123",
            "status": "completed",
            "data": []
        }
        mock_get.return_value = mock_response

        client = FirecrawlClient(api_key="test-key")
        job_data = client.get_job("test-job-123")

        assert job_data["status"] == "completed"
        client.close()

    def test_extract_documents(self):
        """Test document extraction from job data."""
        client = FirecrawlClient(api_key="test-key")

        job_data = {
            "status": "completed",
            "data": [
                {
                    "url": "https://example.com/page1",
                    "markdown": "# Page 1",
                    "metadata": {"title": "Page 1"}
                },
                {
                    "url": "https://example.com/page2",
                    "markdown": "# Page 2",
                    "metadata": {"title": "Page 2"}
                }
            ]
        }

        documents = client.extract_documents(job_data)

        assert len(documents) == 2
        assert documents[0]["url"] == "https://example.com/page1"
        assert documents[0]["title"] == "Page 1"
        assert documents[1]["content_markdown"] == "# Page 2"

        client.close()


class TestGeminiClient:
    """Tests for Gemini client."""

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_init(self, mock_model_class, mock_configure):
        """Test client initialization."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        client = GeminiClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.model_name == "gemini-1.5-flash"
        mock_configure.assert_called_once_with(api_key="test-key")

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_generate_text(self, mock_model_class, mock_configure):
        """Test text generation."""
        mock_response = Mock()
        mock_response.text = "Generated text response"

        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        client = GeminiClient(api_key="test-key")
        result = client.generate_text("Test prompt")

        assert result == "Generated text response"
        mock_model.generate_content.assert_called_once()

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_summarize_documents(self, mock_model_class, mock_configure):
        """Test document summarization."""
        mock_response = Mock()
        mock_response.text = "This is a summary of the documents."

        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        client = GeminiClient(api_key="test-key")
        result = client.summarize_documents(["Doc 1 content", "Doc 2 content"])

        assert "summary" in result.lower()
        assert len(result) > 0

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_extract_sentiment(self, mock_model_class, mock_configure):
        """Test sentiment extraction."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "sentiment": "positive",
            "score": 0.8,
            "key_points": ["Point 1", "Point 2"],
            "stance": "Supportive"
        })

        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        client = GeminiClient(api_key="test-key")
        result = client.extract_sentiment("This is great news!")

        assert result["sentiment"] == "positive"
        assert result["score"] == 0.8
        assert len(result["key_points"]) == 2

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_extract_topics(self, mock_model_class, mock_configure):
        """Test topic extraction."""
        mock_response = Mock()
        mock_response.text = json.dumps([
            {
                "name": "AI Development",
                "keywords": ["AI", "ML", "models"],
                "description": "Discussion about AI",
                "prevalence": 60
            },
            {
                "name": "Data Privacy",
                "keywords": ["privacy", "security", "data"],
                "description": "Privacy concerns",
                "prevalence": 40
            }
        ])

        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        client = GeminiClient(api_key="test-key")
        result = client.extract_topics(["Doc content"], num_topics=2)

        assert len(result) == 2
        assert result[0]["name"] == "AI Development"
        assert result[1]["prevalence"] == 40

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_score_novelty(self, mock_model_class, mock_configure):
        """Test novelty scoring."""
        mock_response = Mock()
        mock_response.text = "0.75"

        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        client = GeminiClient(api_key="test-key")
        score = client.score_novelty("New AI model released", ["Old AI news"])

        assert 0.0 <= score <= 1.0
        assert score == 0.75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
