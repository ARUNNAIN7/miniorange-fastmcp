# import sys
# import json
# import os
# from mistralai import Mistral
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()
# MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# # Load guides
# GUIDES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guides.json")
# DOCS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "miniorange_docs.json")
# guides = []
# docs = []

# if os.path.exists(GUIDES_FILE):
#     with open(GUIDES_FILE, "r") as f:
#         try:
#             guides = json.load(f)
#         except json.JSONDecodeError:
#             sys.stderr.write(f"Error decoding {GUIDES_FILE}\n")

# if os.path.exists(DOCS_FILE):
#     with open(DOCS_FILE, "r") as f:
#         try:
#             docs = json.load(f)
#         except json.JSONDecodeError:
#             sys.stderr.write(f"Error decoding {DOCS_FILE}\n")

# def get_guide(service):
#     for guide in guides:
#         if service.lower() in guide["service"].lower():
#             return guide
#     return None

# def generate_walkthrough(service):
#     guide = get_guide(service)
#     if not guide:
#         return None
    
#     steps = "\n".join(
#         [f"{i+1}. {step}" for i, step in enumerate(guide["setup_steps"])]
#     )
#     env_vars = json.dumps(guide['env_template'], indent=2)
    
#     return f"""
# ### Setup Walkthrough for {guide['service']} ({guide['auth_type']})

# **Prerequisites:**
# You will need: {', '.join(guide['requires'])}

# **Steps:**
# {steps}

# **Environment Configuration:**
# Create a `.env` file in your project and add the following:

# ```env
# {env_vars}
# ```

# **Next Steps:**
# Restart your application to load the new environment variables.
# """

# def search_docs_intelligent(query):
#     query_lower = query.lower()
#     terms = [t for t in query_lower.split() if len(t) > 1] # Filter only 1-char words, keep 2-char like 'id', 'ip'
    
#     if not terms:
#         terms = [query_lower]
    
#     # 1. basic filtering to find relevant docs
#     relevant_docs = []
#     for doc in docs:
#         score = 0
#         doc_title = doc.get("title", "").lower()
#         doc_url = doc.get("url", "").lower()
#         doc_content = doc.get("content", "").lower()

#         for term in terms:
#             if term in doc_title:
#                 score += 5
#             if term in doc_url:
#                 score += 3
#             if term in doc_content:
#                 score += 1
        
#         if score > 0:
#             relevant_docs.append((score, doc))
    
#     relevant_docs.sort(key=lambda x: x[0], reverse=True)
#     top_docs = [d[1] for d in relevant_docs[:3]] # Top 3 docs
    
#     if not top_docs:
#         return "No relevant documentation found for your query."

#     # 2. Use Mistral to synthesize answer
#     if not MISTRAL_API_KEY or MISTRAL_API_KEY == "your_mistral_api_key_here":
#         # Fallback to simple list if no key
#         results_summary = "\n".join([f"- [{d['title']}]({d['url']})" for d in top_docs])
#         return f"Found relevant documentation (Mistral API Key missing for full synthesis):\n\n{results_summary}"
        
#     try:
#         client = Mistral(api_key=MISTRAL_API_KEY)
        
#         context = ""
#         for doc in top_docs:
#             context += f"--- Document: {doc['title']} ({doc['url']}) ---\n"
#             context += doc.get('content', '')[:10000] # Truncate to avoid context limit
#             context += "\n\n"

#         system_prompt = "You are a detailed-oriented technical support engineer for miniOrange. Your goal is to provide actionable solutions. Always include specific code snippets (PHP, Python, Java, etc.), configuration examples, and step-by-step guides from the documentation. If the user asks for credentials (client id, secret), explain where to find them in the dashboard/console. Format your response in Markdown with clear headings and code blocks."
        
#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
#         ]

#         # Use new client.chat.complete pattern
#         chat_response = client.chat.complete(
#             model="mistral-large-latest", # using a known valid model, or open-mistral-7b
#             messages=messages,
#         )
        
#         # Access response content (structure depends on SDK version, usually .choices[0].message.content)
#         return chat_response.choices[0].message.content + "\n\n**Sources:**\n" + "\n".join([f"- <{d['url']}>" for d in top_docs])

#     except Exception as e:
#         sys.stderr.write(f"Mistral AI Error: {e}\n")
#         # Fallback
#         return f"Error analyzing documents with AI: {e}\n\nTop Results:\n" + "\n".join([f"- [{d['title']}]({d['url']})" for d in top_docs])

# def serve():
#     sys.stderr.write("Starting miniOrange MCP Stdio Server (Intelligent)...\n")
#     while True:
#         try:
#             line = sys.stdin.readline()
#             if not line:
#                 break
            
#             request = json.loads(line)
#             method = request.get("method")
#             msg_id = request.get("id")
            
#             response = None
            
#             if method == "initialize":
#                 response = {
#                     "jsonrpc": "2.0",
#                     "id": msg_id,
#                     "result": {
#                         "protocolVersion": "2024-11-05", # Standard version
#                         "capabilities": {
#                             "tools": {},
#                             "resources": {} 
#                         },
#                         "serverInfo": {
#                             "name": "miniOrange-mcp",
#                             "version": "1.0.0"
#                         }
#                     }
#                 }
#             elif method == "notifications/initialized":
#                 # client acknowledging
#                 continue
#             elif method == "resources/list":
#                 resource_list = [
#                     {
#                         "uri": "miniorange://guides",
#                         "name": "miniOrange Setup Guides",
#                         "description": "List of all available setup guides",
#                         "mimeType": "application/json"
#                     },
#                     {
#                         "uri": "miniorange://docs/index",
#                         "name": "miniOrange Documentation Index",
#                         "description": "Full index of miniOrange developer documentation",
#                         "mimeType": "application/json"
#                     }
#                 ]
                
#                 # Add individual guides as resources
#                 for guide in guides:
#                     service_name = guide.get("service", "").replace(" ", "-").lower()
#                     resource_list.append({
#                         "uri": f"miniorange://guide/{service_name}",
#                         "name": f"Guide: {guide.get('service')}",
#                         "description": f"Setup guide for {guide.get('service')}",
#                         "mimeType": "application/json"
#                     })

#                 response = {
#                     "jsonrpc": "2.0",
#                     "id": msg_id,
#                     "result": {
#                         "resources": resource_list
#                     }
#                 }
#             elif method == "resources/read":
#                 params = request.get("params", {})
#                 uri = params.get("uri")
#                 content = []
#                 is_error = False
                
#                 if uri == "miniorange://guides":
#                     content = [{
#                         "uri": uri,
#                         "mimeType": "application/json",
#                         "text": json.dumps(guides, indent=2)
#                     }]
#                 elif uri == "miniorange://docs/index":
#                     content = [{
#                         "uri": uri,
#                         "mimeType": "application/json",
#                         "text": json.dumps(docs, indent=2)
#                     }]
#                 elif uri.startswith("miniorange://guide/"):
#                     service_slug = uri.split("/")[-1]
#                     # Simple fuzzy match for the slug back to service name
#                     matched_guide = None
#                     for guide in guides:
#                         if guide.get("service", "").replace(" ", "-").lower() == service_slug:
#                             matched_guide = guide
#                             break
                    
#                     if matched_guide:
#                         content = [{
#                             "uri": uri,
#                             "mimeType": "application/json",
#                             "text": json.dumps(matched_guide, indent=2)
#                         }]
#                     else:
#                         is_error = True
#                         content = [{"uri": uri, "mimeType": "text/plain", "text": "Guide not found"}]
#                 else:
#                     is_error = True
#                     content = [{"uri": uri, "mimeType": "text/plain", "text": "Resource not found"}]

#                 response = {
#                     "jsonrpc": "2.0",
#                     "id": msg_id,
#                     "result": {
#                         "contents": content
#                     }
#                 }
#                 if is_error:
#                     response["error"] = {"code": -32602, "message": content[0]["text"]}
#                     del response["result"]

#             elif method == "tools/list":
#                 response = {
#                     "jsonrpc": "2.0",
#                     "id": msg_id,
#                     "result": {
#                         "tools": [
#                             {
#                                 "name": "get_miniorange_guide",
#                                 "description": "Fetch setup guide for miniOrange service (e.g., OAuth, SAML, etc.)",
#                                 "inputSchema": {
#                                     "type": "object",
#                                     "properties": {
#                                         "service": {
#                                             "type": "string",
#                                             "description": "The name of the service to get a guide for (e.g. 'OAuth')"
#                                         }
#                                     },
#                                     "required": ["service"]
#                                 }
#                             },
#                              {
#                                 "name": "generate_walkthrough",
#                                 "description": "Generate a step-by-step walkthrough for a miniOrange service",
#                                 "inputSchema": {
#                                     "type": "object",
#                                     "properties": {
#                                         "service": {
#                                             "type": "string",
#                                             "description": "The name of the service to generate a walkthrough for (e.g. 'OAuth')"
#                                         }
#                                     },
#                                     "required": ["service"]
#                                 }
#                             },
#                             {
#                                 "name": "search_docs",
#                                 "description": "Intelligent search of miniOrange documentation using Mistral AI. Returns synthesized answers with code and steps.",
#                                 "inputSchema": {
#                                     "type": "object",
#                                     "properties": {
#                                         "query": {
#                                             "type": "string",
#                                             "description": "The search query (e.g., 'how to configure SAML for Laravel?')"
#                                         }
#                                     },
#                                     "required": ["query"]
#                                 }
#                             }
#                         ]
#                     }
#                 }
#             elif method == "tools/call":
#                 params = request.get("params", {})
#                 name = params.get("name")
#                 args = params.get("arguments", {})
                
#                 result_content = []
#                 is_error = False

#                 if name == "get_miniorange_guide":
#                     service = args.get("service")
#                     data = get_guide(service)
#                     if data:
#                          result_content = [{"type": "text", "text": json.dumps(data, indent=2)}]
#                     else:
#                          is_error = True
#                          result_content = [{"type": "text", "text": "Service not found"}]

#                 elif name == "generate_walkthrough":
#                     service = args.get("service")
#                     text = generate_walkthrough(service)
#                     if text:
#                         result_content = [{"type": "text", "text": text}]
#                     else:
#                         is_error = True
#                         result_content = [{"type": "text", "text": "Service not found"}]

#                 elif name == "search_docs":
#                     query = args.get("query")
#                     # Use new intelligent search
#                     text = search_docs_intelligent(query)
#                     result_content = [{"type": "text", "text": text}]

#                 else:
#                     is_error = True
#                     result_content = [{"type": "text", "text": f"Unknown tool: {name}"}]

#                 response = {
#                     "jsonrpc": "2.0",
#                     "id": msg_id,
#                     "result": {
#                         "content": result_content,
#                         "isError": is_error
#                     }
#                 }
#             elif method == "ping":
#                  response = {
#                     "jsonrpc": "2.0",
#                     "id": msg_id,
#                     "result": {}
#                  }
            
#             if response:
#                 sys.stdout.write(json.dumps(response) + "\n")
#                 sys.stdout.flush()

#         except Exception as e:
#             sys.stderr.write(f"Error handling request: {e}\n")
#             continue

# if __name__ == "__main__":
#     serve()
