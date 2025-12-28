"""
UStG Indexierungspipeline
=========================
Laedt geparste Dokumente und indexiert sie in ChromaDB.

Dieser Schritt:
1. Laedt ustg_documents.json
2. Konvertiert zu LangChain Document-Objekten
3. Erstellt Embeddings via OpenAI API
4. Speichert in ChromaDB mit persistenter Speicherung

Quellen:
- Buch S. 127 (Indexing Pipeline)
- Buch S. 117 (Chroma.from_documents)
- Aufgabenliste S. 16-17
"""

import json
import sys
from pathlib import Path
from datetime import datetime

from langchain_core.documents import Document
from langchain_chroma import Chroma

# Projekt-Root zu sys.path hinzufuegen
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    USTG_DOCUMENTS_FILE,
    CHROMA_DIR,
    CHROMA_COLLECTION_NAME,
    CHROMA_COLLECTION_METADATA,
)
from src.embeddings import get_embedding_function, get_embedding_info


def load_documents_from_json(json_path: Path) -> tuple[list[Document], list[str]]:
    """
    Laedt Dokumente aus JSON und konvertiert zu LangChain Documents.
    
    Args:
        json_path: Pfad zur JSON-Datei
        
    Returns:
        tuple: (Liste von Documents, Liste von IDs)
    """
    print(f"[1/4] Lade Dokumente aus: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    ids = []
    
    for doc_dict in data["documents"]:
        # LangChain Document erstellen
        doc = Document(
            page_content=doc_dict["page_content"],
            metadata=doc_dict["metadata"]
        )
        documents.append(doc)
        
        # UUID als ID verwenden
        ids.append(doc_dict["metadata"]["chunk_id"])
    
    print(f"      {len(documents)} Dokumente geladen")
    print(f"      Quelle: {data['metadata']['source_file']}")
    print(f"      Parser-Version: {data['metadata']['parser_version']}")
    
    return documents, ids


def create_vectorstore(
    documents: list[Document],
    ids: list[str],
    embedding_function,
) -> Chroma:
    """
    Erstellt ChromaDB mit den gegebenen Dokumenten.
    
    Args:
        documents: Liste von LangChain Documents
        ids: Liste von eindeutigen IDs (UUIDs)
        embedding_function: Das Embedding-Modell
        
    Returns:
        Chroma: Die erstellte Vektordatenbank
    """
    print(f"[3/4] Erstelle ChromaDB...")
    print(f"      Collection: {CHROMA_COLLECTION_NAME}")
    print(f"      Speicherort: {CHROMA_DIR}")
    print(f"      Distanzmetrik: {CHROMA_COLLECTION_METADATA.get('hnsw:space', 'default')}")
    print()
    print("      Erstelle Embeddings und speichere...")
    print("      (Dies kann 30-60 Sekunden dauern)")
    print()
    
    # Verzeichnis sicherstellen
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    
    # ChromaDB erstellen mit unseren IDs
    start_time = datetime.now()
    
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_function,
        ids=ids,
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        collection_metadata=CHROMA_COLLECTION_METADATA,
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"      Fertig in {elapsed:.1f} Sekunden")
    
    return vectorstore


def print_statistics(vectorstore: Chroma, documents: list[Document]):
    """Gibt Statistiken ueber die indexierten Dokumente aus."""
    print(f"[4/4] Statistiken:")
    
    # Collection-Statistiken
    collection = vectorstore._collection
    count = collection.count()
    
    print(f"      Dokumente in ChromaDB: {count}")
    
    # Token-Statistiken aus Metadaten
    token_counts = [d.metadata.get("token_count", 0) for d in documents]
    total_tokens = sum(token_counts)
    
    print(f"      Gesamt-Tokens: {total_tokens:,}")
    print(f"      Durchschnitt: {total_tokens // len(documents)} Tokens/Dokument")
    
    # Paragraphen-Statistiken
    paragraphs = set(d.metadata.get("paragraph", "") for d in documents)
    sections = set(d.metadata.get("abschnitt", "") for d in documents)
    
    print(f"      Paragraphen: {len(paragraphs)}")
    print(f"      Abschnitte: {len(sections)}")
    
    # Geschaetzte Kosten
    cost_estimate = (total_tokens / 1_000_000) * 0.02
    print(f"      Geschaetzte API-Kosten: ${cost_estimate:.4f}")


def main():
    """Hauptfunktion der Indexierungspipeline."""
    print("=" * 60)
    print("UStG Indexierungspipeline")
    print("=" * 60)
    print()
    
    # Pruefen ob JSON existiert
    if not USTG_DOCUMENTS_FILE.exists():
        print(f"FEHLER: Dokument-Datei nicht gefunden: {USTG_DOCUMENTS_FILE}")
        print("Bitte zuerst parse_ustg.py ausfuehren.")
        return
    
    # 1. Dokumente laden
    documents, ids = load_documents_from_json(USTG_DOCUMENTS_FILE)
    print()
    
    # 2. Embedding-Modell initialisieren
    print("[2/4] Initialisiere Embedding-Modell...")
    embedding_info = get_embedding_info()
    print(f"      Modell: {embedding_info['model']}")
    print(f"      Dimensionen: {embedding_info['dimensions']}")
    print(f"      API-Key: {embedding_info['api_key_status']}")
    
    if embedding_info['api_key_status'] != "Gesetzt":
        print("FEHLER: OpenAI API-Key nicht gesetzt!")
        return
    
    embedding_function = get_embedding_function()
    print()
    
    # 3. ChromaDB erstellen
    vectorstore = create_vectorstore(documents, ids, embedding_function)
    print()
    
    # 4. Statistiken ausgeben
    print_statistics(vectorstore, documents)
    print()
    
    print("=" * 60)
    print("Indexierung erfolgreich abgeschlossen!")
    print("=" * 60)
    print()
    print(f"ChromaDB gespeichert in: {CHROMA_DIR}")
    print("Naechster Schritt: Retrieval testen mit query.py")


if __name__ == "__main__":
    main()
