"""
State-Schema fuer den Steuerheuer RAG-Workflow mit LangGraph.
==============================================================

Dieses Modul definiert das zentrale State-Schema, das alle
Informationen zwischen Workflow-Nodes transportiert.

Aufgabe: 6.1 - State-Schema definieren

Quellen:
- Buch S. 69-70: "For simplicity, think about a state as a Python 
  dictionary. Nodes are Python functions that operate on this 
  dictionary."
- Aufgabenliste S. 777-810
- LangGraph Docs: "A StateGraph accepts a state_schema argument 
  on initialization that specifies the 'shape' of the state."

Architektur-Entscheidung:
- Option B gewaehlt: Erweiterter State mit Optional und Error-Handling
- Ermoeglicht robuste Fehlerbehandlung und bedingte Edges
"""

from typing import List, Optional
from typing_extensions import TypedDict

from langchain_core.documents import Document


# =============================================================================
# RAG WORKFLOW STATE SCHEMA
# =============================================================================

class RAGState(TypedDict, total=False):
    """
    Zentrales State-Schema fuer den RAG-Workflow.
    
    Dieses TypedDict definiert alle Felder, die zwischen den
    Workflow-Nodes (retrieve, format_context, generate) 
    transportiert werden.
    
    Attribute:
        query (str): 
            Die Benutzerfrage in natuerlicher Sprache.
            Wird zu Beginn des Workflows gesetzt und bleibt unveraendert.
            
        retrieved_docs (Optional[List[Document]]): 
            Liste der aus ChromaDB abgerufenen Dokumente.
            Wird vom 'retrieve'-Node gesetzt.
            None wenn Retrieval fehlschlaegt oder noch nicht ausgefuehrt.
            
        context (Optional[str]): 
            Formatierter Kontext-String fuer das LLM.
            Wird vom 'format_context'-Node aus retrieved_docs erstellt.
            Enthaelt Quellenreferenzen im Format [UStG § X Abs. Y].
            
        answer (Optional[str]): 
            Die generierte Antwort des LLM.
            Wird vom 'generate'-Node gesetzt.
            None wenn Generation fehlschlaegt oder noch nicht ausgefuehrt.
            
        sources (Optional[List[str]]): 
            Liste der Quellenreferenzen (z.B. ["UStG § 12 Abs. 1"]).
            Wird parallel zur Antwort extrahiert.
            
        error (Optional[str]): 
            Fehlermeldung falls ein Node fehlschlaegt.
            Ermoeglicht bedingte Edges und Fehlerbehandlung.
            None wenn kein Fehler aufgetreten ist.
    
    Workflow-Datenfluss:
        START -> retrieve(query) -> retrieved_docs
              -> format_context(retrieved_docs) -> context, sources
              -> generate(query, context) -> answer
              -> END
    
    Beispiel:
        state: RAGState = {
            "query": "Wie hoch ist der Umsatzsteuersatz?",
            "retrieved_docs": [Document(...), Document(...)],
            "context": "[UStG § 12 Abs. 1]\\n(1) Die Steuer...",
            "sources": ["UStG § 12 Abs. 1", "UStG § 12 Abs. 2"],
            "answer": "Der Umsatzsteuersatz betraegt 19%...",
            "error": None
        }
        
    Hinweis:
        total=False bedeutet, dass alle Felder optional sind.
        Dies ist wichtig, weil nicht alle Felder zu jedem Zeitpunkt
        im Workflow gesetzt sind.
        
    Quelle: Buch S. 69-70 - State as Python Dictionary
    """
    
    # === EINGABE ===
    query: str
    """Die Benutzerfrage (Pflichtfeld bei Start)."""
    
    # === RETRIEVAL ===
    retrieved_docs: Optional[List[Document]]
    """Abgerufene Dokumente aus ChromaDB (nach retrieve-Node)."""
    
    # === KONTEXT-FORMATIERUNG ===
    context: Optional[str]
    """Formatierter Kontext-String fuer LLM (nach format_context-Node)."""
    
    sources: Optional[List[str]]
    """Quellenreferenzen z.B. ['UStG § 12 Abs. 1'] (nach format_context-Node)."""
    
    # === GENERIERUNG ===
    answer: Optional[str]
    """Generierte Antwort (nach generate-Node)."""
    
    # === ERROR HANDLING ===
    error: Optional[str]
    """Fehlermeldung falls ein Node fehlschlaegt."""


# =============================================================================
# INITIAL STATE FACTORY
# =============================================================================

def create_initial_state(query: str) -> RAGState:
    """
    Erstellt einen initialen State fuer den Workflow.
    
    Args:
        query: Die Benutzerfrage
        
    Returns:
        RAGState: Initialisierter State mit query und None-Werten
        
    Beispiel:
        state = create_initial_state("Wie hoch ist der Umsatzsteuersatz?")
        result = graph.invoke(state)
    """
    return RAGState(
        query=query,
        retrieved_docs=None,
        context=None,
        sources=None,
        answer=None,
        error=None,
    )


# =============================================================================
# STATE VALIDATION
# =============================================================================

def validate_state(state: RAGState) -> bool:
    """
    Validiert ob der State die Mindestanforderungen erfuellt.
    
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
    """
    Prueft ob der State einen Fehler enthaelt.
    
    Args:
        state: Der zu pruefende State
        
    Returns:
        bool: True wenn error-Feld gesetzt ist
        
    Hinweis:
        Kann fuer bedingte Edges verwendet werden.
    """
    return state.get("error") is not None


def is_complete(state: RAGState) -> bool:
    """
    Prueft ob der Workflow vollstaendig abgeschlossen ist.
    
    Args:
        state: Der zu pruefende State
        
    Returns:
        bool: True wenn answer gesetzt und kein Fehler vorhanden
    """
    return (
        state.get("answer") is not None 
        and state.get("error") is None
    )


# =============================================================================
# STATE INFO
# =============================================================================

def get_state_info() -> dict:
    """
    Gibt Informationen ueber das State-Schema zurueck.
    
    Returns:
        dict: Schema-Details fuer Dokumentation/Debugging
    """
    return {
        "schema_name": "RAGState",
        "fields": [
            {"name": "query", "type": "str", "required": True, "description": "Benutzerfrage"},
            {"name": "retrieved_docs", "type": "List[Document]", "required": False, "description": "Abgerufene Dokumente"},
            {"name": "context", "type": "str", "required": False, "description": "Formatierter Kontext"},
            {"name": "sources", "type": "List[str]", "required": False, "description": "Quellenreferenzen"},
            {"name": "answer", "type": "str", "required": False, "description": "Generierte Antwort"},
            {"name": "error", "type": "str", "required": False, "description": "Fehlermeldung"},
        ],
        "total": False,  # Alle Felder optional (ausser query bei Start)
        "source": "Aufgabenliste S. 777-810, Buch S. 69-70",
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("STATE-SCHEMA TEST (Aufgabe 6.1)")
    print("=" * 60)
    print()
    
    # Info ausgeben
    print("SCHEMA-INFO:")
    info = get_state_info()
    print(f"  Name: {info['schema_name']}")
    print(f"  total=False: Alle Felder optional")
    print()
    
    print("FELDER:")
    for field in info["fields"]:
        req = "REQUIRED" if field["required"] else "optional"
        print(f"  {field['name']:20s} {field['type']:20s} [{req}]")
    print()
    
    # Test: Initial State erstellen
    print("TEST: Initial State erstellen...")
    test_query = "Wie hoch ist der Umsatzsteuersatz?"
    state = create_initial_state(test_query)
    
    print(f"  query: '{state['query']}'")
    print(f"  retrieved_docs: {state['retrieved_docs']}")
    print(f"  context: {state['context']}")
    print(f"  answer: {state['answer']}")
    print(f"  error: {state['error']}")
    print()
    
    # Test: Validierung
    print("TEST: State-Validierung...")
    try:
        validate_state(state)
        print("  [OK] State ist valide")
    except ValueError as e:
        print(f"  [FEHLER] {e}")
    print()
    
    # Test: Error-Check
    print("TEST: Error-Check...")
    print(f"  has_error: {has_error(state)}")
    print(f"  is_complete: {is_complete(state)}")
    print()
    
    # Simuliere kompletten State
    print("TEST: Simuliere kompletten Workflow-State...")
    complete_state: RAGState = {
        "query": test_query,
        "retrieved_docs": [],  # Wuerde normalerweise Document-Objekte enthalten
        "context": "[UStG § 12 Abs. 1]\n(1) Die Steuer betraegt...",
        "sources": ["UStG § 12 Abs. 1"],
        "answer": "Der Umsatzsteuersatz betraegt 19 Prozent.",
        "error": None,
    }
    print(f"  has_error: {has_error(complete_state)}")
    print(f"  is_complete: {is_complete(complete_state)}")
    print()
    
    print("=" * 60)
    print("[OK] State-Schema funktioniert!")
    print("=" * 60)
