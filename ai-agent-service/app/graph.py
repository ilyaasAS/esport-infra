import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings
from app.state import EsportAgentState
from app.tools.chroma_rules import query_tournament_rules
from app.tools.backend_client import fetch_players, fetch_matches

logger = logging.getLogger("ai_agent_service.graph")

SUPERVISOR_SYSTEM_PROMPT = """Tu es l'Agent Superviseur de la ligue e-sport Esport Hub.
Ton rôle est de coordonner les requêtes des utilisateurs entre l'Agent Scout (statistiques, classements, Elo) et l'Agent Arbitre (règlements officiels ChromaDB).
- Si les données de l'Arbitre ou du Scout sont présentes dans le contexte, synthétise une réponse finale fluide, concise, professionnelle et sans hallucination en français.
- Ne mentionne jamais le nom interne des nœuds ou du graphe."""

SCOUT_SYSTEM_PROMPT = """Tu es l'Agent Scout & Analyste de données de la ligue e-sport.
Ton rôle est de restituer avec précision les statistiques réelles, classements (Top X) et historiques de la ligue.
Sois analytique, chiffré, froid et concis."""

REFEREE_SYSTEM_PROMPT = """Tu es l'Agent Arbitre officiel de la ligue e-sport.
Ton rôle est d'appliquer strictement le règlement officiel (Articles 1 à 6).
OBLIGATION ABSOLUE : Cite systématiquement le numéro d'article applicable (ex: Article 5, Article 6.3) et base ta réponse uniquement sur les extraits fournis."""

def get_chat_model(temperature: float = 0.2):
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=temperature
    )

def supervisor_node(state: EsportAgentState) -> dict:
    """
    Nœud Superviseur : Analyse la requête, détermine l'orientation vers le Scout ou le Referee,
    ou formule la synthèse finale à partir des contextes récoltés.
    """
    messages = state.get("messages", [])
    last_user_message = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")
    scout_ctx = state.get("scout_context")
    referee_ctx = state.get("referee_context")

    # Si nous avons déjà des éléments spécialisés, le Superviseur synthétise la réponse finale
    if scout_ctx or referee_ctx:
        logger.info("Superviseur : Synthèse finale à partir des contextes spécialisés")
        context_block = ""
        if scout_ctx:
            context_block += f"\n[DONNÉES DU SCOUT]\n{scout_ctx}\n"
        if referee_ctx:
            context_block += f"\n[RÈGLEMENT OFFICIEL DE L'ARBITRE]\n{referee_ctx}\n"

        llm = get_chat_model(temperature=0.2)
        prompt = [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT + context_block),
            HumanMessage(content=last_user_message)
        ]
        resp = llm.invoke(prompt)
        return {
            "final_response": resp.content,
            "next_step": "__end__",
            "messages": [AIMessage(content=resp.content)]
        }

    # Analyse de la requête pour décision de routage
    lower_query = last_user_message.lower()
    rule_keywords = ["règle", "regle", "règlement", "reglement", "déconnexion", "deconnexion", "forfait", "crash", "sanction", "litige", "arbitre", "code de conduite"]
    scout_keywords = ["top", "classement", "joueur", "player", "match", "score", "elo", "cote", "pronostic", "prédire", "predire", "gagnant"]

    is_rule = any(kw in lower_query for kw in rule_keywords)
    is_scout = any(kw in lower_query for kw in scout_keywords)

    if is_rule and not referee_ctx:
        logger.info("Superviseur : Routage vers l'Agent Arbitre (Referee)")
        return {"next_step": "referee"}
    elif is_scout and not scout_ctx:
        logger.info("Superviseur : Routage vers l'Agent Scout")
        return {"next_step": "scout"}

    # Requête conversationnelle générale directe
    llm = get_chat_model(temperature=0.2)
    resp = llm.invoke([
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=last_user_message)
    ])
    return {
        "final_response": resp.content,
        "next_step": "__end__",
        "messages": [AIMessage(content=resp.content)]
    }

def scout_node(state: EsportAgentState) -> dict:
    """
    Nœud Scout : Récupère les données réelles de ligue (MySQL) et synthétise l'analyse.
    """
    logger.info("Exécution du nœud Scout")
    players = fetch_players()
    matches = fetch_matches()

    summary = f"Nombre de joueurs dans la ligue : {len(players)}.\n"
    if players:
        sorted_players = sorted(players, key=lambda p: p.get("score", 0), reverse=True)[:5]
        summary += "Top joueurs par score :\n"
        for i, p in enumerate(sorted_players, 1):
            summary += f"- {i}. {p.get('nickname')} (niveau {p.get('level')}, score {p.get('score')})\n"

    if matches:
        summary += f"Nombre de matchs disputés : {len(matches)}.\n"

    return {
        "scout_context": summary,
        "next_step": "supervisor"
    }

def referee_node(state: EsportAgentState) -> dict:
    """
    Nœud Arbitre : Interroge la base vectorielle ChromaDB sur le Rulebook officiel.
    """
    logger.info("Exécution du nœud Arbitre (RAG ChromaDB)")
    messages = state.get("messages", [])
    last_user_message = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")

    rule_excerpts = query_tournament_rules(last_user_message, top_k=3)

    return {
        "referee_context": rule_excerpts,
        "next_step": "supervisor"
    }

def route_decision(state: EsportAgentState) -> str:
    """
    Condition de routage dynamique depuis le superviseur.
    """
    next_step = state.get("next_step", "__end__")
    if next_step in ("scout", "referee"):
        return next_step
    return "__end__"

def build_graph():
    """
    Assemble le StateGraph cyclique avec persistance d'états (MemorySaver).
    """
    builder = StateGraph(EsportAgentState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("scout", scout_node)
    builder.add_node("referee", referee_node)

    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges(
        "supervisor",
        route_decision,
        {
            "scout": "scout",
            "referee": "referee",
            "__end__": END
        }
    )

    # Boucles de collaboration cyclique vers le superviseur
    builder.add_edge("scout", "supervisor")
    builder.add_edge("referee", "supervisor")

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)

agent_graph = build_graph()
