from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class EsportAgentState(TypedDict):
    """
    État partagé traversant l'ensemble des nœuds du graphe LangGraph.
    Permet la collaboration itérative et la persistance des contextes d'arbitrage et de scoutisme.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_step: Literal["supervisor", "scout", "referee", "human_approval", "__end__"]
    user_role: Literal["ADMIN", "USER"]
    scout_context: str | None
    referee_context: str | None
    requires_human_approval: bool
    final_response: str | None
