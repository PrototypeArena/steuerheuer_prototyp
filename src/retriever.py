"""
Retriever-Konfiguration fuer das Steuerheuer RAG-System.
=========================================================

Dieses Modul stellt den konfigurierten Retriever bereit,
der Dokumente basierend auf semantischer Aehnlichkeit abruft.

Quellen:
- Buch S. 137-140 (Retrievers)
- Aufgabenliste S. 18
- https://python.langchain.com/docs/how_to/vectorstore_retriever/

Wichtig (LangChain Docs):
"Users should favor using .invoke or .batch rather than 
get_relevant_documents directly."
"""

from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_chroma import Chroma

from src.config import (
    RETRIEVER_K,
    RETRIEVER_SEARCH_TYPE,
)
from src.embeddings import get_embedding_function
from src.vectorstore import get_vectorstore


def create_retriever(
    k: int = RETRIEVER_K,
    search_type: str = RETRIEVER_SEARCH_TYPE,
) -> VectorStoreRetriever:
    """
    Erstellt und konfiguriert den Retriever fuer das RAG-System.
    
    Args:
        k: Anzahl der zurueckzugebenden Dokumente (Standard: 5)
        search_type: Suchtyp - "similarity", "mmr", oder 
                     "similarity_score_threshold"
        
    Returns:
        VectorStoreRetriever: Der konfigurierte Retriever
        
    Beispiel:
        retriever = create_retriever()
        docs = retriever.invoke("Was ist der Umsatzsteuersatz?")
        
    Quelle: Buch S. 137 - vectorstore.as_retriever()
    """
    # Embedding-Funktion und VectorStore laden
    embedding_function = get_embedding_function()
    vectorstore = get_vectorstore(embedding_function)
    
    # Retriever konfigurieren
    retriever = vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs={"k": k},
    )
    
    return retriever


def retrieve_documents(
    query: str,
    k: int = RETRIEVER_K,
    search_type: str = RETRIEVER_SEARCH_TYPE,
) -> List[Document]:
    """
    Ruft relevante Dokumente fuer eine Anfrage ab.
    
    Args:
        query: Die Suchanfrage in natuerlicher Sprache
        k: Anzahl der zurueckzugebenden Dokumente
        search_type: Suchtyp
        
    Returns:
        List[Document]: Liste der relevantesten Dokumente
        
    Beispiel:
        docs = retrieve_documents("Wie hoch ist die Mehrwertsteuer?")
        for doc in docs:
            print(doc.metadata["full_reference"])
            
    Quelle: LangChain Docs - retriever.invoke()
    """
    retriever = create_retriever(k=k, search_type=search_type)
    
    # invoke() ist die aktuelle Methode (nicht get_relevant_documents)
    documents = retriever.invoke(query)
    
    return documents


def retrieve_with_scores(
    query: str,
    k: int = RETRIEVER_K,
) -> List[tuple[Document, float]]:
    """
    Ruft Dokumente mit Aehnlichkeits-Scores ab.
    
    Args:
        query: Die Suchanfrage
        k: Anzahl der Ergebnisse
        
    Returns:
        List[tuple[Document, float]]: Dokumente mit Scores
        
    Hinweis:
        Der Score ist die Cosine-Distanz (niedriger = aehnlicher).
        Bei Cosine Similarity: 0.0 = identisch, 2.0 = gegensaetzlich.
        
    Quelle: ChromaDB - similarity_search_with_score()
    """
    embedding_function = get_embedding_function()
    vectorstore = get_vectorstore(embedding_function)
    
    # Diese Methode gibt auch die Scores zurueck
    results = vectorstore.similarity_search_with_score(query, k=k)
    
    return results


def get_retriever_info() -> dict:
    """
    Gibt Informationen ueber die Retriever-Konfiguration zurueck.
    
    Returns:
        dict: Konfigurationsdetails
    """
    return {
        "k": RETRIEVER_K,
        "search_type": RETRIEVER_SEARCH_TYPE,
        "description": f"Top-{RETRIEVER_K} Dokumente via {RETRIEVER_SEARCH_TYPE} search",
    }


if __name__ == "__main__":
    print("=== Retriever-Modul Test ===")
    
    # Info ausgeben
    info = get_retriever_info()
    print(f"Konfiguration: {info['description']}")
    print()
    
    # Test-Abfrage
    test_query = "Wie hoch ist der normale Umsatzsteuersatz in Deutschland?"
    print(f"Test-Query: \"{test_query}\"")
    print()
    
    print("Rufe Dokumente ab...")
    try:
        docs = retrieve_documents(test_query)
        
        print(f"[OK] {len(docs)} Dokumente gefunden:")
        print()
        
        for i, doc in enumerate(docs, 1):
            ref = doc.metadata.get("full_reference", "N/A")
            para = doc.metadata.get("paragraph", "N/A")
            tokens = doc.metadata.get("token_count", 0)
            preview = doc.page_content[:80].replace("\n", " ")
            
            print(f"{i}. {ref}")
            print(f"   Paragraph: {para}")
            print(f"   Tokens: {tokens}")
            print(f"   Text: {preview}...")
            print()
            
    except Exception as e:
        print(f"[FEHLER] {e}")
        import traceback
        traceback.print_exc()
