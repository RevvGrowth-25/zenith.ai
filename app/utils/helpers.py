import re
from bs4 import BeautifulSoup

def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = BeautifulSoup(text, 'html.parser').get_text()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:\-\'"()]', ' ', text)
    
    # Remove extra spaces
    text = ' '.join(text.split())
    
    return text.strip()

def extract_main_content(html_content):
    """Extract main content from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()
    
    # Find main content areas
    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
    
    if main_content:
        return main_content.get_text()
    
    return soup.get_text()