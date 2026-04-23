# import os
# import json
# import asyncio
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from groq import Groq
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from contextlib import asynccontextmanager

# # ─── CONFIGURATION ──────────────────────────────────────────────────
# GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# MODEL = "llama-3.3-70b-versatile"

# # Path to your MCP server (Django Bridge)
# SERVER_PARAMS = StdioServerParameters(
#     command="python",
#     args=["/app/mcp_server.py"], 
# )

# # ─── SCHEMAS ────────────────────────────────────────────────────────
# class ChatRequest(BaseModel):
#     message: str

# class ChatResponse(BaseModel):
#     response: str

# # ─── BRAIN LOGIC ────────────────────────────────────────────────────
# class GroqBrain:
#     def __init__(self):
#         self.client = Groq(api_key=GROQ_API_KEY)
#         self.tools = []

#     async def get_tools(self, session):
#         """Fetch tools from the MCP server once."""
#         mcp_tools = await session.list_tools()
#         return [
#             {
#                 "type": "function",
#                 "function": {
#                     "name": t.name,
#                     "description": t.description,
#                     "parameters": t.inputSchema
#                 }
#             } for t in mcp_tools.tools
#         ]

#     async def process_request(self, user_input, session):
#         messages = [{"role": "user", "content": user_input}]
        
#         # 1. Ask Groq if it needs a tool
#         response = self.client.chat.completions.create(
#             model=MODEL,
#             messages=messages,
#             tools=self.tools if self.tools else None,
#             tool_choice="auto" if self.tools else None
#         )

#         response_message = response.choices[0].message
#         tool_calls = response_message.tool_calls

#         # 2. If Groq wants to use a tool, call it via MCP
#         if tool_calls and session:
#             messages.append(response_message)
#             for tool_call in tool_calls:
#                 function_name = tool_call.function.name
#                 function_args = json.loads(tool_call.function.arguments)
                
#                 # Call the MCP Tool (The Django Bridge)
#                 result = await session.call_tool(function_name, function_args)
                
#                 messages.append({
#                     "role": "tool",
#                     "tool_call_id": tool_call.id,
#                     "name": function_name,
#                     "content": str(result.content)
#                 })
            
#             # 3. Get final natural language response from Groq
#             final_response = self.client.chat.completions.create(
#                 model=MODEL,
#                 messages=messages
#             )
#             return final_response.choices[0].message.content
        
#         return response_message.content

# brain = GroqBrain()

# # ─── LIFECYCLE ──────────────────────────────────────────────────────
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # This keeps the MCP connection alive for the whole time FastAPI is running
#     async with stdio_client(SERVER_PARAMS) as (read, write):
#         async with ClientSession(read, write) as session:
#             await session.initialize()
#             # Cache the tools on startup
#             brain.tools = await brain.get_tools(session)
#             app.state.mcp_session = session
#             yield
#     # Connection closes when app stops

# app = FastAPI(lifespan=lifespan)

# # ─── ENDPOINTS ──────────────────────────────────────────────────────
# @app.post("/chat", response_model=ChatResponse)
# async def chat(request: ChatRequest):
#     session = app.state.mcp_session
#     try:
#         answer = await brain.process_request(request.message, session)
#         return ChatResponse(response=answer)
#     except Exception as e:
#         # Fallback to pure Groq if MCP fails during request
#         print(f"MCP Error: {e}")
#         fallback = brain.client.chat.completions.create(
#             model=MODEL,
#             messages=[{"role": "user", "content": request.message}]
#         )
#         return ChatResponse(response=fallback.choices[0].message.content)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8002)