import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import re
import time
import sys

class Crawler:
    def __init__(self, base_url="https://developers.miniorange.com/"):
        self.base_url = base_url
        self.seen = set()
        self.docs_data = {}

    def get_module(self, url):
        """Extract module name from URL."""
        path = urlparse(url).path
        match = re.search(r"/docs/([^/]+)/", path)
        if match:
            return match.group(1)
        return "general"

    def crawl(self, url, depth=0, max_depth=15):
        if url in self.seen:
            return
        if depth > max_depth:
            return

        self.seen.add(url)
        
        # Only crawl developers.miniorange.com if base_url is set to it
        if "developers.miniorange.com" in self.base_url and "developers.miniorange.com" not in url:
             return

        print(f"Crawling: {url}")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Skipping {url}: Status {response.status_code}")
                return

            soup = BeautifulSoup(response.text, "html.parser")
            
            # If it's a doc page, add to dataset
            # Relaxed condition: if we are specifically asked to crawl a URL, we should probably include it even if not strictly /docs/ if it has content.
            # But adhering to original logic for finding docs:
            if "/docs/" in url or url == self.base_url: 
                self._process_page(url, soup)

            # Find links
            for link in soup.find_all("a", href=True):
                href = link["href"]
                next_url = urljoin(url, href)
                
                # Remove fragments
                parsed = urlparse(next_url)
                if parsed.fragment:
                    next_url = next_url.split("#")[0]

                # Normalize
                if next_url.endswith("/"):
                    next_url = next_url[:-1]

                # Filter relevant links to crawl
                if next_url.startswith(self.base_url) and next_url not in self.seen:
                     # simplistic filter to avoid endless loops or irrelevant paths
                    if not any(ext in next_url.lower() for ext in [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".css", ".js", "wp-content", "wp-includes"]):
                         self.crawl(next_url, depth=depth+1, max_depth=max_depth)
                         
            # Be nice to the server
            time.sleep(0.1)

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    def _process_page(self, url, soup):
        title = soup.title.string.strip() if soup.title else url
        module = self.get_module(url)
        
        # Extract content as Markdown-ish text to preserve code blocks
        content_md = ""
        
        # Try to find the main content area first
        main_content = soup.find('main') or soup.find('article') or soup.find(class_='content') or soup.body
        
        if main_content:
            # Remove script and style elements
            for script in main_content(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Process elements
            for element in main_content.descendants:
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    content_md += f"\n\n# {element.get_text().strip()}\n\n"
                elif element.name == 'p':
                    content_md += f"\n{element.get_text().strip()}\n"
                elif element.name == 'li':
                    content_md += f"- {element.get_text().strip()}\n"
                elif element.name == 'pre':
                    code_content = element.get_text().strip()
                    content_md += f"\n```\n{code_content}\n```\n"
                elif element.name == 'code' and element.parent.name != 'pre':
                        # Inline code
                        content_md += f"`{element.get_text().strip()}` "
            
            # Cleanup multiple newlines
            content_md = re.sub(r'\n{3,}', '\n\n', content_md)

        self.docs_data[url] = {
            "url": url,
            "title": title,
            "module": module,
            "path": urlparse(url).path,
            "content": content_md[:50000] 
        }

    def get_data(self):
        return list(self.docs_data.values())

    def save_data(self, filename="miniorange_docs.json"):
         with open(filename, "w") as f:
            json.dump(self.get_data(), f, indent=2)
            print(f"Saved data to {filename}")

if __name__ == "__main__":
    print("Starting recursively crawl...")
    crawler = Crawler()
    crawler.crawl("https://developers.miniorange.com/")
    
    print(f"Crawling complete. Found {len(crawler.docs_data)} documentation pages.")
    crawler.save_data()
