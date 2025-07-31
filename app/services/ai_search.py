import openai
import anthropic
import requests
from typing import Dict, List, Optional
from datetime import datetime
import json
import time
import re
from flask import current_app


class AISearchService:
    def __init__(self, openai_key: str = None, anthropic_key: str = None):
        self.openai_key = openai_key or current_app.config.get('OPENAI_API_KEY')
        self.anthropic_key = anthropic_key or current_app.config.get('ANTHROPIC_API_KEY')

        # Initialize OpenAI client (new v1.0+ format)
        if self.openai_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_key)
        else:
            self.openai_client = None

        # Initialize Anthropic client correctly
        if self.anthropic_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
            except Exception as e:
                print(f"Error initializing Anthropic client: {e}")
                self.anthropic_client = None
        else:
            self.anthropic_client = None

    def search_chatgpt(self, query: str, brand_name: str = None) -> Dict:
        """Search using OpenAI GPT API (v1.0+ format)"""
        if not self.openai_key or not self.openai_client:
            return self._mock_response('chatgpt', query, 'OpenAI API key not configured', brand_name)

        try:
            # Create a search-like prompt
            search_prompt = f"""
            Please provide a comprehensive answer to this query: "{query}"

            Include relevant companies, brands, and sources in your response. 
            Be factual and cite specific examples where appropriate.
            """

            # Use new v1.0+ API format
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": "You are a helpful AI assistant that provides comprehensive, factual responses with specific company and brand mentions when relevant."},
                    {"role": "user", "content": search_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            content = response.choices[0].message.content

            # Analyze brand mentions if brand_name provided
            analysis = {}
            if brand_name:
                analysis = self.analyze_brand_mentions(content, brand_name)

            return {
                'platform': 'chatgpt',
                'query': query,
                'response': content,
                'brand_analysis': analysis,
                'timestamp': datetime.utcnow().isoformat(),
                'success': True,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
            }

        except Exception as e:
            print(f"ChatGPT API Error: {e}")
            return {
                'platform': 'chatgpt',
                'query': query,
                'error': str(e),
                'success': False,
                'timestamp': datetime.utcnow().isoformat()
            }

    def search_claude(self, query: str, brand_name: str = None) -> Dict:
        """Search using Claude API"""
        if not self.anthropic_key or not self.anthropic_client:
            return self._mock_response('claude', query,
                                       'Anthropic API key not configured or client initialization failed', brand_name)

        try:
            search_prompt = f"""
            Please provide a detailed response to this query: "{query}"

            Include relevant companies, products, and sources in your answer.
            Be comprehensive and mention specific brands or services when appropriate.
            """

            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": search_prompt}
                ]
            )

            content = message.content[0].text

            # Analyze brand mentions if brand_name provided
            analysis = {}
            if brand_name:
                analysis = self.analyze_brand_mentions(content, brand_name)

            return {
                'platform': 'claude',
                'query': query,
                'response': content,
                'brand_analysis': analysis,
                'timestamp': datetime.utcnow().isoformat(),
                'success': True,
                'tokens_used': getattr(message.usage, 'input_tokens', 0) + getattr(message.usage, 'output_tokens',
                                                                                   0) if hasattr(message,
                                                                                                 'usage') else 0
            }

        except Exception as e:
            print(f"Claude API Error: {e}")
            return {
                'platform': 'claude',
                'query': query,
                'error': str(e),
                'success': False,
                'timestamp': datetime.utcnow().isoformat()
            }

    def search_perplexity(self, query: str, brand_name: str = None) -> Dict:
        """Search using Perplexity API (mock for now - replace with real API when available)"""
        return self._mock_response('perplexity', query, brand_name=brand_name)

    def search_all_platforms(self, query: str, brand_name: str = None) -> List[Dict]:
        """Search across all available AI platforms"""
        results = []

        # Search ChatGPT
        print(f"Searching ChatGPT for: {query}")
        chatgpt_result = self.search_chatgpt(query, brand_name)
        results.append(chatgpt_result)

        # Add delay between API calls
        time.sleep(1)

        # Search Claude
        print(f"Searching Claude for: {query}")
        claude_result = self.search_claude(query, brand_name)
        results.append(claude_result)

        # Search Perplexity (mock)
        perplexity_result = self.search_perplexity(query, brand_name)
        results.append(perplexity_result)

        return results

    def analyze_brand_mentions(self, response_text: str, brand_name: str) -> Dict:
        """Analyze brand mentions in AI response"""
        if not response_text or not brand_name:
            return {
                'direct_mentions': 0,
                'mention_type': 'none',
                'sentiment_score': 0.0,
                'position_score': 0,
                'contexts': [],
                'visibility_score': 0.0
            }

        response_lower = response_text.lower()
        brand_lower = brand_name.lower()

        # Count direct mentions
        direct_mentions = response_lower.count(brand_lower)

        # Find mention contexts
        contexts = self._extract_mention_contexts(response_text, brand_name)

        # Analyze sentiment around mentions
        sentiment_score = self._analyze_sentiment(response_text, brand_name)

        # Determine mention type
        mention_type = 'none'
        if direct_mentions > 0:
            mention_type = 'direct'
        elif any(
                word in response_lower for word in [brand_lower.split()[0] if ' ' in brand_lower else brand_lower[:5]]):
            mention_type = 'indirect'

        # Calculate position score (higher if mentioned earlier)
        position_score = 0
        if contexts:
            first_mention_pos = response_text.lower().find(brand_lower)
            if first_mention_pos >= 0:
                position_score = max(10, 100 - (first_mention_pos / len(response_text)) * 90)

        return {
            'direct_mentions': direct_mentions,
            'mention_type': mention_type,
            'sentiment_score': sentiment_score,
            'position_score': position_score,
            'contexts': contexts[:3],  # Limit to 3 contexts
            'visibility_score': self._calculate_visibility_score(direct_mentions, mention_type, sentiment_score,
                                                                 position_score)
        }

    def _calculate_visibility_score(self, mentions: int, mention_type: str, sentiment: float, position: float) -> float:
        """Calculate visibility score based on various factors"""
        if mentions == 0 and mention_type == 'none':
            return 0.0

        base_score = 0
        if mention_type == 'direct':
            base_score = min(mentions * 20, 60)  # Max 60 points for mentions
        elif mention_type == 'indirect':
            base_score = 20

        # Add sentiment bonus/penalty
        sentiment_modifier = sentiment * 15  # -15 to +15 points

        # Add position bonus
        position_modifier = (position / 100) * 25  # 0 to 25 points

        total_score = max(0, min(100, base_score + sentiment_modifier + position_modifier))
        return round(total_score, 1)

    def _analyze_sentiment(self, text: str, brand_name: str) -> float:
        """Simple sentiment analysis around brand mentions"""
        if not text or not brand_name:
            return 0.0

        # Get contexts around brand mentions
        contexts = self._extract_mention_contexts(text, brand_name, context_length=200)

        if not contexts:
            return 0.0

        positive_words = [
            'excellent', 'best', 'great', 'outstanding', 'recommended', 'top', 'leading',
            'innovative', 'reliable', 'trusted', 'popular', 'successful', 'effective',
            'quality', 'superior', 'amazing', 'fantastic', 'impressive', 'strong',
            'premier', 'prestigious', 'renowned', 'established', 'accredited'
        ]

        negative_words = [
            'poor', 'bad', 'worst', 'terrible', 'avoid', 'problematic', 'failed',
            'disappointing', 'unreliable', 'weak', 'inferior', 'lacking', 'struggling'
        ]

        total_sentiment = 0
        for context in contexts:
            context_lower = context.lower()
            positive_count = sum(1 for word in positive_words if word in context_lower)
            negative_count = sum(1 for word in negative_words if word in context_lower)

            total_sentiment += (positive_count - negative_count)

        # Normalize to -1 to 1 scale
        if len(contexts) > 0:
            normalized_sentiment = total_sentiment / (len(contexts) * 5)  # Divide by max possible sentiment per context
            return max(-1, min(1, normalized_sentiment))

        return 0.0

    def _extract_mention_contexts(self, text: str, brand_name: str, context_length: int = 150) -> List[str]:
        """Extract context around brand mentions"""
        if not text or not brand_name:
            return []

        contexts = []
        text_lower = text.lower()
        brand_lower = brand_name.lower()

        start = 0
        while True:
            pos = text_lower.find(brand_lower, start)
            if pos == -1:
                break

            # Extract context around the mention
            context_start = max(0, pos - context_length // 2)
            context_end = min(len(text), pos + len(brand_name) + context_length // 2)
            context = text[context_start:context_end].strip()

            # Clean up context
            if context and context not in contexts:
                contexts.append(context)

            start = pos + len(brand_name)

        return contexts

    def _mock_response(self, platform: str, query: str, error: str = None, brand_name: str = None) -> Dict:
        """Generate mock response when API is not available"""
        if error:
            print(f"{platform} Error: {error}")
            # Generate a mock response even when there's an error, so testing can continue
            if brand_name:
                mock_content = f"Based on the query '{query}', {brand_name} is mentioned as one of the institutions in this space. {brand_name} offers various programs and services to students, focusing on quality education and innovation. The institution is known for its commitment to academic excellence and student development."
            else:
                mock_content = f"This is a simulated response for '{query}'. Various institutions and organizations are working in this field to provide quality services and solutions."

            analysis = {}
            if brand_name:
                analysis = self.analyze_brand_mentions(mock_content, brand_name)

            return {
                'platform': platform,
                'query': query,
                'response': mock_content,
                'brand_analysis': analysis,
                'timestamp': datetime.utcnow().isoformat(),
                'success': True,  # Mark as success for mock data
                'tokens_used': 0,
                'note': f'Mock response due to: {error}'
            }

        # Generate realistic mock response that might mention the brand
        if brand_name:
            mock_content = f"Here's information about {query}. {brand_name} is one of the solutions in this space, along with other companies offering similar services. The market includes various platforms and tools designed to address these specific needs."
        else:
            mock_content = f"Based on current information about '{query}', here are some key insights. There are several companies and solutions in this space, including various platforms and services that offer different approaches to address these needs."

        analysis = {}
        if brand_name:
            analysis = self.analyze_brand_mentions(mock_content, brand_name)

        return {
            'platform': platform,
            'query': query,
            'response': mock_content,
            'brand_analysis': analysis,
            'timestamp': datetime.utcnow().isoformat(),
            'success': True,
            'tokens_used': 0
        }