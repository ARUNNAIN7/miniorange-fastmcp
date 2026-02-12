import json
import os
from mistralai import Mistral
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Initialize FastMCP
mcp = FastMCP("miniOrange")

# Load guides
GUIDES_FILE = "guides.json"
DOCS_FILE = "miniorange_docs.json"
guides = []
docs = []

if os.path.exists(GUIDES_FILE):
    with open(GUIDES_FILE, "r") as f:
        try:
            guides = json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding {GUIDES_FILE}")

if os.path.exists(DOCS_FILE):
    with open(DOCS_FILE, "r") as f:
        try:
            docs = json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding {DOCS_FILE}")

def get_guide_data(service):
    for guide in guides:
        if service.lower() in guide["service"].lower():
            return guide
    return None

@mcp.tool()
def get_miniorange_guide(service: str) -> str:
    """Fetch setup guide for miniOrange service (e.g., OAuth, SAML, etc.)"""
    guide = get_guide_data(service)
    if guide:
        return json.dumps(guide, indent=2)
    return "Service not found"

@mcp.tool()
def list_plugins() -> str:
    """List all available plugins/services"""
    plugin_list = []
    seen_titles = set()
    for doc in docs:
        title = doc.get("title")
        if title and title not in seen_titles:
            plugin_list.append(title)
            seen_titles.add(title)
    return json.dumps(sorted(plugin_list), indent=2)

@mcp.tool()
def get_plugin_details(service: str) -> str:
    """Get detailed information for a specific plugin"""
    guide = get_guide_data(service)
    if guide:
        # Construct the response with specific fields
        details = {
            "service": guide.get("service"),
            "auth_type": guide.get("auth_type"),
            "requires": guide.get("requires", []),
            "description": guide.get("description", "No description available")
        }
        return json.dumps(details, indent=2)
    return "Service not found"

@mcp.tool()
def generate_walkthrough(service: str) -> str:
    """Generate a structured walkthrough for a miniOrange service"""
    for guide in guides:
        if service.lower() in guide["service"].lower():
            # Return structured JSON instead of formatted text
            walkthrough_data = {
                "service": guide.get("service"),
                "auth_type": guide.get("auth_type"),
                "steps": guide.get("setup_steps", []),
                "env_template": guide.get("env_template", {})
            }
            return json.dumps(walkthrough_data, indent=2)
    return "Service not found"

@mcp.tool()
def search_docs(query: str, scan_url: str = None) -> str:
    """Intelligent search of miniOrange documentation. Optionally scan a URL first."""
    if scan_url:
        scan_result = _scan_docs(scan_url)
        print(f"Pre-search scan: {scan_result}")

    query_lower = query.lower()
    terms = [t for t in query_lower.split() if len(t) > 1] # Filter only 1-char words, keep 2-char like 'id', 'ip'
    
    # If no valid terms, fallback to original query
    if not terms:
        terms = [query_lower]

    # 1. basic filtering
    relevant_docs = []
    for doc in docs:
        score = 0
        doc_title = doc.get("title", "").lower()
        doc_url = doc.get("url", "").lower()
        doc_content = doc.get("content", "").lower()

        for term in terms:
            if term in doc_title:
                score += 5
            if term in doc_url:
                score += 3
            if term in doc_content:
                score += 1
        
        if score > 0:
            relevant_docs.append((score, doc))
    
    relevant_docs.sort(key=lambda x: x[0], reverse=True)
    top_docs = [d[1] for d in relevant_docs[:3]]
    
    if not top_docs:
        return "No relevant documentation found."

    # 2. Use Mistral
    if not MISTRAL_API_KEY or MISTRAL_API_KEY == "your_mistral_api_key_here":
        results_summary = "\n".join([f"- [{d['title']}]({d['url']})" for d in top_docs])
        return f"Found relevant documentation (Mistral API Key missing):\n\n{results_summary}"
        
    try:
        client = Mistral(api_key=MISTRAL_API_KEY)
        
        context = ""
        for doc in top_docs:
            context += f"--- Document: {doc['title']} ({doc['url']}) ---\n"
            context += doc.get('content', '')[:10000]
            context += "\n\n"

        system_prompt = "You are a detailed-oriented technical support engineer for miniOrange. Your goal is to provide actionable solutions. Always include specific code snippets (PHP, Python, Java, etc.), configuration examples, and step-by-step guides from the documentation. If the user asks for credentials (client id, secret), explain where to find them in the dashboard/console. Format your response in Markdown with clear headings and code blocks."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]

        chat_response = client.chat.complete(
            model="mistral-large-latest",
            messages=messages,
        )
        
        return chat_response.choices[0].message.content + "\n\n**Sources:**\n" + "\n".join([f"- <{d['url']}>" for d in top_docs])

    except Exception as e:
        print(f"Mistral Error: {e}")
        return f"Error analyzing documents with AI: {e}"

def _scan_docs(url: str, depth: int = 1) -> str:
    global docs
    from recursive_crawler import Crawler

    try:
        crawler = Crawler()
        crawler.crawl(url, max_depth=depth)
        
        new_data = crawler.get_data()
        
        docs_map = {d['url']: d for d in docs}
        
        added_count = 0
        updated_count = 0
        
        for item in new_data:
            if item['url'] in docs_map:
                docs_map[item['url']] = item
                updated_count += 1
            else:
                docs_map[item['url']] = item
                added_count += 1
        
        docs = list(docs_map.values())
        
        with open(DOCS_FILE, "w") as f:
            json.dump(docs, f, indent=2)
            
        return f"Successfully scanned {url}. Added {added_count} pages, updated {updated_count} pages."

    except Exception as e:
        return f"Error scanning documentation: {e}"

@mcp.tool()
def scan_documentation(url: str, depth: int = 1) -> str:
    """Scan a documentation page (and optionally children) in real-time and update the knowledge base."""
    return _scan_docs(url, depth)




if __name__ == "__main__":
    mcp.run()
