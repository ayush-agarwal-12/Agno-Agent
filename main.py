import os
import json
import uuid
from typing import Dict, Optional, AsyncGenerator
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Agno Imports
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools


# Load environment variables
load_dotenv()

# --- LIFECYCLE ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("------------------------------------------------")
    print("Server Started!")
    if os.getenv("GROQ_API_KEY"):
        print("GROQ_API_KEY found.")
    else:
        print("WARNING: GROQ_API_KEY NOT FOUND in .env file.")
    print("------------------------------------------------")
    yield

app = FastAPI(
    title="Agno Streaming Chat API",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage
session_store: Dict[str, list] = {}

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID")

def get_or_create_session_id(session_id: Optional[str] = None) -> str:
    """Get existing session or create a new one."""
    if session_id and session_id in session_store:
        return session_id
    new_session_id = session_id or str(uuid.uuid4())
    if new_session_id not in session_store:
        session_store[new_session_id] = []
    return new_session_id

def add_to_session_history(session_id: str, role: str, content: str):
    """Add a message to session history."""
    if session_id not in session_store:
        session_store[session_id] = []
    session_store[session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })

def create_research_agent(session_id: str) -> Agent:
    """
    Creates a research agent configured for Agno v2.
    
    Key fixes applied:
    1. Removed deprecated 'show_tool_calls' parameter (v2 has this always enabled)
    2. Set temperature to 0.0 for consistent, reproducible outputs
    3. Proper conversation context management
    """
    history = session_store.get(session_id, [])
    
    # Build conversation context from history
    conversation_context = ""
    if history:
        conversation_context = "\n\nPrevious conversation:\n"
        for msg in history[-6:]:  # Last 6 messages for context
            conversation_context += f"{msg['role']}: {msg['content']}\n"
    
    # Clear, specific instructions
    instructions = [
        "You are a helpful assistant.",
        "When asked about current information, use DuckDuckGo search.",
        "Always use the search tool for questions about news, weather, or current events.",
        "Do no Add special symbols and emojis"
    ]
    
    if conversation_context:
        instructions.append(conversation_context)
    
    # Create agent with v2-compatible parameters
    # Note: show_tool_calls is REMOVED in v2 (always enabled by default)
    # Using debug_mode=False to avoid excessive logging
    agent = Agent(
        name="Research Assistant",
        role="Expert research assistant",
        model=Groq(
            id="openai/gpt-oss-120b",
            temperature=0.0  # Set to 0 for consistent outputs
        ),
        tools=[
            DuckDuckGoTools(),
            Newspaper4kTools()
        ],
        instructions=instructions,
        markdown=True,
        debug_mode=False,  # Set to True only for deep debugging
    )
    
    return agent

async def stream_agent_response(agent: Agent, message: str, session_id: str) -> AsyncGenerator[str, None]:
    """
    Stream the agent's response using Server-Sent Events (SSE) format.
    
    Handles:
    - Proper chunk extraction from RunResponse objects
    - Error handling and reporting
    - Session history management
    """
    try:
        # Add user message to history
        add_to_session_history(session_id, "user", message)
        
        # Send start event
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
        await asyncio.sleep(0.01)
        
        full_response_text = ""
        
        # Run agent with streaming
        response_generator = agent.run(message, stream=True)
        
        for chunk in response_generator:
            content = ""
            
            # Extract content from various chunk types
            if hasattr(chunk, "content") and chunk.content is not None:
                content = str(chunk.content)
            elif isinstance(chunk, str):
                content = chunk
            
            # Stream non-empty content
            if content:
                full_response_text += content
                data = {'type': 'token', 'content': content}
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(0.01)
        
        # Add assistant's response to history
        if full_response_text:
            add_to_session_history(session_id, "assistant", full_response_text)
        
        # Send completion event
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
        
    except Exception as e:
        print(f"Stream Error: {e}")
        error_data = {'type': 'error', 'error': str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"

@app.post("/chat")
async def chat_stream(request: ChatRequest):
    """
    Main chat endpoint for streaming responses.
    
    Args:
        request: ChatRequest containing message and optional session_id
    
    Returns:
        StreamingResponse with Server-Sent Events
    """
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY missing")
    
    session_id = get_or_create_session_id(request.session_id)
    
    try:
        agent = create_research_agent(session_id)
    except Exception as e:
        print(f"Agent Creation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent creation failed: {str(e)}")
    
    return StreamingResponse(
        stream_agent_response(agent, request.message, session_id),
        media_type="text/event-stream"
    )

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serves the frontend HTML file."""
    try:
        with open("index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Frontend not found</h1><p>Please create an index.html file</p>",
            status_code=404
        )

@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    sessions_info = []
    for session_id, history in session_store.items():
        sessions_info.append({
            "session_id": session_id,
            "message_count": len(history),
            "last_message": history[-1]["timestamp"] if history else None
        })
    return {"sessions": sessions_info}

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get specific session history."""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "history": session_store[session_id]}

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session."""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found")
    del session_store[session_id]
    return {"message": f"Session {session_id} deleted successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(session_store),
        "agno_version": "2.0",
        "groq_api_configured": bool(os.getenv("GROQ_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)