"""
RAG-Chain fuer das Steuerheuer RAG-System.
==========================================

Dieses Modul verbindet alle Komponenten zu einer vollstaendigen
RAG-Pipeline mit LangChain Expression Language (LCEL).

Aufgabe: 5.3 - RAG-Chain zusammenbauen

Quellen:
- Buch S. 42-43: "LCEL is a declarative approach to constructing
  complex LLM workflows. The pipe operator (|) serves as the
  cornerstone of LCEL."
- Buch S. 127: RAG Pipeline Architecture
- Aufgabenliste S. 26-27

Pipeline-Struktur:
    Query -> Retriever -> Context Formatting -> Prompt -> LLM -> Answer

LCEL-Pattern (Buch S. 42):
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
"""

from typing import Dict, List, Any, Optional

from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from src.retriever import create_retriever, retrieve_documents
from src.system_prompt_ustg import get_rag_prompt, format_context
from src.generator import get_llm


# =============================================================================
# RAG-CHAIN ERSTELLUNG
# =============================================================================

def create_rag_chain():
    """
    Erstellt die vollstaendige RAG-Chain mit LCEL.
    
    Die Chain verbindet:
    1. Retriever: Holt relevante Dokumente aus ChromaDB
    2. Context Formatter: Formatiert Dokumente als Kontext-String
    3. Prompt: Kombiniert System-Prompt, Kontext und Frage
    4. LLM: Generiert die Antwort
    5. Parser: Extrahiert den String aus der LLM-Response
    
    Returns:
        Runnable: Die kompilierte RAG-Chain
        
    Beispiel:
        chain = create_rag_chain()
        answer = chain.invoke("Wie hoch ist der Umsatzsteuersatz?")
        
    Quelle: Buch S. 42-43 - LCEL Pipe Operator
    """
    # Komponenten initialisieren
    retriever = create_retriever()
    prompt = get_rag_prompt()
    llm = get_llm()
    
    # Hilfsfunktion: Dokumente formatieren
    def format_docs(docs: List[Document]) -> str:
        """Formatiert abgerufene Dokumente als Kontext-String."""
        return format_context(docs)
    
    # LCEL Chain aufbauen (Buch S. 42-43)
    # Pattern: {"context": ..., "question": ...} | prompt | llm | parser
    chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain


def create_rag_chain_with_sources():
    """
    Erstellt eine RAG-Chain, die auch die Quellen zurueckgibt.
    
    Returns:
        Runnable: Chain die {"answer": str, "sources": List[str]} liefert
        
    Beispiel:
        chain = create_rag_chain_with_sources()
        result = chain.invoke("Was ist die Kleinunternehmerregelung?")
        print(result["answer"])
        print(result["sources"])
    """
    retriever = create_retriever()
    prompt = get_rag_prompt()
    llm = get_llm()
    
    def format_docs_and_extract_sources(docs: List[Document]) -> Dict[str, Any]:
        """Formatiert Dokumente und extrahiert Quellenreferenzen."""
        context = format_context(docs)
        sources = [
            doc.metadata.get("full_reference", "Unbekannt")
            for doc in docs
        ]
        return {"context": context, "sources": sources}
    
    def create_response(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Kombiniert Antwort mit Quellen."""
        return {
            "answer": inputs["answer"],
            "sources": inputs["sources"],
        }
    
    # Chain mit Quellen-Tracking
    chain = (
        # Schritt 1: Retrieval + Context Formatting
        RunnablePassthrough.assign(
            docs=lambda x: retriever.invoke(x["question"])
        )
        # Schritt 2: Context und Sources extrahieren
        | RunnablePassthrough.assign(
            context=lambda x: format_context(x["docs"]),
            sources=lambda x: [
                d.metadata.get("full_reference", "?") for d in x["docs"]
            ]
        )
        # Schritt 3: LLM aufrufen
        | RunnablePassthrough.assign(
            answer=lambda x: (
                prompt.invoke({"context": x["context"], "question": x["question"]})
                | llm
                | StrOutputParser()
            ).invoke({})
        )
        # Schritt 4: Nur relevante Felder zurueckgeben
        | RunnableLambda(lambda x: {
            "answer": x["answer"],
            "sources": x["sources"],
            "question": x["question"],
        })
    )
    
    return chain


# =============================================================================
# EINFACHE INVOKE-FUNKTIONEN
# =============================================================================

def ask(question: str) -> str:
    """
    Stellt eine Frage an das RAG-System und gibt die Antwort zurueck.
    
    Args:
        question: Die Benutzerfrage in natuerlicher Sprache
        
    Returns:
        str: Die generierte Antwort
        
    Beispiel:
        answer = ask("Wie hoch ist der normale Umsatzsteuersatz?")
        print(answer)
    """
    chain = create_rag_chain()
    return chain.invoke(question)


def ask_with_sources(question: str) -> Dict[str, Any]:
    """
    Stellt eine Frage und gibt Antwort mit Quellen zurueck.
    
    Args:
        question: Die Benutzerfrage
        
    Returns:
        dict: {"answer": str, "sources": List[str], "question": str}
        
    Beispiel:
        result = ask_with_sources("Was ist die Kleinunternehmerregelung?")
        print(f"Antwort: {result['answer']}")
        print(f"Quellen: {result['sources']}")
    """
    chain = create_rag_chain_with_sources()
    return chain.invoke({"question": question})


# =============================================================================
# DETAILLIERTE PIPELINE (FUER DEBUGGING)
# =============================================================================

def run_rag_pipeline(question: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Fuehrt die RAG-Pipeline Schritt fuer Schritt aus.
    
    Diese Funktion ist nuetzlich fuer Debugging und um zu verstehen,
    was in jedem Schritt passiert.
    
    Args:
        question: Die Benutzerfrage
        verbose: Wenn True, werden Zwischenschritte ausgegeben
        
    Returns:
        dict: Vollstaendiges Ergebnis mit allen Zwischenschritten
    """
    result = {
        "question": question,
        "retrieved_docs": [],
        "context": "",
        "sources": [],
        "answer": "",
    }
    
    # Schritt 1: Retrieval
    if verbose:
        print(f"[1/4] Retrieval fuer: '{question[:50]}...'")
    
    docs = retrieve_documents(question)
    result["retrieved_docs"] = docs
    result["sources"] = [
        doc.metadata.get("full_reference", "?") for doc in docs
    ]
    
    if verbose:
        print(f"      Gefunden: {len(docs)} Dokumente")
        for i, doc in enumerate(docs, 1):
            ref = doc.metadata.get("full_reference", "?")
            print(f"      {i}. {ref}")
    
    # Schritt 2: Context Formatting
    if verbose:
        print(f"[2/4] Kontext formatieren...")
    
    context = format_context(docs)
    result["context"] = context
    
    if verbose:
        print(f"      Kontext-Laenge: {len(context)} Zeichen")
    
    # Schritt 3: Prompt erstellen
    if verbose:
        print(f"[3/4] Prompt erstellen...")
    
    prompt = get_rag_prompt()
    messages = prompt.invoke({
        "context": context,
        "question": question,
    })
    
    if verbose:
        print(f"      System-Message: {len(messages.messages[0].content)} Zeichen")
        print(f"      Human-Message: {len(messages.messages[1].content)} Zeichen")
    
    # Schritt 4: LLM aufrufen
    if verbose:
        print(f"[4/4] LLM aufrufen...")
    
    llm = get_llm()
    response = llm.invoke(messages)
    result["answer"] = response.content
    
    if verbose:
        print(f"      Antwort erhalten: {len(response.content)} Zeichen")
    
    return result


# =============================================================================
# INFO-FUNKTION
# =============================================================================

def get_workflow_info() -> dict:
    """
    Gibt Informationen ueber die Workflow-Konfiguration zurueck.
    
    Returns:
        dict: Workflow-Details
    """
    from src.retriever import get_retriever_info
    from src.generator import get_llm_info
    from src.system_prompt_ustg import get_prompt_info
    
    return {
        "retriever": get_retriever_info(),
        "llm": get_llm_info(),
        "prompt": get_prompt_info(),
        "pipeline_steps": [
            "1. Retrieval (ChromaDB)",
            "2. Context Formatting",
            "3. Prompt Assembly",
            "4. LLM Generation",
            "5. Output Parsing",
        ],
        "available_functions": [
            "ask(question) -> str",
            "ask_with_sources(question) -> dict",
            "run_rag_pipeline(question, verbose) -> dict",
            "create_rag_chain() -> Runnable",
        ],
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("STEUERHEUER RAG-CHAIN TEST")
    print("=" * 60)
    print()
    
    # Info ausgeben
    print("KONFIGURATION:")
    info = get_workflow_info()
    print(f"  LLM: {info['llm']['model']}")
    print(f"  Retriever: {info['retriever']['description']}")
    print(f"  Prompt: {info['prompt']['line_count']} Zeilen")
    print()
    
    # Test-Frage
    test_question = "Wie hoch ist der normale Umsatzsteuersatz in Deutschland?"
    print(f"TEST-FRAGE: \"{test_question}\"")
    print()
    
    print("Starte RAG-Pipeline...")
    print("-" * 60)
    
    try:
        result = run_rag_pipeline(test_question, verbose=True)
        
        print()
        print("-" * 60)
        print("ERGEBNIS:")
        print("-" * 60)
        print()
        print(f"QUELLEN: {', '.join(result['sources'])}")
        print()
        print("ANTWORT:")
        print(result["answer"])
        print()
        print("=" * 60)
        print("[OK] RAG-Chain funktioniert!")
        print("=" * 60)
        
    except Exception as e:
        print(f"[FEHLER] {e}")
        import traceback
        traceback.print_exc()
