"""
OpenAI Embedding-Modell Konfiguration.
======================================

Dieses Modul kapselt die Embedding-Funktionalitaet fuer das RAG-System.

Quellen:
- Buch S. 114-115 (Embeddings)
- Aufgabenliste S. 14-15
- https://docs.langchain.com/

Wichtig (Buch S. 114):
"The same model is used for both documents as well as queries
to ensure consistency in the vector space."
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

from src.config import (
    PROJECT_ROOT,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
)

# .env Datei laden (fuer OPENAI_API_KEY)
load_dotenv(PROJECT_ROOT / ".env")


def get_embedding_function() -> OpenAIEmbeddings:
    """
    Erstellt und gibt das konfigurierte Embedding-Modell zurueck.
    
    Returns:
        OpenAIEmbeddings: Das initialisierte Embedding-Modell
        
    Raises:
        ValueError: Wenn OPENAI_API_KEY nicht gesetzt ist
        
    Beispiel:
        embeddings = get_embedding_function()
        vector = embeddings.embed_query("Was ist der Umsatzsteuersatz?")
        
    Quelle: Buch S. 114 - OpenAIEmbeddings()
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY nicht gefunden. "
            "Bitte in .env Datei setzen: OPENAI_API_KEY=sk-..."
        )
    
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        # API-Key wird automatisch aus Umgebungsvariable gelesen
    )


def embed_single_text(text: str) -> list[float]:
    """
    Erstellt einen Embedding-Vektor fuer einen einzelnen Text.
    
    Args:
        text: Der zu embeddende Text
        
    Returns:
        list[float]: Der Embedding-Vektor (1536 Dimensionen)
        
    Hinweis:
        Fuer mehrere Texte ist embed_documents() effizienter.
        
    Quelle: Buch S. 114 - .embed_query()
    """
    embeddings = get_embedding_function()
    return embeddings.embed_query(text)


def embed_multiple_texts(texts: list[str]) -> list[list[float]]:
    """
    Erstellt Embedding-Vektoren fuer mehrere Texte.
    
    Args:
        texts: Liste von Texten
        
    Returns:
        list[list[float]]: Liste von Embedding-Vektoren
        
    Hinweis:
        Effizienter als einzelne Aufrufe, da Batch-Verarbeitung.
        
    Quelle: Buch S. 114 - .embed_documents()
    """
    embeddings = get_embedding_function()
    return embeddings.embed_documents(texts)


def get_embedding_info() -> dict:
    """
    Gibt Informationen ueber das Embedding-Modell zurueck.
    
    Returns:
        dict: Modellname, Dimensionen, API-Key Status
    """
    api_key = os.getenv("OPENAI_API_KEY")
    api_key_status = "Gesetzt" if api_key else "NICHT gesetzt"
    api_key_preview = f"{api_key[:8]}...{api_key[-4:]}" if api_key else "N/A"
    
    return {
        "model": EMBEDDING_MODEL,
        "dimensions": EMBEDDING_DIMENSIONS,
        "api_key_status": api_key_status,
        "api_key_preview": api_key_preview,
    }


if __name__ == "__main__":
    print("=== Embedding-Modul Test ===")
    
    # Info ausgeben
    info = get_embedding_info()
    print(f"Modell:      {info['model']}")
    print(f"Dimensionen: {info['dimensions']}")
    print(f"API-Key:     {info['api_key_status']} ({info['api_key_preview']})")
    print()
    
    # Test-Embedding erstellen
    print("Teste Embedding-Erstellung...")
    try:
        test_text = "Was ist der normale Umsatzsteuersatz in Deutschland?"
        vector = embed_single_text(test_text)
        print(f"[OK] Embedding erstellt")
        print(f"     Text: {test_text[:50]}...")
        print(f"     Vektor-Laenge: {len(vector)} Dimensionen")
        print(f"     Erste 5 Werte: {vector[:5]}")
    except Exception as e:
        print(f"[FEHLER] {e}")
