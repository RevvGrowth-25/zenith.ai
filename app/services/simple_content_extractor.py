import requests
from bs4 import BeautifulSoup
import re

class SimpleContentExtractor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def extract_content(self, url, max_length=2000):
        """Extract main content from a URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe']):
                element.decompose()
            
            # Try to find main content
            content_selectors = [
                'main', 'article', '.content', '.main-content', 
                '.post-content', '.entry-content', '#content',
                '.article-body', '.story-body', '.text-content'
            ]
            
            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content and len(main_content.get_text(strip=True)) > 100:
                    break
            
            if not main_content:
                # Fallback to paragraphs
                paragraphs = soup.find_all('p')
                if paragraphs:
                    main_content = soup.new_tag('div')
                    for p in paragraphs[:10]:  # Take first 10 paragraphs
                        main_content.append(p)
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                # Clean text
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'[^\w\s.,!?;:\-\'"()]', ' ', text)
                text = ' '.join(text.split())
                
                return text[:max_length] if len(text) > max_length else text
            
            return None
            
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None