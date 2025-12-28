"""
Zentrale Konfiguration fuer das Steuerheuer RAG-Projekt.
=========================================================

Alle Pfade, Konstanten und Konfigurationsparameter an einem Ort.

Quellen:
- Aufgabenliste S. 4-6, S. 12-13
- Buch S. 117 (ChromaDB), S. 38 (LLM-Parameter)
"""

from pathlib import Path

# === PROJEKT-PFADE ===
# Berechnet relativ zu dieser Datei (src/config.py)
SRC_DIR = Path(__file__).parent
PROJECT_ROOT = SRC_DIR.parent

# Daten-Verzeichnisse
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Spezifische Dateien
USTG_XML_FILE = RAW_DATA_DIR / "umsatzsteuergesetz.xml"
USTG_DOCUMENTS_FILE = PROCESSED_DATA_DIR / "ustg_documents.json"

# === CHROMADB KONFIGURATION ===
# Quelle: Aufgabenliste S. 13
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
CHROMA_COLLECTION_NAME = "ustg_vectors"
CHROMA_COLLECTION_METADATA = {"hnsw:space": "cosine"}

# === EMBEDDING KONFIGURATION ===
# Quelle: Aufgabenliste S. 14-15, Buch S. 114
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

# === LLM KONFIGURATION ===
# Quelle: Aufgabenliste S. 20-21, Buch S. 38-39
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.1  # Niedrig fuer faktische Antworten
LLM_MAX_TOKENS = 1000

# === RETRIEVAL KONFIGURATION ===
# Quelle: Aufgabenliste S. 18
RETRIEVER_K = 5  # Top-5 Ergebnisse
RETRIEVER_SEARCH_TYPE = "similarity"

# === TOKEN KONFIGURATION ===
# Quelle: Aufgabenliste S. 9-10
MIN_TOKENS_FOR_SPLIT = 1000
TIKTOKEN_MODEL = "gpt-4o-mini"


def print_config():
    """Gibt die aktuelle Konfiguration aus (fuer Debugging)."""
    print("=== Steuerheuer RAG Konfiguration ===")
    print(f"PROJECT_ROOT:          {PROJECT_ROOT}")
    print(f"CHROMA_DIR:            {CHROMA_DIR}")
    print(f"CHROMA_COLLECTION:     {CHROMA_COLLECTION_NAME}")
    print(f"EMBEDDING_MODEL:       {EMBEDDING_MODEL}")
    print(f"LLM_MODEL:             {LLM_MODEL}")
    print(f"RETRIEVER_K:           {RETRIEVER_K}")


if __name__ == "__main__":
    print_config()
