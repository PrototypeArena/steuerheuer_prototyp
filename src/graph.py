"""
LangGraph RAG-Workflow fuer das Steuerheuer-System.
=====================================================

Dieses Modul kompiliert den vollstaendigen RAG-Workflow als
LangGraph StateGraph mit allen Nodes und Edges.

Aufgabe: 6.3 - Graph kompilieren und testen

Quellen:
- Buch S. 70-71: "A graph instance itself is a Runnable 
  (to be precise, it inherits from Runnable) and we can execute it."
- LangGraph Docs: "StateGraph is a builder class and cannot be 
  used directly for execution. You must first call .compile()."
- Aufgabenliste S. 856-890

Workflow-Ablauf:
    START -> retrieve -> format_context -> generate -> END

Verwendung:
    from src.graph import create_rag_graph, ask_graph
    
    # Option 1: Graph direkt verwenden
    graph = create_rag_graph()
    result = graph.invoke({"query": "Wie hoch ist der Umsatzsteuersatz?"})
    
    # Option 2: Convenience-Funktion
    result = ask_graph("Was ist die Kleinunternehmerregelung?")
"""

from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from src.state import RAGState, create_initial_state, is_complete, has_error
from src.nodes import retrieve_node, format_context_node, generate_node


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def create_rag_graph():
    """
    Erstellt und kompiliert den RAG-Workflow-Graph.
    
    Der Graph verbindet die drei Nodes in sequentieller Reihenfolge:
    1. retrieve: Holt Dokumente aus ChromaDB
    2. format_context: Formatiert Dokumente als Kontext
    3. generate: Generiert LLM-Antwort
    
    Returns:
        CompiledStateGraph: Der kompilierte, ausfuehrbare Graph
        
    Beispiel:
        graph = create_rag_graph()
        result = graph.invoke({"query": "Wie hoch ist der Umsatzsteuersatz?"})
        print(result["answer"])
        
    Quellen:
        - Buch S. 70: "add_node is a convenient way to add a component"
        - LangGraph Docs: StateGraph.compile()
    """
    # =================================================================
    # SCHRITT 1: StateGraph mit Schema initialisieren
    # =================================================================
    # Quelle: Buch S. 69 - "You initialize this class by passing 
    #         in a state definition."
    builder = StateGraph(RAGState)
    
    # =================================================================
    # SCHRITT 2: Nodes hinzufuegen
    # =================================================================
    # Quelle: Buch S. 70 - "graph.add_node(name, value) syntax"
    # Die Nodes sind in src/nodes.py definiert
    
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("format_context", format_context_node)
    builder.add_node("generate", generate_node)
    
    # =================================================================
    # SCHRITT 3: Edges definieren (Workflow-Ablauf)
    # =================================================================
    # Quelle: LangGraph Docs - "add_edge(start_key, end_key)"
    # Linearer Workflow: START -> retrieve -> format_context -> generate -> END
    
    # Entry Point: START -> retrieve
    builder.add_edge(START, "retrieve")
    
    # Sequentielle Edges
    builder.add_edge("retrieve", "format_context")
    builder.add_edge("format_context", "generate")
    
    # Exit Point: generate -> END
    builder.add_edge("generate", END)
    
    # =================================================================
    # SCHRITT 4: Graph kompilieren
    # =================================================================
    # Quelle: LangGraph Docs - "You must first call .compile() to 
    #         create an executable graph"
    
    compiled_graph = builder.compile()
    
    return compiled_graph


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def ask_graph(question: str) -> Dict[str, Any]:
    """
    Stellt eine Frage an den RAG-Graph und gibt das Ergebnis zurueck.
    
    Args:
        question: Die Benutzerfrage in natuerlicher Sprache
        
    Returns:
        dict: Der finale State mit allen Feldern:
            - query: Die urspruengliche Frage
            - retrieved_docs: Abgerufene Dokumente
            - context: Formatierter Kontext
            - sources: Quellenreferenzen
            - answer: Generierte Antwort
            - error: Fehlermeldung (falls vorhanden)
            
    Beispiel:
        result = ask_graph("Was ist der Vorsteuerabzug?")
        print(f"Antwort: {result['answer']}")
        print(f"Quellen: {result['sources']}")
    """
    graph = create_rag_graph()
    
    # Initial State erstellen
    initial_state = {"query": question}
    
    # Graph ausfuehren
    result = graph.invoke(initial_state)
    
    return result


def ask_graph_simple(question: str) -> str:
    """
    Einfache Funktion die nur die Antwort zurueckgibt.
    
    Args:
        question: Die Benutzerfrage
        
    Returns:
        str: Die generierte Antwort oder Fehlermeldung
        
    Beispiel:
        antwort = ask_graph_simple("Wie hoch ist der Umsatzsteuersatz?")
        print(antwort)
    """
    result = ask_graph(question)
    
    if result.get("error"):
        return f"Fehler: {result['error']}"
    
    return result.get("answer", "Keine Antwort generiert.")


# =============================================================================
# GRAPH INFO
# =============================================================================

def get_graph_info() -> dict:
    """
    Gibt Informationen ueber den Graph zurueck.
    
    Returns:
        dict: Graph-Details fuer Dokumentation/Debugging
    """
    return {
        "name": "Steuerheuer RAG Graph",
        "nodes": ["retrieve", "format_context", "generate"],
        "edges": [
            ("START", "retrieve"),
            ("retrieve", "format_context"),
            ("format_context", "generate"),
            ("generate", "END"),
        ],
        "state_schema": "RAGState",
        "workflow": "START -> retrieve -> format_context -> generate -> END",
        "source": "Aufgabenliste S. 856-890, Buch S. 70-71",
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LANGGRAPH RAG-WORKFLOW TEST (Aufgabe 6.3)")
    print("=" * 70)
    print()
    
    # Graph-Info ausgeben
    print("GRAPH-INFO:")
    info = get_graph_info()
    print(f"  Name: {info['name']}")
    print(f"  Workflow: {info['workflow']}")
    print(f"  Nodes: {info['nodes']}")
    print()
    
    # Graph erstellen
    print("SCHRITT 1: Graph erstellen...")
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
    
    # Test-Frage
    test_question = "Wie hoch ist der Umsatzsteuersatz in Deutschland?"
    print(f"SCHRITT 2: Test-Frage ausfuehren...")
    print(f"  Frage: \"{test_question}\"")
    print()
    
    print("SCHRITT 3: Graph.invoke() ausfuehren...")
    print("-" * 70)
    
    try:
        # Graph ausfuehren
        result = graph.invoke({"query": test_question})
        
        # Ergebnis analysieren
        print()
        print("ERGEBNIS:")
        print("-" * 70)
        print()
        
        # State-Felder anzeigen
        print(f"  query: '{result.get('query', '')[:50]}...'")
        print(f"  retrieved_docs: {len(result.get('retrieved_docs', []))} Dokumente")
        print(f"  context: {len(result.get('context', ''))} Zeichen")
        print(f"  sources: {result.get('sources', [])}")
        print(f"  answer: {len(result.get('answer', ''))} Zeichen")
        print(f"  error: {result.get('error')}")
        print()
        
        # Vollstaendigkeit pruefen
        print("STATUS:")
        print(f"  has_error: {has_error(result)}")
        print(f"  is_complete: {is_complete(result)}")
        print()
        
        # Antwort anzeigen
        print("GENERIERTE ANTWORT:")
        print("-" * 70)
        answer = result.get("answer", "")
        # Antwort auf 800 Zeichen begrenzen fuer Ausgabe
        if len(answer) > 800:
            print(answer[:800] + "...")
        else:
            print(answer)
        print()
        
        # Quellen anzeigen
        print("QUELLEN:")
        for src in result.get("sources", []):
            print(f"  - {src}")
        print()
        
        print("=" * 70)
        if is_complete(result):
            print("[OK] LangGraph RAG-Workflow funktioniert!")
        else:
            print("[!] Workflow nicht vollstaendig abgeschlossen")
        print("=" * 70)
        
    except Exception as e:
        print(f"[FEHLER] {e}")
        import traceback
        traceback.print_exc()
