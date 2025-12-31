"""
State-Schema für den Steuerheuer RAG-Workflow mit LangGraph.
==============================================================

VERSION 2.0 - MIT KONVERSATIONSGEDÄCHTNIS

Änderungen gegenüber v1:
- NEUES FELD 'messages' für Chat-History
- Verwendet add_messages Reducer für automatisches Merging
- Ermöglicht Multi-Turn-Konversationen

Quellen:
- Buch S. 74-75: "add_messages reducer"
- Buch S. 97-103: "Understanding memory mechanisms"
- LangGraph Docs: "MessagesState"
"""

from typing import List, Optional, Annotated
from typing_extensions import TypedDict

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages


# =============================================================================
# RAG WORKFLOW STATE SCHEMA (v2.0 mit Memory)
# =============================================================================

class RAGState(TypedDict, total=False):
    """
    Erweitertes State-Schema mit Konversationsgedächtnis.
    
    NEUES FELD 'messages' (v2.0):
    - Speichert den gesamten Chatverlauf als Liste von Messages
    - Verwendet den add_messages Reducer für automatisches Merging
    - Ermöglicht dem LLM, vorherige Interaktionen zu "sehen"
    
    Attribute:
        query (str): 
            Die aktuelle Benutzerfrage.
            
        messages (Annotated[list[AnyMessage], add_messages]):
            NEU: Vollständiger Chatverlauf (Human + AI Messages).
            Der add_messages Reducer sorgt dafür, dass neue Messages
            automatisch zur bestehenden Liste hinzugefügt werden.
            
        retrieved_docs (Optional[List[Document]]): 
            Aus ChromaDB abgerufene Dokumente.
            
        context (Optional[str]): 
            Formatierter Kontext-String für das LLM.
            
        sources (Optional[List[str]]): 
            Quellenreferenzen (z.B. ["UStG § 12 Abs. 1"]).
            
        answer (Optional[str]): 
            Die generierte Antwort des LLM.
            
        error (Optional[str]): 
            Fehlermeldung falls ein Node fehlschlägt.
    
    Workflow-Datenfluss mit Memory:
        1. User stellt Frage -> HumanMessage wird zu messages hinzugefügt
        2. retrieve(query) -> retrieved_docs
        3. format_context(retrieved_docs) -> context, sources
        4. generate(query, context, messages) -> answer
        5. AIMessage wird zu messages hinzugefügt
        6. Checkpointer speichert den State
        
        Bei nächster Frage:
        1. Checkpointer lädt State (inkl. messages)
        2. Workflow hat Zugriff auf vorherige Konversation
    
    Quelle: Buch S. 74-75 - add_messages Reducer
    """
    
    # === EINGABE ===
    query: str
    """Die aktuelle Benutzerfrage (Pflichtfeld bei Start)."""
    
    # === NEU: CONVERSATION MEMORY (v2.0) ===
    messages: Annotated[list[AnyMessage], add_messages]
    """
    Vollständiger Chatverlauf mit automatischem Merging.
    
    Der add_messages Reducer (Buch S. 74):
    - Fügt neue Messages zur bestehenden Liste hinzu
    - Verhindert Duplikate durch Message-IDs
    - Ermöglicht sowohl einzelne Messages als auch Listen
    
    Beispiel:
        state["messages"] = [HumanMessage(content="Wie heiße ich?")]
        -> Wird automatisch zu bestehenden Messages hinzugefügt
    """
    
    # === RETRIEVAL ===
    retrieved_docs: Optional[List[Document]]
    """Abgerufene Dokumente aus ChromaDB (nach retrieve-Node)."""
    
    # === KONTEXT-FORMATIERUNG ===
    context: Optional[str]
    """Formatierter Kontext-String für LLM (nach format_context-Node)."""
    
    sources: Optional[List[str]]
    """Quellenreferenzen z.B. ['UStG § 12 Abs. 1']."""
    
    # === GENERIERUNG ===
    answer: Optional[str]
    """Generierte Antwort (nach generate-Node)."""
    
    # === ERROR HANDLING ===
    error: Optional[str]
    """Fehlermeldung falls ein Node fehlschlägt."""


# =============================================================================
# INITIAL STATE FACTORY (v2.0)
# =============================================================================

def create_initial_state(query: str) -> RAGState:
    """
    Erstellt einen initialen State für den Workflow mit erster Message.
    
    Args:
        query: Die Benutzerfrage
        
    Returns:
        RAGState: Initialisierter State mit query und HumanMessage
        
    Beispiel:
        state = create_initial_state("Wie hoch ist der Umsatzsteuersatz?")
        # state["messages"] enthält jetzt [HumanMessage(content="...")]
    """
    return RAGState(
        query=query,
        messages=[HumanMessage(content=query)],  # NEU: Erste Message
        retrieved_docs=None,
        context=None,
        sources=None,
        answer=None,
        error=None,
    )


# =============================================================================
# STATE HELPER FUNCTIONS
# =============================================================================

def add_ai_response_to_state(state: RAGState, response: str) -> dict:
    """
    Fügt eine AI-Antwort zum State hinzu.
    
    Args:
        state: Der aktuelle State
        response: Die generierte Antwort
        
    Returns:
        dict: State-Update mit neuer AIMessage
        
    Hinweis:
        Der add_messages Reducer fügt die AIMessage automatisch
        zur bestehenden messages-Liste hinzu.
    """
    return {
        "answer": response,
        "messages": [AIMessage(content=response)]
    }


def get_conversation_history(state: RAGState) -> str:
    """
    Extrahiert den Chatverlauf als formatierten String.
    
    Args:
        state: Der State mit messages
        
    Returns:
        str: Formatierter Chatverlauf für Debugging/Logging
    """
    messages = state.get("messages", [])
    if not messages:
        return "Keine vorherigen Nachrichten."
    
    history = []
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Assistent"
        content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        history.append(f"{role}: {content}")
    
    return "\n".join(history)


def validate_state(state: RAGState) -> bool:
    """
    Validiert ob der State die Mindestanforderungen erfüllt.
    
    Args:
        state: Der zu validierende State
        
    Returns:
        bool: True wenn State valide ist
        
    Raises:
        ValueError: Wenn query fehlt oder leer ist
    """
    if "query" not in state or not state.get("query"):
        raise ValueError("State muss ein 'query'-Feld mit Inhalt haben.")
    return True


def has_error(state: RAGState) -> bool:
    """Prüft ob der State einen Fehler enthält."""
    return state.get("error") is not None


def is_complete(state: RAGState) -> bool:
    """Prüft ob der Workflow vollständig abgeschlossen ist."""
    return (
        state.get("answer") is not None 
        and state.get("error") is None
    )


def get_message_count(state: RAGState) -> int:
    """Gibt die Anzahl der Messages im Chatverlauf zurück."""
    return len(state.get("messages", []))


# =============================================================================
# STATE INFO
# =============================================================================

def get_state_info() -> dict:
    """
    Gibt Informationen über das State-Schema zurück.
    
    Returns:
        dict: Schema-Details für Dokumentation/Debugging
    """
    return {
        "schema_name": "RAGState",
        "version": "2.0",
        "fields": [
            {"name": "query", "type": "str", "required": True, 
             "description": "Aktuelle Benutzerfrage"},
            {"name": "messages", "type": "Annotated[list[AnyMessage], add_messages]", 
             "required": False, "description": "NEU: Chatverlauf mit Reducer"},
            {"name": "retrieved_docs", "type": "List[Document]", 
             "required": False, "description": "Abgerufene Dokumente"},
            {"name": "context", "type": "str", 
             "required": False, "description": "Formatierter Kontext"},
            {"name": "sources", "type": "List[str]", 
             "required": False, "description": "Quellenreferenzen"},
            {"name": "answer", "type": "str", 
             "required": False, "description": "Generierte Antwort"},
            {"name": "error", "type": "str", 
             "required": False, "description": "Fehlermeldung"},
        ],
        "memory_enabled": True,
        "reducer": "add_messages",
        "source": "Buch S. 74-75, 97-103; LangGraph Docs",
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("STATE-SCHEMA TEST (v2.0 mit Memory)")
    print("=" * 60)
    print()
    
    # Info ausgeben
    print("SCHEMA-INFO:")
    info = get_state_info()
    print(f"  Name: {info['schema_name']}")
    print(f"  Version: {info['version']}")
    print(f"  Memory: {'Aktiviert' if info['memory_enabled'] else 'Deaktiviert'}")
    print(f"  Reducer: {info['reducer']}")
    print()
    
    print("FELDER:")
    for field in info["fields"]:
        req = "REQUIRED" if field["required"] else "optional"
        print(f"  {field['name']:20s} [{req}]")
        print(f"    -> {field['description']}")
    print()
    
    # Test: Initial State erstellen
    print("TEST: Initial State mit Message erstellen...")
    test_query = "Wie hoch ist der Umsatzsteuersatz?"
    state = create_initial_state(test_query)
    
    print(f"  query: '{state['query']}'")
    print(f"  messages: {len(state.get('messages', []))} Message(s)")
    if state.get('messages'):
        print(f"    -> Typ: {type(state['messages'][0]).__name__}")
        print(f"    -> Inhalt: {state['messages'][0].content[:50]}...")
    print()
    
    # Test: AI-Response hinzufügen
    print("TEST: AI-Response zum State hinzufügen...")
    update = add_ai_response_to_state(state, "Der Umsatzsteuersatz beträgt 19%.")
    print(f"  Neue AIMessage: {update['messages'][0].content[:50]}...")
    print()
    
    # Test: Conversation History
    print("TEST: Conversation History formatieren...")
    # Simuliere vollständigen State
    full_state = {
        **state,
        "messages": state["messages"] + update["messages"]
    }
    history = get_conversation_history(full_state)
    print(history)
    print()
    
    print("=" * 60)
    print("[OK] State-Schema v2.0 funktioniert!")
    print("=" * 60)
