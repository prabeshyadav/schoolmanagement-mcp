import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq, BadRequestError
import re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import asynccontextmanager

# ─── CONFIG ───────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"
MCP_SERVER_FILE = os.environ.get("MCP_SERVER_FILE", None)
# Load system prompt from prompts/system.txt when available for easier iteration
try:
    with open("prompts/system.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except Exception:
    SYSTEM_PROMPT = (
        "You are a School Management Assistant. "
        "Use tools when the user asks for real data like teachers, students, etc. "
        "If a tool is used, return the tool result directly."
    )

# ─── SCHEMAS ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str


# ─── BRAIN ────────────────────────────────────────────────
class GroqBrain:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.tools = []

    async def get_tools(self, session):
        mcp_tools = await session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema
                }
            }
            for t in mcp_tools.tools
        ]

    async def process_request(self, user_input, session=None):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]

        tool_kwargs = {"tools": self.tools, "tool_choice": "auto"} if self.tools else {}

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                **tool_kwargs
            )
            response_message = response.choices[0].message

        except BadRequestError as e:
            # Handle Groq 'tool_use_failed' errors where the model attempted a tool call
            # but the request failed. Try to extract the failed function and invoke it
            # directly via the MCP session as a fallback, otherwise ask the model
            # again without tool definitions.
            err_text = str(e)
            m = re.search(r"failed_generation'?:\s*'?(<function=[^']+>)", err_text)
            fn_name = None
            if m:
                failed = m.group(1)
                fnm = re.search(r'function=([a-zA-Z0-9_]+)', failed)
                if fnm:
                    fn_name = fnm.group(1)

            if fn_name and session:
                try:
                    result = await session.call_tool(fn_name, {})
                    if result.content:
                        return result.content[0].text
                    return "Tool executed but returned no data."
                except Exception as e2:
                    print(f"Fallback tool execution failed: {e2}")
                    # Fall through to retry model without tools

            # Retry the request without tool definitions as a safe fallback
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages
            )
            response_message = response.choices[0].message

        # 🧠 DEBUG
        if response_message.tool_calls:
            print(f"DEBUG: Tool Calls → {[t.function.name for t in response_message.tool_calls]}")
        else:
            print("DEBUG: No tool call")

        # ─── TOOL EXECUTION ───────────────────────────────
        if response_message.tool_calls and session:
            for tool_call in response_message.tool_calls:
                try:
                    tool_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments or "{}")

                    print(f"🛠️ Calling Tool: {tool_name} with {args}")

                    result = await session.call_tool(tool_name, args)

                    print(f"✅ Tool Raw Result: {result}")

                    # ✅ Extract actual data from MCP result
                    if result.content:
                        tool_text = result.content[0].text
                        return tool_text

                    return "Tool executed but returned no data."

                except Exception as e:
                    print(f"❌ Tool Error: {e}")
                    return f"Error executing tool: {e}"

        # ─── NORMAL CHAT ─────────────────────────────────
        return response_message.content


brain = GroqBrain()


# ─── LIFESPAN (MCP CONNECTOR) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    if MCP_SERVER_FILE:
        params = StdioServerParameters(command="python", args=[MCP_SERVER_FILE])
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    brain.tools = await brain.get_tools(session)

                    tool_names = [t['function']['name'] for t in brain.tools]
                    print(f"🧠 Connected Tools: {tool_names}")

                    app.state.mcp_session = session
                    yield

        except Exception as e:
            print(f"⚠️ MCP failed: {e}")
            app.state.mcp_session = None
            yield
    else:
        print("💬 Running without MCP tools")
        app.state.mcp_session = None
        yield


app = FastAPI(lifespan=lifespan)


# ─── CHAT ENDPOINT ───────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session = getattr(app.state, "mcp_session", None)

    answer = await brain.process_request(request.message, session)

    return ChatResponse(response=answer)


# ─── RUN ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)