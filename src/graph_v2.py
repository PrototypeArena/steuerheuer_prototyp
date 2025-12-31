"""
LangGraph RAG-Workflow für das Steuerheuer-System.
=====================================================

VERSION 2.0 - MIT KONVERSATIONSGEDÄCHTNIS

Änderungen gegenüber v1:
- MemorySaver Checkpointer für Persistenz
- thread_id Support für Session-Management
- Message-History-Integration

Quellen:
- Buch S. 70-71: "A graph instance itself is a Runnable"
- Buch S. 101-103: "LangGraph checkpoints"
- LangGraph Docs: "If you provide a checkpointer when compiling the graph 
  and a thread_id when calling your graph, LangGraph automatically saves 
  the state after each step."

Workflow-Ablauf:
    START -> retrieve -> format_context -> generate -> END
    
    Mit Checkpointer:
    - State wird nach jedem Schritt gespeichert
    - Bei gleichem thread_id wird vorheriger State geladen
    - Ermöglicht Multi-Turn-Konversationen
"""

from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Importiere das NEUE State-Schema mit messages
from src.state_v2 import (
    RAGState, 
    create_initial_state, 
    is_complete, 
    has_error,
    get_message_count
)
from src.nodes_v2 import retrieve_node, format_context_node, generate_node


# =============================================================================
# CHECKPOINTER SINGLETON
# =============================================================================

_checkpointer: Optional[MemorySaver] = None

def get_checkpointer() -> MemorySaver:
    """
    Gibt den globalen Checkpointer zurück (Singleton-Pattern).
    
    Der Checkpointer muss global sein, damit:
    1. Alle Aufrufe denselben Speicher nutzen
    2. Thread-übergreifende Persistenz funktioniert
    3. Kein neuer Checkpointer bei jedem Graph-Aufruf erstellt wird
    
    Returns:
        MemorySaver: Der globale In-Memory Checkpointer
        
    Hinweis für Produktion (Buch S. 103):
        Für Produktionssysteme sollte SqliteSaver oder PostgresSaver
        verwendet werden statt MemorySaver.
        
    Quelle: Buch S. 101-102 - MemorySaver
    """
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
        print("[INFO] MemorySaver Checkpointer initialisiert")
    return _checkpointer


def reset_checkpointer():
    """
    Setzt den Checkpointer zurück (für Tests).
    
    Achtung: Löscht alle gespeicherten Threads/Konversationen!
    """
    global _checkpointer
    _checkpointer = None


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def create_rag_graph():
    """
    Erstellt und kompiliert den RAG-Workflow-Graph MIT Checkpointer.
    
    Der Graph verbindet die drei Nodes in sequentieller Reihenfolge:
    1. retrieve: Holt Dokumente aus ChromaDB
    2. format_context: Formatiert Dokumente als Kontext
    3. generate: Generiert LLM-Antwort (inkl. Message-History)
    
    KRITISCHE ÄNDERUNG (v2.0):
    Der Graph wird mit checkpointer=memory kompiliert, wodurch:
    - State nach jedem Schritt gespeichert wird
    - Thread-basierte Konversationen möglich sind
    - Memory zwischen Aufrufen erhalten bleibt
    
    Returns:
        CompiledStateGraph: Der kompilierte, ausfuehrbare Graph
        
    Beispiel:
        graph = create_rag_graph()
        config = {"configurable": {"thread_id": "session-123"}}
        result = graph.invoke({"query": "Hallo"}, config=config)
        
    Quellen:
        - Buch S. 101-102: "builder.compile(checkpointer=memory)"
        - LangGraph Docs: "graph = builder.compile(checkpointer=checkpointer)"
    """
    # =================================================================
    # SCHRITT 1: StateGraph mit Schema initialisieren
    # =================================================================
    builder = StateGraph(RAGState)
    
    # =================================================================
    # SCHRITT 2: Nodes hinzufügen
    # =================================================================
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("format_context", format_context_node)
    builder.add_node("generate", generate_node)
    
    # =================================================================
    # SCHRITT 3: Edges definieren (Workflow-Ablauf)
    # =================================================================
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "format_context")
    builder.add_edge("format_context", "generate")
    builder.add_edge("generate", END)
    
    # =================================================================
    # SCHRITT 4: Graph MIT CHECKPOINTER kompilieren
    # =================================================================
    # KRITISCHE ÄNDERUNG: checkpointer=memory hinzugefügt!
    # 
    # Quelle (Buch S. 101-102):
    # "We initiate a MemorySaver that will keep checkpoints in local 
    #  memory and pass it to the graph during compilation"
    
    checkpointer = get_checkpointer()
    compiled_graph = builder.compile(checkpointer=checkpointer)
    
    return compiled_graph


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def ask_graph(
    question: str, 
    thread_id: str = "default"
) -> Dict[str, Any]:
    """
    Stellt eine Frage an den RAG-Graph MIT Konversationsgedächtnis.
    
    Args:
        question: Die Benutzerfrage in natürlicher Sprache
        thread_id: Eindeutige Session-/Konversations-ID.
                   Gleiche thread_id = gleiche Konversation.
                   
    Returns:
        dict: Der finale State mit allen Feldern:
            - query: Die ursprüngliche Frage
            - messages: Der vollständige Chatverlauf
            - retrieved_docs: Abgerufene Dokumente
            - context: Formatierter Kontext
            - sources: Quellenreferenzen
            - answer: Generierte Antwort
            - error: Fehlermeldung (falls vorhanden)
            
    Beispiel:
        # Erste Frage in neuer Session
        result1 = ask_graph("Mein Name ist Fawzi", thread_id="user-123")
        
        # Zweite Frage in GLEICHER Session (Memory!)
        result2 = ask_graph("Wie heiße ich?", thread_id="user-123")
        # -> result2['answer'] wird "Fawzi" enthalten!
        
    Quelle: Buch S. 102 - "config={'configurable': {'thread_id': ...}}"
    """
    from langchain_core.messages import HumanMessage
    
    graph = create_rag_graph()
    
    # =================================================================
    # KRITISCHE KONFIGURATION: thread_id für Checkpointer
    # =================================================================
    # Quelle (Buch S. 102):
    # "Each time we invoke the graph, we should provide either a 
    #  specific checkpoint or a thread-id (a unique identifier of 
    #  each run)."
    
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # =================================================================
    # Initial State mit User-Message
    # =================================================================
    # Die HumanMessage wird durch den add_messages Reducer
    # automatisch zur bestehenden History hinzugefügt
    
    initial_state = {
        "query": question,
        "messages": [HumanMessage(content=question)]
    }
    
    # =================================================================
    # Graph mit Konfiguration ausführen
    # =================================================================
    result = graph.invoke(initial_state, config=config)
    
    return result


def ask_graph_simple(question: str, thread_id: str = "default") -> str:
    """
    Einfache Funktion die nur die Antwort zurückgibt.
    
    Args:
        question: Die Benutzerfrage
        thread_id: Session-ID
        
    Returns:
        str: Die generierte Antwort oder Fehlermeldung
    """
    result = ask_graph(question, thread_id)
    
    if result.get("error"):
        return f"Fehler: {result['error']}"
    
    return result.get("answer", "Keine Antwort generiert.")


def get_conversation_state(thread_id: str) -> Optional[Dict[str, Any]]:
    """
    Ruft den aktuellen State einer Konversation ab.
    
    Args:
        thread_id: Die Thread-/Session-ID
        
    Returns:
        dict: Der gespeicherte State oder None
        
    Beispiel:
        state = get_conversation_state("user-123")
        print(f"Nachrichten: {len(state.get('messages', []))}")
    """
    checkpointer = get_checkpointer()
    config = {"configurable": {"thread_id": thread_id}}
    
    # Letzten Checkpoint abrufen
    checkpoint = checkpointer.get(config)
    
    if checkpoint:
        return checkpoint.get("channel_values", {})
    return None


def list_all_threads() -> list:
    """
    Listet alle aktiven Thread-IDs auf.
    
    Returns:
        list: Liste aller Thread-IDs
    """
    checkpointer = get_checkpointer()
    
    # Alle Checkpoints durchgehen
    threads = set()
    for checkpoint in checkpointer.list(None):
        thread_id = checkpoint.config.get("configurable", {}).get("thread_id")
        if thread_id:
            threads.add(thread_id)
    
    return list(threads)


# =============================================================================
# GRAPH INFO
# =============================================================================

def get_graph_info() -> dict:
    """
    Gibt Informationen über den Graph zurück.
    
    Returns:
        dict: Graph-Details für Dokumentation/Debugging
    """
    return {
        "name": "Steuerheuer RAG Graph",
        "version": "2.0",
        "memory_enabled": True,
        "checkpointer": "MemorySaver",
        "nodes": ["retrieve", "format_context", "generate"],
        "edges": [
            ("START", "retrieve"),
            ("retrieve", "format_context"),
            ("format_context", "generate"),
            ("generate", "END"),
        ],
        "state_schema": "RAGState v2.0 (mit messages)",
        "workflow": "START -> retrieve -> format_context -> generate -> END",
        "source": "Buch S. 70-71, 101-103; LangGraph Docs",
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LANGGRAPH RAG-WORKFLOW TEST (v2.0 mit Memory)")
    print("=" * 70)
    print()
    
    # Graph-Info ausgeben
    print("GRAPH-INFO:")
    info = get_graph_info()
    print(f"  Name: {info['name']}")
    print(f"  Version: {info['version']}")
    print(f"  Memory: {'Aktiviert' if info['memory_enabled'] else 'Deaktiviert'}")
    print(f"  Checkpointer: {info['checkpointer']}")
    print(f"  Workflow: {info['workflow']}")
    print()
    
    # Graph erstellen
    print("SCHRITT 1: Graph mit Checkpointer erstellen...")
    try:
        graph = create_rag_graph()
        print(f"  [OK] Graph kompiliert")
        print(f"  Typ: {type(graph).__name__}")
    except Exception as e:
        print(f"  [FEHLER] {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    print()
    
    # Test: Memory-Funktionalität
    print("SCHRITT 2: Memory-Test durchführen...")
    print("-" * 70)
    
    test_thread_id = "test-memory-session"
    
    # Erste Frage
    print()
    print(f"  Frage 1: 'Mein Name ist TestUser'")
    print(f"  Thread-ID: {test_thread_id}")
    
    try:
        result1 = ask_graph("Mein Name ist TestUser", thread_id=test_thread_id)
        print(f"  [OK] Antwort erhalten")
        print(f"  Messages: {get_message_count(result1)}")
        
        # Zweite Frage (sollte sich an Namen erinnern!)
        print()
        print(f"  Frage 2: 'Wie heiße ich?' (MEMORY-TEST)")
        print(f"  Thread-ID: {test_thread_id} (gleich!)")
        
        result2 = ask_graph("Wie heiße ich?", thread_id=test_thread_id)
        print(f"  [OK] Antwort erhalten")
        print(f"  Messages: {get_message_count(result2)}")
        
        print()
        print("-" * 70)
        print("ERGEBNIS:")
        print("-" * 70)
        print()
        
        print(f"Antwort auf 'Wie heiße ich?':")
        print(result2.get("answer", "Keine Antwort")[:500])
        print()
        
        # Prüfe ob Memory funktioniert
        if "TestUser" in result2.get("answer", ""):
            print("=" * 70)
            print("[OK] MEMORY FUNKTIONIERT! Name wurde gemerkt!")
            print("=" * 70)
        else:
            print("=" * 70)
            print("[!] Memory-Test nicht eindeutig")
            print("    (LLM-Antwort enthält nicht 'TestUser')")
            print("=" * 70)
        
    except Exception as e:
        print(f"  [FEHLER] {e}")
        import traceback
        traceback.print_exc()
    
    # Aufräumen
    print()
    print("SCHRITT 3: Checkpointer zurücksetzen...")
    reset_checkpointer()
    print("  [OK] Checkpointer zurückgesetzt")
