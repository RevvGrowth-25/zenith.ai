import time
import hashlib
import openai
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
from serpapi import GoogleSearch
from app.models import db
from app.models.ai_overview import AIOverview, SearchCache
from app.utils.helpers import clean_text
import logging

class AIOverviewService:
    def __init__(self, openai_api_key, serpapi_key):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.serpapi_key = serpapi_key
        self.logger = logging.getLogger(__name__)

    def generate_overview(self, query, user_id):
        """Main method to generate AI overview for a query"""
        start_time = time.time()

        try:
            # Step 1: Check cache first
            cached_result = self._check_cache(query)
            if cached_result:
                return self._create_overview_record(query, user_id, cached_result, time.time() - start_time)

            # Step 2: Search Google using SerpAPI
            search_results = self._search_google(query)
            if not search_results:
                raise Exception("No search results found")

            # Step 3: Extract content from top URLs
            page_contents = self._extract_page_contents(search_results[:8])  # Top 8 results

            # Step 4: Generate AI summary
            overview_text = self._generate_summary(query, page_contents)

            # Step 5: Prepare sources
            sources_used = self._prepare_sources(search_results[:5], page_contents)

            # Step 6: Cache the results
            result_data = {
                'overview_text': overview_text,
                'sources_used': sources_used,
                'search_results': search_results[:10]
            }
            self._cache_results(query, result_data)

            # Step 7: Save to database
            processing_time = time.time() - start_time
            return self._create_overview_record(query, user_id, result_data, processing_time)

        except Exception as e:
            self.logger.error(f"Error generating AI overview: {str(e)}")
            raise

    def _check_cache(self, query):
        """Check if query results are cached and still valid"""
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        cached = SearchCache.query.filter_by(query_hash=query_hash).first()

        if cached and cached.expires_at > datetime.utcnow():
            return cached.results
        elif cached:
            db.session.delete(cached)
            db.session.commit()

        return None

    def _search_google(self, query):
        """Search Google using SerpAPI"""
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": self.serpapi_key,
                "num": 10,
                "hl": "en",
                "gl": "us"
            })

            results = search.get_dict()
            organic_results = results.get("organic_results", [])

            search_results = []
            for result in organic_results:
                search_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'position': result.get('position', 0)
                })

            return search_results

        except Exception as e:
            self.logger.error(f"Error searching Google: {str(e)}")
            return []

    def _extract_page_contents(self, search_results):
        """Extract main content from web pages using BeautifulSoup"""
        page_contents = []

        for result in search_results:
            try:
                content = self._extract_single_page_content(result['url'])
                if content:
                    page_contents.append({
                        'url': result['url'],
                        'title': result['title'],
                        'content': content,
                        'snippet': result['snippet']
                    })
            except Exception as e:
                self.logger.warning(f"Failed to extract content from {result['url']}: {str(e)}")
                continue

        return page_contents

    def _extract_single_page_content(self, url):
        """Extract content from a single web page using BeautifulSoup"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
                element.decompose()

            # Try to find main content areas
            main_content = None

            # Look for main content selectors
            content_selectors = [
                'main', 'article', '.content', '.main-content',
                '.post-content', '.entry-content', '#content',
                '.article-body', '.story-body'
            ]

            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            # If no main content found, use body
            if not main_content:
                main_content = soup.find('body')

            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                # Clean and limit text
                text = clean_text(text)
                return text[:2000] if len(text) > 2000 else text

            return None

        except Exception as e:
            self.logger.warning(f"Content extraction failed for {url}: {str(e)}")
            return None

    def _generate_summary(self, query, page_contents):
        """Generate AI summary using OpenAI"""
        if not page_contents:
            return "Sorry, I couldn't find enough reliable information to provide a comprehensive overview."

        # Combine all content
        combined_content = "\n\n".join([
            f"Source: {content['title']}\n{content['content']}"
            for content in page_contents[:5]  # Use top 5 sources
        ])

        prompt = f"""Based on the following web search results, provide a comprehensive and accurate answer to the question: "{query}"

Web Results:
{combined_content}

Instructions:
1. Provide a clear, informative overview in 2-3 paragraphs
2. Focus on the most important and relevant information
3. Be factual and avoid speculation
4. If there are different perspectives, mention them
5. Keep the response concise but comprehensive
6. Don't mention "according to the sources" - write as if you know the information

Answer:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that provides accurate, comprehensive overviews based on web search results. Write in a natural, informative tone."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return "I encountered an error while generating the overview. Please try again."

    def _prepare_sources(self, search_results, page_contents):
        """Prepare sources list for display"""
        sources = []
        content_urls = {content['url'] for content in page_contents}

        for result in search_results:
            sources.append({
                'title': result['title'],
                'url': result['url'],
                'snippet': result['snippet'],
                'content_extracted': result['url'] in content_urls
            })

        return sources

    def _cache_results(self, query, result_data):
        """Cache search results"""
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(hours=6)  # Cache for 6 hours

        cache_entry = SearchCache(
            query_hash=query_hash,
            search_query=query,  # Updated to use search_query
            results=result_data,
            expires_at=expires_at
        )

        db.session.add(cache_entry)
        db.session.commit()

    def _create_overview_record(self, query, user_id, result_data, processing_time):
        """Create and save AI overview record"""
        overview = AIOverview(
            user_id=user_id,
            search_query=query,  # Updated to use search_query
            overview_text=result_data['overview_text'],
            sources_used=result_data['sources_used'],
            search_results=result_data['search_results'],
            processing_time=processing_time
        )

        db.session.add(overview)
        db.session.commit()

        return overview.to_dict()

    def get_user_overviews(self, user_id, limit=20):
        """Get user's recent AI overviews"""
        overviews = AIOverview.query.filter_by(user_id=user_id)\
            .order_by(AIOverview.created_at.desc())\
            .limit(limit).all()

        return [overview.to_dict() for overview in overviews]