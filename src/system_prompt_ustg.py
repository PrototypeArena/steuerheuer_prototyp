"""
Prompt-Vorlagen fuer das Steuerheuer RAG-System.
=================================================

Dieses Modul laedt und verwaltet die System-Prompts fuer die
LLM-Antwortgenerierung. Der Prompt wird aus einer separaten
Markdown-Datei geladen, um einfache Bearbeitung zu ermoeglichen.

Aufgabe: 5.2 - System-Prompt entwickeln

Quellen:
- Buch S. 41: "Templates standardize prompts across your application."
- Buch S. 41: "Separate template logic from business logic."
- Aufgabenliste S. 23-24

Dateistruktur:
- prompts/system_prompt_ustg.md   -> Der eigentliche Prompt-Text
- src/system_prompt_ustg.py       -> Diese Datei (Lade-Logik)
"""

from pathlib import Path
from typing import List

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.documents import Document

from src.config import PROJECT_ROOT


# =============================================================================
# PFAD-KONFIGURATION
# =============================================================================

PROMPTS_DIR = PROJECT_ROOT / "prompts"
SYSTEM_PROMPT_FILE = PROMPTS_DIR / "system_prompt_ustg.md"


# =============================================================================
# PROMPT-LADEN
# =============================================================================

def load_system_prompt() -> str:
    """
    Laedt den System-Prompt aus der Markdown-Datei.
    
    Returns:
        str: Der System-Prompt als String
        
    Raises:
        FileNotFoundError: Wenn die Prompt-Datei nicht existiert
    """
    if not SYSTEM_PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"System-Prompt nicht gefunden: {SYSTEM_PROMPT_FILE}\n"
            f"Bitte erstelle die Datei: prompts/system_prompt_ustg.md"
        )
    
    with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
        return f.read()


# =============================================================================
# RAG-PROMPT TEMPLATE
# =============================================================================

RAG_USER_TEMPLATE = """
---

## Abgerufener Kontext aus dem UStG

Die folgenden Auszuege wurden zu dieser Anfrage abgerufen.
Nutze NUR diese Informationen fuer deine Antwort:

{context}

---

## Benutzerfrage

{question}
"""


def get_rag_prompt() -> ChatPromptTemplate:
    """
    Erstellt das vollstaendige RAG-Prompt mit System-Message und User-Template.
    
    Returns:
        ChatPromptTemplate: Das konfigurierte Prompt-Template
    """
    system_prompt = load_system_prompt()
    
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", RAG_USER_TEMPLATE),
    ])


def get_simple_prompt() -> PromptTemplate:
    """
    Erstellt ein einfaches Prompt-Template als String.
    
    Returns:
        PromptTemplate: Das einfache Template
    """
    system_prompt = load_system_prompt()
    
    full_template = f"""{system_prompt}

{RAG_USER_TEMPLATE}

---

## Deine Antwort:
"""
    
    return PromptTemplate.from_template(full_template)


# =============================================================================
# KONTEXT-FORMATIERUNG
# =============================================================================

def format_context(documents: List[Document]) -> str:
    """
    Formatiert eine Liste von Dokumenten als Kontext-String.
    
    Args:
        documents: Liste von LangChain Document-Objekten
        
    Returns:
        str: Formatierter Kontext mit Quellenangaben
    """
    if not documents:
        return "Keine relevanten Gesetzesauszuege gefunden."
    
    formatted_parts = []
    
    for doc in documents:
        ref = doc.metadata.get("full_reference", "Unbekannte Quelle")
        titel = doc.metadata.get("titel", "")
        content = doc.page_content.strip()
        
        header = f"[{ref}]"
        if titel:
            header += f" - {titel}"
        
        formatted_parts.append(f"{header}\n{content}")
    
    return "\n\n---\n\n".join(formatted_parts)


# =============================================================================
# INFO-FUNKTION
# =============================================================================

def get_prompt_info() -> dict:
    """
    Gibt Informationen ueber die Prompt-Konfiguration zurueck.
    
    Returns:
        dict: Prompt-Details (Pfad, Laenge, Status)
    """
    prompt_exists = SYSTEM_PROMPT_FILE.exists()
    prompt_length = 0
    line_count = 0
    
    if prompt_exists:
        content = load_system_prompt()
        prompt_length = len(content)
        line_count = len(content.split('\n'))
    
    return {
        "prompt_file": str(SYSTEM_PROMPT_FILE),
        "exists": prompt_exists,
        "length_chars": prompt_length,
        "line_count": line_count,
        "template_variables": ["context", "question"],
    }
