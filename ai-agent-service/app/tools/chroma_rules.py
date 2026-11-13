import logging
import chromadb
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from app.config import settings

logger = logging.getLogger("ai_agent_service.chroma_rules")

def query_tournament_rules(query: str, top_k: int = 3) -> str:
    """
    Recherche sémantique dans le corpus officiel ChromaDB (collection esport-rules).
    """
    try:
        embeddings = OllamaEmbeddings(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_EMBEDDING_MODEL
        )
        client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT
        )
        vector_store = Chroma(
            client=client,
            collection_name=settings.CHROMA_COLLECTION,
            embedding_function=embeddings
        )
        docs = vector_store.similarity_search(query, k=top_k)
        if not docs:
            return "Aucun article de règlement officiel ne correspond spécifiquement à cette requête."

        formatted_chunks = []
        for i, doc in enumerate(docs, 1):
            formatted_chunks.append(f"[Extrait {i}]\n{doc.page_content.strip()}")

        return "\n\n".join(formatted_chunks)
    except Exception as ex:
        logger.error(f"Erreur lors de la consultation ChromaDB: {ex}", exc_info=True)
        return "Le service de consultation du règlement officiel est temporairement indisponible."
