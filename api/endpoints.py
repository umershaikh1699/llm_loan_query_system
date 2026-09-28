from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class Query(BaseModel):
    text: str


class QueryResponse(BaseModel):
    result: Any
    explanation: Optional[str] = None


class MemoryResponse(BaseModel):
    messages: List[Dict[str, Any]]


class StatusResponse(BaseModel):
    status: str


def setup_routes(app: FastAPI, agent):
    @app.post("/query", response_model=QueryResponse)
    async def process_query(query: Query):
        """Process a natural language query about loan data"""
        response = agent.process_query(query.text)
        return response

    @app.get("/memory", response_model=MemoryResponse)
    async def get_memory():
        """Get the current session memory"""
        messages = agent.get_memory()
        return {
            "messages": [{"role": msg.type, "content": msg.content} for msg in messages]
        }

    @app.delete("/memory", response_model=StatusResponse)
    async def reset_memory():
        """Reset the session memory"""
        return agent.reset_memory()
