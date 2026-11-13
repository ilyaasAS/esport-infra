import asyncio
import logging
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from sse_starlette.sse import EventSourceResponse

from app.graph import agent_graph
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_agent_service.main")

app = FastAPI(
    title="Esport Hub Multi-Agent Service",
    description="Microservice d'orchestration multi-agents LangGraph (Python)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_role: str = "USER"
    thread_id: str | None = None

@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": "ai-agent-service",
        "version": "2.0.0"
    }

@app.post("/api/agents/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    Point d'entrée de streaming SSE pour l'orchestration multi-agents LangGraph.
    Consommé par le BFF Spring Boot via WebClient réactif.
    """
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "messages": [HumanMessage(content=req.message)],
        "user_role": req.user_role,
        "scout_context": None,
        "referee_context": None,
        "requires_human_approval": False,
        "final_response": None
    }

    async def event_generator():
        try:
            logger.info(f"Démarrage de l'inférence LangGraph pour thread_id={thread_id}")
            result = await asyncio.to_thread(agent_graph.invoke, initial_state, config)
            response_text = result.get("final_response") or "L'Oracle n'a pas pu formuler de réponse."

            # Découpage par mots pour un streaming SSE progressif fluide
            words = response_text.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield {"data": chunk}
                await asyncio.sleep(0.015)
        except Exception as ex:
            logger.error(f"Erreur lors de l'exécution du graphe LangGraph : {ex}", exc_info=True)
            yield {"data": "Une erreur est survenue lors de l'orchestration multi-agents."}

    return EventSourceResponse(event_generator())
