"""
ChromaDB Vector Store Operationen.
==================================

Dieses Modul kapselt alle Interaktionen mit der ChromaDB-Vektordatenbank.

Quellen:
- Buch S. 115-117 (Vector Stores)
- Buch S. 137 (Retriever)
- Aufgabenliste S. 12-13
- https://docs.langchain.com/
"""

from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_chroma import Chroma

from src.config import (
    CHROMA_DIR,
    CHROMA_COLLECTION_NAME,
    CHROMA_COLLECTION_METADATA,
    RETRIEVER_K,
    RETRIEVER_SEARCH_TYPE,
)


def get_vectorstore(embedding_function: Embeddings) -> Chroma:
    """
    Laedt eine bestehende ChromaDB-Instanz.
    
    Args:
        embedding_function: Das Embedding-Modell (z.B. OpenAIEmbeddings)
        
    Returns:
        Chroma: Die geladene Vektordatenbank
        
    Hinweis:
        Die Datenbank muss bereits existieren. Falls nicht, verwenden Sie
        create_vectorstore_from_documents().
        
    Quelle: Buch S. 117
    """
    return Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embedding_function,
        persist_directory=str(CHROMA_DIR),
        collection_metadata=CHROMA_COLLECTION_METADATA,
    )


def create_vectorstore_from_documents(
    documents: List[Document],
    embedding_function: Embeddings,
) -> Chroma:
    """
    Erstellt eine neue ChromaDB aus einer Liste von Documents.
    
    Args:
        documents: Liste von LangChain Document-Objekten
        embedding_function: Das Embedding-Modell
        
    Returns:
        Chroma: Die neu erstellte Vektordatenbank
        
    Hinweis:
        Diese Funktion erstellt Embeddings fuer alle Dokumente.
        Bei 516 Documents und ~85.000 Tokens dauert dies einige Sekunden
        und verursacht API-Kosten (~$0.002 bei text-embedding-3-small).
        
    Quelle: Buch S. 117 - Chroma.from_documents()
    """
    # Verzeichnis sicherstellen
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    
    return Chroma.from_documents(
        documents=documents,
        embedding=embedding_function,
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        collection_metadata=CHROMA_COLLECTION_METADATA,
    )


def add_documents_to_vectorstore(
    vectorstore: Chroma,
    documents: List[Document],
) -> List[str]:
    """
    Fuegt weitere Dokumente zu einer bestehenden Datenbank hinzu.
    
    Args:
        vectorstore: Die bestehende ChromaDB-Instanz
        documents: Neue Dokumente zum Hinzufuegen
        
    Returns:
        List[str]: IDs der hinzugefuegten Dokumente
        
    Quelle: Buch S. 117 - .add_documents()
    """
    return vectorstore.add_documents(documents)


def get_retriever(
    vectorstore: Chroma,
    k: int = RETRIEVER_K,
    search_type: str = RETRIEVER_SEARCH_TYPE,
) -> VectorStoreRetriever:
    """
    Erstellt einen Retriever aus der Vektordatenbank.
    
    Args:
        vectorstore: Die ChromaDB-Instanz
        k: Anzahl der zurueckzugebenden Dokumente (Standard: 5)
        search_type: Suchtyp ("similarity" oder "mmr")
        
    Returns:
        VectorStoreRetriever: Der konfigurierte Retriever
        
    Quelle: Buch S. 137 - vectorstore.as_retriever()
    """
    return vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs={"k": k},
    )


def similarity_search(
    vectorstore: Chroma,
    query: str,
    k: int = RETRIEVER_K,
) -> List[Document]:
    """
    Fuehrt eine Aehnlichkeitssuche durch.
    
    Args:
        vectorstore: Die ChromaDB-Instanz
        query: Die Suchanfrage
        k: Anzahl der Ergebnisse
        
    Returns:
        List[Document]: Die aehnlichsten Dokumente
        
    Quelle: Buch S. 117 - .similarity_search()
    """
    return vectorstore.similarity_search(query, k=k)


def get_collection_stats(vectorstore: Chroma) -> dict:
    """
    Gibt Statistiken ueber die Collection zurueck.
    
    Args:
        vectorstore: Die ChromaDB-Instanz
        
    Returns:
        dict: Statistiken (count, collection_name, etc.)
    """
    # Zugriff auf die zugrundeliegende Collection
    collection = vectorstore._collection
    
    return {
        "collection_name": CHROMA_COLLECTION_NAME,
        "document_count": collection.count(),
        "persist_directory": str(CHROMA_DIR),
        "metadata": CHROMA_COLLECTION_METADATA,
    }


if __name__ == "__main__":
    # Test: Nur Struktur pruefen (ohne Embedding-Modell)
    print("=== VectorStore Modul ===")
    print(f"Collection Name: {CHROMA_COLLECTION_NAME}")
    print(f"Persist Dir:     {CHROMA_DIR}")
    print(f"Retriever K:     {RETRIEVER_K}")
    print(f"Search Type:     {RETRIEVER_SEARCH_TYPE}")
    print()
    print("Verfuegbare Funktionen:")
    print("  - get_vectorstore(embedding_function)")
    print("  - create_vectorstore_from_documents(documents, embedding_function)")
    print("  - add_documents_to_vectorstore(vectorstore, documents)")
    print("  - get_retriever(vectorstore, k, search_type)")
    print("  - similarity_search(vectorstore, query, k)")
    print("  - get_collection_stats(vectorstore)")
