"""
Workflow-Nodes fuer den Steuerheuer RAG-Workflow mit LangGraph.
================================================================

Dieses Modul implementiert die einzelnen Workflow-Schritte als
Python-Funktionen (Nodes), die auf dem RAGState operieren.

Aufgabe: 6.2 - Workflow-Nodes implementieren

Quellen:
- Buch S. 70: "add_node is a convenient way to add a component 
  to your graph by providing its name and a corresponding 
  Python function."
- Buch S. 69-70: "Nodes are Python functions that operate on 
  this dictionary."
- Aufgabenliste S. 814-852

Workflow-Ablauf:
    START -> retrieve -> format_context -> generate -> END

Node-Signaturen (LangGraph-Konvention):
    def node_name(state: RAGState) -> dict:
        # Verarbeite state
        return {"field_to_update": new_value}
"""

from typing import Dict, Any, List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from src.state import RAGState
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
        - error (str): Fehlermeldung falls Retrieval fehlschlaegt
    
    Beispiel:
        state = {"query": "Wie hoch ist der Umsatzsteuersatz?"}
        result = retrieve_node(state)
        # result = {"retrieved_docs": [Document(...), ...]}
        
    Quelle: Buch S. 70 - Node als Python-Funktion
    """
    try:
        # Query aus State extrahieren
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
            "error": None  # Kein Fehler
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
    Kontext-Formatierungs-Node: Bereitet Dokumente fuer das LLM auf.
    
    Input aus State:
        - retrieved_docs (List[Document]): Abgerufene Dokumente
        
    Output (State-Update):
        - context (str): Formatierter Kontext-String
        - sources (List[str]): Liste der Quellenreferenzen
        - error (str): Fehlermeldung falls Formatierung fehlschlaegt
    
    Beispiel:
        state = {"retrieved_docs": [Document(...)]}
        result = format_context_node(state)
        # result = {
        #     "context": "[UStG § 12 Abs. 1]\n(1) Die Steuer...",
        #     "sources": ["UStG § 12 Abs. 1"]
        # }
        
    Quelle: Aufgabenliste S. 821-825 - format_context Node
    """
    try:
        # Dokumente aus State extrahieren
        docs = state.get("retrieved_docs", [])
        
        # Pruefen ob Dokumente vorhanden
        if not docs:
            return {
                "context": "Keine relevanten Gesetzesauszuege gefunden.",
                "sources": [],
                "error": None  # Kein kritischer Fehler
            }
        
        # Kontext formatieren (nutzt bestehende Funktion)
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
# NODE 3: GENERATE
# =============================================================================

def generate_node(state: RAGState) -> Dict[str, Any]:
    """
    Generierungs-Node: Erzeugt die LLM-Antwort.
    
    Input aus State:
        - query (str): Die Benutzerfrage
        - context (str): Der formatierte Kontext
        
    Output (State-Update):
        - answer (str): Die generierte Antwort
        - error (str): Fehlermeldung falls Generation fehlschlaegt
    
    Beispiel:
        state = {
            "query": "Wie hoch ist der Umsatzsteuersatz?",
            "context": "[UStG § 12 Abs. 1]\n(1) Die Steuer..."
        }
        result = generate_node(state)
        # result = {"answer": "Der Umsatzsteuersatz betraegt 19%..."}
        
    Quelle: Buch S. 70 - Node als Python-Funktion
    """
    try:
        # Daten aus State extrahieren
        query = state.get("query", "")
        context = state.get("context", "")
        
        # Pruefen auf Error im vorherigen Schritt
        if state.get("error"):
            return {
                "answer": f"Fehler im Workflow: {state.get('error')}",
                "error": state.get("error")
            }
        
        # Pruefen ob Query vorhanden
        if not query:
            return {
                "answer": "",
                "error": "Keine Frage (query) fuer Generation vorhanden."
            }
        
        # Prompt erstellen
        prompt = get_rag_prompt()
        
        # LLM initialisieren
        llm = get_llm()
        
        # Prompt mit Kontext und Frage fuellen
        messages = prompt.invoke({
            "context": context,
            "question": query
        })
        
        # LLM aufrufen
        response = llm.invoke(messages)
        
        # Antwort extrahieren
        answer = response.content
        
        return {
            "answer": answer,
            "error": None
        }
        
    except Exception as e:
        return {
            "answer": "",
            "error": f"Generierungs-Fehler: {str(e)}"
        }


# =============================================================================
# NODE-REGISTRY (fuer einfachen Zugriff)
# =============================================================================

# Dictionary mit allen Nodes fuer einfache Registrierung
NODES = {
    "retrieve": retrieve_node,
    "format_context": format_context_node,
    "generate": generate_node,
}


def get_node(name: str):
    """
    Gibt eine Node-Funktion anhand des Namens zurueck.
    
    Args:
        name: Name des Nodes ("retrieve", "format_context", "generate")
        
    Returns:
        Callable: Die Node-Funktion
        
    Raises:
        KeyError: Wenn Node-Name nicht existiert
    """
    if name not in NODES:
        raise KeyError(f"Node '{name}' nicht gefunden. Verfuegbar: {list(NODES.keys())}")
    return NODES[name]


# =============================================================================
# NODE-INFO
# =============================================================================

def get_nodes_info() -> dict:
    """
    Gibt Informationen ueber alle Nodes zurueck.
    
    Returns:
        dict: Node-Details fuer Dokumentation/Debugging
    """
    return {
        "nodes": [
            {
                "name": "retrieve",
                "input": ["query"],
                "output": ["retrieved_docs", "error"],
                "description": "Ruft Dokumente aus ChromaDB ab"
            },
            {
                "name": "format_context",
                "input": ["retrieved_docs"],
                "output": ["context", "sources", "error"],
                "description": "Formatiert Dokumente als Kontext-String"
            },
            {
                "name": "generate",
                "input": ["query", "context"],
                "output": ["answer", "error"],
                "description": "Generiert LLM-Antwort"
            },
        ],
        "workflow": "START -> retrieve -> format_context -> generate -> END",
        "total_nodes": len(NODES),
        "source": "Aufgabenliste S. 814-852, Buch S. 70",
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("WORKFLOW-NODES TEST (Aufgabe 6.2)")
    print("=" * 60)
    print()
    
    # Info ausgeben
    print("NODE-INFO:")
    info = get_nodes_info()
    print(f"  Workflow: {info['workflow']}")
    print(f"  Anzahl Nodes: {info['total_nodes']}")
    print()
    
    for node_info in info["nodes"]:
        print(f"  [{node_info['name']}]")
        print(f"    Input:  {node_info['input']}")
        print(f"    Output: {node_info['output']}")
        print(f"    Beschreibung: {node_info['description']}")
        print()
    
    # Test: Nodes einzeln ausfuehren
    print("-" * 60)
    print("TEST: Nodes einzeln ausfuehren")
    print("-" * 60)
    print()
    
    test_query = "Wie hoch ist der Umsatzsteuersatz?"
    print(f"Test-Frage: \"{test_query}\"")
    print()
    
    try:
        # Node 1: Retrieve
        print("[1/3] retrieve_node...")
        state_1 = {"query": test_query}
        result_1 = retrieve_node(state_1)
        print(f"      retrieved_docs: {len(result_1.get('retrieved_docs', []))} Dokumente")
        print(f"      error: {result_1.get('error')}")
        
        # State aktualisieren
        state_2 = {**state_1, **result_1}
        
        # Node 2: Format Context
        print("[2/3] format_context_node...")
        result_2 = format_context_node(state_2)
        print(f"      context: {len(result_2.get('context', ''))} Zeichen")
        print(f"      sources: {result_2.get('sources', [])[:3]}...")
        print(f"      error: {result_2.get('error')}")
        
        # State aktualisieren
        state_3 = {**state_2, **result_2}
        
        # Node 3: Generate
        print("[3/3] generate_node...")
        result_3 = generate_node(state_3)
        answer = result_3.get('answer', '')
        print(f"      answer: {len(answer)} Zeichen")
        print(f"      error: {result_3.get('error')}")
        
        print()
        print("-" * 60)
        print("ERGEBNIS:")
        print("-" * 60)
        print()
        print(f"QUELLEN: {', '.join(state_3.get('sources', []))}")
        print()
        print("ANTWORT:")
        print(answer[:500] + "..." if len(answer) > 500 else answer)
        print()
        print("=" * 60)
        print("[OK] Alle Nodes funktionieren!")
        print("=" * 60)
        
    except Exception as e:
        print(f"[FEHLER] {e}")
        import traceback
        traceback.print_exc()
