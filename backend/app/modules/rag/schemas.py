from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class RAGQuery(BaseModel):
    query: str
    top_k: Optional[int] = 5
    user_role: Optional[str] = "user"


class RAGResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    confidence: float = 0.8


class DocumentIngestionRequest(BaseModel):
    source_type: str  # guideline, protocol, manual, research
    source_id: Optional[str] = None
    title: str
    content: str
    source_url: Optional[str] = None
    published_date: Optional[datetime] = None
    tags: Optional[List[str]] = []
    language: Optional[str] = "en"
