# import sys
# import json
# import os
# from mistralai import Mistral
# from dotenv import load_dotenv
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# # Load environment variables
# load_dotenv()
# MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# app = FastAPI(title="miniOrange MCP Server")

# # Load guides
# GUIDES_FILE = "guides.json"
# DOCS_FILE = "miniorange_docs.json"
# guides = []
# docs = []

# if os.path.exists(GUIDES_FILE):
#     with open(GUIDES_FILE, "r") as f:
#         try:
#             guides = json.load(f)
#         except json.JSONDecodeError:
#             print(f"Error decoding {GUIDES_FILE}")

# if os.path.exists(DOCS_FILE):
#     with open(DOCS_FILE, "r") as f:
#         try:
#             docs = json.load(f)
#         except json.JSONDecodeError:
#             print(f"Error decoding {DOCS_FILE}")

# class ServiceRequest(BaseModel):
#     service: str

# class SearchRequest(BaseModel):
#     query: str

# def get_guide_data(service):
#     for guide in guides:
#         if service.lower() in guide["service"].lower():
#             return guide
#     return None

# def search_docs_intelligent(query):
#     query_lower = query.lower()
#     terms = [t for t in query_lower.split() if len(t) > 1] # Filter only 1-char words, keep 2-char like 'id', 'ip'
    
#     # If no valid terms, fallback to original query
#     if not terms:
#         terms = [query_lower]

#     # 1. basic filtering
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
#     top_docs = [d[1] for d in relevant_docs[:3]]
    
#     if not top_docs:
#         return "No relevant documentation found."

#     # 2. Use Mistral
#     if not MISTRAL_API_KEY or MISTRAL_API_KEY == "your_mistral_api_key_here":
#         results_summary = "\n".join([f"- [{d['title']}]({d['url']})" for d in top_docs])
#         return f"Found relevant documentation (Mistral API Key missing):\n\n{results_summary}"
        
#     try:
#         client = Mistral(api_key=MISTRAL_API_KEY)
        
#         context = ""
#         for doc in top_docs:
#             context += f"--- Document: {doc['title']} ({doc['url']}) ---\n"
#             context += doc.get('content', '')[:10000]
#             context += "\n\n"

#         system_prompt = "You are a detailed-oriented technical support engineer for miniOrange. Your goal is to provide actionable solutions. Always include specific code snippets (PHP, Python, Java, etc.), configuration examples, and step-by-step guides from the documentation. If the user asks for credentials (client id, secret), explain where to find them in the dashboard/console. Format your response in Markdown with clear headings and code blocks."
        
#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
#         ]

#         chat_response = client.chat.complete(
#             model="mistral-large-latest",
#             messages=messages,
#         )
        
#         return chat_response.choices[0].message.content + "\n\n**Sources:**\n" + "\n".join([f"- <{d['url']}>" for d in top_docs])

#     except Exception as e:
#         print(f"Mistral Error: {e}")
#         return f"Error analyzing documents with AI: {e}"

# @app.get("/")
# def read_root():
#     return {"status": "ok", "message": "miniOrange MCP Server is running"}

# @app.post("/get_guide")
# def get_guide(request: ServiceRequest):
#     guide = get_guide_data(request.service)
#     if guide:
#         return guide
#     raise HTTPException(status_code=404, detail="Service not found")

# @app.get("/tools")
# def tools():
#     return {
#         "tools": [
#             {
#                 "name": "get_miniorange_guide",
#                 "description": "Fetch setup guide for miniOrange service (e.g., OAuth, SAML, etc.)",
#                 "input_schema": {
#                     "type": "object",
#                     "properties": {
#                         "service": {
#                             "type": "string",
#                             "description": "The name of the service to get a guide for (e.g. 'OAuth')"
#                         }
#                     },
#                     "required": ["service"]
#                 }
#             },
#             {
#                 "name": "generate_walkthrough",
#                 "description": "Generate a step-by-step walkthrough for a miniOrange service",
#                 "input_schema": {
#                     "type": "object",
#                     "properties": {
#                         "service": {
#                             "type": "string",
#                             "description": "The name of the service to generate a walkthrough for (e.g. 'OAuth')"
#                         }
#                     },
#                     "required": ["service"]
#                 }
#             },
#             {
#                 "name": "search_docs",
#                 "description": "Intelligent search of miniOrange documentation using Mistral AI.",
#                 "input_schema": {
#                     "type": "object",
#                     "properties": {
#                         "query": {
#                             "type": "string",
#                             "description": "The search query (e.g., 'how to configure SAML for Laravel?')"
#                         }
#                     },
#                     "required": ["query"]
#                 }
#             }
#         ]
#     }

# @app.post("/walkthrough")
# def walkthrough(request: ServiceRequest):
#     for guide in guides:
#         if request.service.lower() in guide["service"].lower():
#             steps = "\n".join(
#                 [f"{i+1}. {step}" for i, step in enumerate(guide["setup_steps"])]
#             )
#             env_vars = json.dumps(guide['env_template'], indent=2)
#             return {
#                 "walkthrough": f"""
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
#             }
#     raise HTTPException(status_code=404, detail="Service not found")

# @app.post("/search_docs")
# def search_docs(request: SearchRequest):
#     return {"result": search_docs_intelligent(request.query)}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
