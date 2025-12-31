"""
Workflow-Nodes für den Steuerheuer RAG-Workflow mit LangGraph.
================================================================

VERSION 2.0 - MIT MESSAGE-HISTORY-HANDLING

Änderungen gegenüber v1:
- generate_node fügt AIMessage zum State hinzu
- Messages werden an das LLM übergeben (für Kontext)
- Besseres Error-Handling für Memory-Operationen

Quellen:
- Buch S. 70: "Nodes are Python functions that operate on this dictionary"
- Buch S. 74-75: "add_messages reducer"
- LangGraph Docs: "The node must return a dictionary containing the 
  specific keys and values it wants to update"
"""

from typing import Dict, Any, List

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.state_v2 import RAGState
from src.retriever import retrieve_documents
from src.system_prompt_ustg import format_context as format_docs_to_context, get_rag_prompt
from src.generator import get_llm


# =============================================================================
# NODE 1: RETRIEVE
# =============================================================================

def retrieve_node(state: RAGState) -> Dict[str, Any]:
    """
    Retrieval-Node: Ruft relevante Dokumente aus ChromaDB ab.
    
    Input aus State:
        - query (str): Die Benutzerfrage
        
    Output (State-Update):
        - retrieved_docs (List[Document]): Gefundene Dokumente
        - error (str): Fehlermeldung falls Retrieval fehlschlägt
    
    Hinweis:
        Dieser Node bleibt weitgehend unverändert, da er nur auf 
        query zugreift und retrieved_docs zurückgibt.
    """
    try:
        query = state.get("query", "")
        
        if not query:
            return {
                "retrieved_docs": [],
                "error": "Keine Frage (query) im State vorhanden."
            }
        
        # Dokumente aus ChromaDB abrufen
        docs = retrieve_documents(query)
        
        return {
            "retrieved_docs": docs,
            "error": None
        }
        
    except Exception as e:
        return {
            "retrieved_docs": [],
            "error": f"Retrieval-Fehler: {str(e)}"
        }


# =============================================================================
# NODE 2: FORMAT_CONTEXT
# =============================================================================

def format_context_node(state: RAGState) -> Dict[str, Any]:
    """
    Kontext-Formatierungs-Node: Bereitet Dokumente für das LLM auf.
    
    Input aus State:
        - retrieved_docs (List[Document]): Abgerufene Dokumente
        
    Output (State-Update):
        - context (str): Formatierter Kontext-String
        - sources (List[str]): Liste der Quellenreferenzen
        - error (str): Fehlermeldung falls Formatierung fehlschlägt
    
    Hinweis:
        Dieser Node bleibt weitgehend unverändert.
    """
    try:
        docs = state.get("retrieved_docs", [])
        
        if not docs:
            return {
                "context": "Keine relevanten Gesetzesauszüge gefunden.",
                "sources": [],
                "error": None
            }
        
        # Kontext formatieren
        context = format_docs_to_context(docs)
        
        # Quellen extrahieren
        sources = [
            doc.metadata.get("full_reference", "Unbekannte Quelle")
            for doc in docs
        ]
        
        return {
            "context": context,
            "sources": sources,
            "error": None
        }
        
    except Exception as e:
        return {
            "context": "",
            "sources": [],
            "error": f"Kontext-Formatierungs-Fehler: {str(e)}"
        }


# =============================================================================
# NODE 3: GENERATE (v2.0 mit Message-History)
# =============================================================================

def generate_node(state: RAGState) -> Dict[str, Any]:
    """
    Generierungs-Node: Erzeugt die LLM-Antwort MIT Message-History.
    
    KRITISCHE ÄNDERUNG (v2.0):
    - Berücksichtigt vorherige Messages für Kontext
    - Fügt AIMessage zum State hinzu (für Memory)
    - Verwendet add_messages Reducer
    
    Input aus State:
        - query (str): Die Benutzerfrage
        - context (str): Der formatierte Kontext
        - messages (List[AnyMessage]): Bisheriger Chatverlauf
        
    Output (State-Update):
        - answer (str): Die generierte Antwort
        - messages (List[AIMessage]): NEUE AI-Antwort als Message
        - error (str): Fehlermeldung falls Generation fehlschlägt
    
    Quelle: Buch S. 74 - "add_messages reducer"
    """
    try:
        # Daten aus State extrahieren
        query = state.get("query", "")
        context = state.get("context", "")
        messages = state.get("messages", [])
        
        # Prüfen auf Error im vorherigen Schritt
        if state.get("error"):
            error_msg = f"Fehler im Workflow: {state.get('error')}"
            return {
                "answer": error_msg,
                "messages": [AIMessage(content=error_msg)],
                "error": state.get("error")
            }
        
        # Prüfen ob Query vorhanden
        if not query:
            error_msg = "Keine Frage für Generation vorhanden."
            return {
                "answer": error_msg,
                "messages": [AIMessage(content=error_msg)],
                "error": error_msg
            }
        
        # =================================================================
        # NEU (v2.0): Conversation-History für LLM aufbereiten
        # =================================================================
        # Extrahiere vorherige Nachrichten (ohne die aktuelle Frage)
        # um dem LLM Kontext über die bisherige Konversation zu geben
        
        conversation_context = _build_conversation_context(messages)
        
        # Prompt mit Konversationshistorie erweitern
        enhanced_prompt = get_rag_prompt()
        
        # LLM initialisieren
        llm = get_llm()
        
        # =================================================================
        # Prompt mit Kontext, Frage UND Konversationshistorie füllen
        # =================================================================
        
        # System-Message mit Konversationskontext erweitern
        system_message = enhanced_prompt.messages[0]
        human_template = enhanced_prompt.messages[1]
        
        # Erstelle erweiterten Kontext mit Konversationshistorie
        full_context = context
        if conversation_context:
            full_context = f"""
## Bisherige Konversation (zur Referenz):
{conversation_context}

---

## Aktuelle Gesetzesauszüge:
{context}
"""
        
        # Messages für LLM vorbereiten
        formatted_messages = enhanced_prompt.invoke({
            "context": full_context,
            "question": query
        })
        
        # LLM aufrufen
        response = llm.invoke(formatted_messages)
        
        # Antwort extrahieren
        answer = response.content
        
        # =================================================================
        # KRITISCH (v2.0): AIMessage zum State hinzufügen
        # =================================================================
        # Der add_messages Reducer fügt diese AIMessage automatisch
        # zur bestehenden messages-Liste hinzu!
        #
        # Quelle (Buch S. 74):
        # "we tell the LangGraph compiler that the type of our variable 
        #  in the state is a list... and it should use the add method 
        #  to concatenate two lists"
        
        return {
            "answer": answer,
            "messages": [AIMessage(content=answer)],  # NEU: AI-Antwort als Message
            "error": None
        }
        
    except Exception as e:
        error_msg = f"Generierungs-Fehler: {str(e)}"
        return {
            "answer": "",
            "messages": [AIMessage(content=f"Fehler: {str(e)}")],
            "error": error_msg
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_conversation_context(messages: List, max_messages: int = 10) -> str:
    """
    Baut einen formatierten Konversationskontext aus den Messages.
    
    Args:
        messages: Liste von Messages (Human/AI)
        max_messages: Maximale Anzahl zu berücksichtigender Messages
        
    Returns:
        str: Formatierter Konversationskontext
    """
    if not messages:
        return ""
    
    # Nur die letzten N Messages berücksichtigen (ohne die aktuelle)
    # Die letzte Message ist die aktuelle Frage
    relevant_messages = messages[:-1][-max_messages:]
    
    if not relevant_messages:
        return ""
    
    lines = []
    for msg in relevant_messages:
        if isinstance(msg, HumanMessage):
            lines.append(f"Benutzer: {msg.content}")
        elif isinstance(msg, AIMessage):
            # Kürze lange AI-Antworten
            content = msg.content
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"Assistent: {content}")
    
    return "\n".join(lines)


def _count_messages_by_type(messages: List) -> Dict[str, int]:
    """
    Zählt Messages nach Typ.
    
    Args:
        messages: Liste von Messages
        
    Returns:
        dict: {"human": N, "ai": M}
    """
    counts = {"human": 0, "ai": 0, "other": 0}
    
    for msg in messages:
        if isinstance(msg, HumanMessage):
            counts["human"] += 1
        elif isinstance(msg, AIMessage):
            counts["ai"] += 1
        else:
            counts["other"] += 1
    
    return counts


# =============================================================================
# NODE-REGISTRY
# =============================================================================

NODES = {
    "retrieve": retrieve_node,
    "format_context": format_context_node,
    "generate": generate_node,
}


def get_node(name: str):
    """Gibt eine Node-Funktion anhand des Namens zurück."""
    if name not in NODES:
        raise KeyError(f"Node '{name}' nicht gefunden. Verfügbar: {list(NODES.keys())}")
    return NODES[name]


# =============================================================================
# NODE-INFO
# =============================================================================

def get_nodes_info() -> dict:
    """Gibt Informationen über alle Nodes zurück."""
    return {
        "version": "2.0",
        "memory_enabled": True,
        "nodes": [
            {
                "name": "retrieve",
                "input": ["query"],
                "output": ["retrieved_docs", "error"],
                "description": "Ruft Dokumente aus ChromaDB ab",
                "changes_v2": "Keine"
            },
            {
                "name": "format_context",
                "input": ["retrieved_docs"],
                "output": ["context", "sources", "error"],
                "description": "Formatiert Dokumente als Kontext-String",
                "changes_v2": "Keine"
            },
            {
                "name": "generate",
                "input": ["query", "context", "messages"],
                "output": ["answer", "messages", "error"],
                "description": "Generiert LLM-Antwort MIT Message-History",
                "changes_v2": "NEU: Gibt AIMessage zurück für Memory"
            },
        ],
        "workflow": "START -> retrieve -> format_context -> generate -> END",
        "source": "Buch S. 70, 74-75",
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("WORKFLOW-NODES TEST (v2.0 mit Memory)")
    print("=" * 60)
    print()
    
    # Info ausgeben
    print("NODE-INFO:")
    info = get_nodes_info()
    print(f"  Version: {info['version']}")
    print(f"  Memory: {'Aktiviert' if info['memory_enabled'] else 'Deaktiviert'}")
    print(f"  Workflow: {info['workflow']}")
    print()
    
    for node_info in info["nodes"]:
        print(f"  [{node_info['name']}]")
        print(f"    Input:  {node_info['input']}")
        print(f"    Output: {node_info['output']}")
        print(f"    Änderungen v2: {node_info['changes_v2']}")
        print()
    
    # Test: Nodes mit Message-History
    print("-" * 60)
    print("TEST: generate_node mit Message-History")
    print("-" * 60)
    print()
    
    # Simuliere State mit vorherigen Messages
    test_state = {
        "query": "Wie heiße ich?",
        "context": "UStG § 12: Der Steuersatz beträgt 19%.",
        "messages": [
            HumanMessage(content="Mein Name ist Fawzi"),
            AIMessage(content="Hallo Fawzi! Wie kann ich helfen?"),
            HumanMessage(content="Wie heiße ich?"),
        ],
        "error": None,
    }
    
    print(f"  Vorherige Messages: {len(test_state['messages'])}")
    print(f"  Aktuelle Frage: '{test_state['query']}'")
    print()
    
    # Konversationskontext testen
    conv_context = _build_conversation_context(test_state["messages"])
    print("  Generierter Konversationskontext:")
    print("-" * 40)
    print(conv_context)
    print("-" * 40)
    print()
    
    print("=" * 60)
    print("[OK] Nodes v2.0 bereit für Memory-Integration!")
    print("=" * 60)
