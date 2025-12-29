"""
LLM-Generator fuer das Steuerheuer RAG-System.
===============================================

Dieses Modul kapselt die LLM-Konfiguration und stellt
das ChatOpenAI-Modell fuer die Antwortgenerierung bereit.

Aufgabe: 5.1 - LLM-Modell konfigurieren

Quellen:
- Buch S. 66: "For factual, consistent responses: temperature=0.1"
- Buch S. 67: "For enterprise applications requiring consistency 
              and accuracy, lower temperatures (0.0-0.3)"
- LangChain Docs: ChatOpenAI API Reference
- Aufgabenliste S. 20-21

Wichtig (LangChain Docs, Sept 2024):
"OpenAI deprecated max_tokens in favor of max_completion_tokens.
 While max_tokens is still supported for backwards compatibility,
 it's automatically converted to max_completion_tokens internally."
"""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from src.config import (
    PROJECT_ROOT,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)

# .env Datei laden (fuer OPENAI_API_KEY)
load_dotenv(PROJECT_ROOT / ".env")


def get_llm(
    model: str = LLM_MODEL,
    temperature: float = LLM_TEMPERATURE,
    max_tokens: int = LLM_MAX_TOKENS,
) -> ChatOpenAI:
    """
    Erstellt und gibt das konfigurierte LLM zurueck.
    
    Args:
        model: OpenAI-Modellname (Standard: gpt-4o-mini)
        temperature: Sampling-Temperatur (Standard: 0.1 fuer faktisch)
        max_tokens: Maximale Ausgabe-Tokens (Standard: 1000)
        
    Returns:
        ChatOpenAI: Das initialisierte Chat-Modell
        
    Raises:
        ValueError: Wenn OPENAI_API_KEY nicht gesetzt ist
        
    Beispiel:
        llm = get_llm()
        response = llm.invoke([HumanMessage(content="Hallo!")])
        print(response.content)
        
    Quellen:
        - Buch S. 66: temperature=0.1 fuer faktische Antworten
        - LangChain Docs: ChatOpenAI Parameter
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY nicht gefunden. "
            "Bitte in .env Datei setzen: OPENAI_API_KEY=sk-..."
        )
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=2,
        # API-Key wird automatisch aus Umgebungsvariable gelesen
    )


def invoke_llm(
    user_message: str,
    system_message: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None,
) -> str:
    """
    Sendet eine Nachricht an das LLM und gibt die Antwort zurueck.
    
    Args:
        user_message: Die Benutzeranfrage
        system_message: Optionale System-Anweisung
        llm: Optionales vorinitialisiertes LLM
        
    Returns:
        str: Die Antwort des LLM
        
    Beispiel:
        antwort = invoke_llm(
            user_message="Was ist der Umsatzsteuersatz?",
            system_message="Du bist ein Steuerexperte."
        )
        
    Quelle: LangChain Docs - llm.invoke(messages)
    """
    if llm is None:
        llm = get_llm()
    
    messages = []
    
    if system_message:
        messages.append(SystemMessage(content=system_message))
    
    messages.append(HumanMessage(content=user_message))
    
    response = llm.invoke(messages)
    
    return response.content


def get_llm_info() -> dict:
    """
    Gibt Informationen ueber die LLM-Konfiguration zurueck.
    
    Returns:
        dict: Modellname, Temperatur, Max-Tokens, API-Key Status
    """
    api_key = os.getenv("OPENAI_API_KEY")
    api_key_status = "Gesetzt" if api_key else "NICHT gesetzt"
    api_key_preview = f"{api_key[:8]}...{api_key[-4:]}" if api_key else "N/A"
    
    return {
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
        "api_key_status": api_key_status,
        "api_key_preview": api_key_preview,
        "description": (
            f"{LLM_MODEL} mit temperature={LLM_TEMPERATURE} "
            f"(faktisch/konsistent)"
        ),
    }


if __name__ == "__main__":
    print("=== LLM-Generator-Modul Test ===")
    print()
    
    # Info ausgeben
    info = get_llm_info()
    print("KONFIGURATION:")
    print(f"  Modell:      {info['model']}")
    print(f"  Temperatur:  {info['temperature']} (faktisch)")
    print(f"  Max-Tokens:  {info['max_tokens']}")
    print(f"  API-Key:     {info['api_key_status']} ({info['api_key_preview']})")
    print()
    
    # Test-Anfrage
    print("TEST-ANFRAGE:")
    test_message = "Antworte in einem Satz: Was ist die Aufgabe eines RAG-Systems?"
    print(f"  Input: \"{test_message}\"")
    print()
    
    try:
        print("  Sende Anfrage an OpenAI...")
        response = invoke_llm(
            user_message=test_message,
            system_message="Du bist ein hilfreicher Assistent. Antworte praegnant."
        )
        print()
        print("  [OK] Antwort erhalten:")
        print(f"  \"{response}\"")
        print()
        print("=" * 50)
        print("[OK] LLM-Modul funktioniert korrekt!")
        print("=" * 50)
        
    except Exception as e:
        print(f"  [FEHLER] {e}")
        import traceback
        traceback.print_exc()
