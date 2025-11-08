"""Gemini API client for LLM operations.

Based on Google Generative AI SDK: https://ai.google.dev/gemini-api/docs
"""

import logging
from typing import Dict, Any, List, Optional
import json

import google.generativeai as genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Base exception for Gemini client errors."""
    pass


class GeminiClient:
    """Client for Google Gemini API with structured output support."""

    def __init__(self, api_key: str = None, model_name: str = "gemini-1.5-flash"):
        """Initialize Gemini client.

        Args:
            api_key: Gemini API key (defaults to settings)
            model_name: Model to use (gemini-1.5-pro, gemini-1.5-flash, etc.)
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

        logger.info(f"Initialized Gemini client with model: {model_name}")

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=2, min=1, max=30),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Generate text completion from Gemini.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text

        Raises:
            GeminiError: On API errors
        """
        try:
            logger.info(f"Generating text (temperature={temperature}, max_tokens={max_tokens})")

            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            if not response.text:
                raise GeminiError("No text generated in response")

            logger.info("Text generation successful")
            return response.text

        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise GeminiError(f"Failed to generate text: {e}")

    def summarize_documents(
        self,
        documents: List[str],
        max_length: int = 500
    ) -> str:
        """Summarize a list of documents.

        Args:
            documents: List of document texts
            max_length: Maximum summary length in words

        Returns:
            Summary text

        Raises:
            GeminiError: On API errors
        """
        if not documents:
            return ""

        # Combine documents with separators
        combined = "\n\n---\n\n".join(documents[:10])  # Limit to 10 docs

        prompt = f"""Summarize the following documents into a concise overview of maximum {max_length} words.
Focus on the main themes, key points, and overall sentiment.

Documents:
{combined}

Summary:"""

        return self.generate_text(prompt, temperature=0.3, max_tokens=max_length * 2)

    def extract_sentiment(self, text: str) -> Dict[str, Any]:
        """Extract sentiment and stance from text.

        Args:
            text: Input text

        Returns:
            Dict with sentiment, score, and key points

        Raises:
            GeminiError: On API errors
        """
        prompt = f"""Analyze the sentiment and stance of the following text.
Provide your analysis in JSON format with these fields:
- sentiment: one of "positive", "negative", "neutral", "mixed"
- score: float from -1.0 (very negative) to 1.0 (very positive)
- key_points: list of up to 5 key points or themes
- stance: brief description of the author's position

Text:
{text[:2000]}

Return only valid JSON, no other text."""

        try:
            response_text = self.generate_text(prompt, temperature=0.2)

            # Try to extract JSON from response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse sentiment JSON: {e}")
            # Return default structure
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "key_points": [],
                "stance": "Unable to determine"
            }

    def extract_topics(
        self,
        documents: List[str],
        num_topics: int = 5
    ) -> List[Dict[str, Any]]:
        """Extract main topics from documents.

        Args:
            documents: List of document texts
            num_topics: Number of topics to extract

        Returns:
            List of topic dicts with name, keywords, and description

        Raises:
            GeminiError: On API errors
        """
        if not documents:
            return []

        # Sample and combine documents
        sample = documents[:20]
        combined = "\n\n".join([doc[:500] for doc in sample])

        prompt = f"""Analyze the following documents and extract the top {num_topics} discussion topics.
For each topic, provide:
- name: short topic name (3-5 words)
- keywords: list of 3-5 relevant keywords
- description: one-sentence description
- prevalence: estimated percentage of documents discussing this (0-100)

Documents:
{combined}

Return your answer as a JSON array of topic objects."""

        try:
            response_text = self.generate_text(prompt, temperature=0.3, max_tokens=1500)

            # Extract JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            topics = json.loads(response_text)
            return topics if isinstance(topics, list) else []

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse topics JSON: {e}")
            return []

    def score_novelty(
        self,
        cluster_description: str,
        baseline_topics: List[str]
    ) -> float:
        """Score how novel/emerging a cluster is compared to baseline topics.

        Args:
            cluster_description: Description of the cluster
            baseline_topics: List of known/established topics

        Returns:
            Novelty score from 0.0 (not novel) to 1.0 (very novel)

        Raises:
            GeminiError: On API errors
        """
        baseline_text = ", ".join(baseline_topics) if baseline_topics else "No baseline"

        prompt = f"""Rate how novel or emerging this topic is compared to established topics.
Return ONLY a number between 0.0 and 1.0, where:
- 0.0 = completely established/well-known topic
- 0.5 = moderately novel with some new angles
- 1.0 = highly novel/emerging topic

New Topic:
{cluster_description}

Established Topics:
{baseline_text}

Novelty Score (number only):"""

        try:
            response_text = self.generate_text(prompt, temperature=0.1, max_tokens=10)
            # Extract first number
            import re
            match = re.search(r'([0-1]\.\d+|[01])', response_text)
            if match:
                score = float(match.group(1))
                return max(0.0, min(1.0, score))  # Clamp to [0, 1]
            return 0.5  # Default if parsing fails

        except Exception as e:
            logger.warning(f"Failed to score novelty: {e}")
            return 0.5

    def generate_key_quotes(
        self,
        text: str,
        num_quotes: int = 3
    ) -> List[Dict[str, str]]:
        """Extract key quotes from text.

        Args:
            text: Source text
            num_quotes: Number of quotes to extract

        Returns:
            List of quote dicts with 'quote' and 'context'

        Raises:
            GeminiError: On API errors
        """
        prompt = f"""Extract {num_quotes} key quotes from the following text that best represent the main arguments or insights.
Return as JSON array with objects containing:
- quote: the exact quote
- context: why this quote is significant

Text:
{text[:3000]}

Return only valid JSON array."""

        try:
            response_text = self.generate_text(prompt, temperature=0.2, max_tokens=800)

            # Extract JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            quotes = json.loads(response_text)
            return quotes if isinstance(quotes, list) else []

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse quotes JSON: {e}")
            return []
