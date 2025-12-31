#!/usr/bin/env python3
"""
Steuerheuer CLI - Interaktives Command-Line Interface.
=======================================================

VERSION 2.0 - MIT SESSION-MANAGEMENT

Änderungen gegenüber v1:
- Generiert eindeutige Session-ID beim Start
- Übergibt thread_id an ask_graph für Memory
- Zeigt Session-Info im Banner

Quellen:
- Buch S. 102: "config={'configurable': {'thread_id': ...}}"
- Aufgabenliste S. 897-916 (Phase 7: Benutzeroberfläche)

Verwendung:
    python scripts/cli_v2.py
    
Features:
    - Kontinuierliche Frage-Antwort-Schleife MIT MEMORY
    - Session-ID für Konversationsgedächtnis
    - Formatierte Antworten mit Quellenangaben
"""

import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Projekt-Root zu sys.path hinzufügen
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# SESSION-MANAGEMENT (NEU in v2.0)
# =============================================================================

# Generiere eine eindeutige Session-ID beim Start
# Diese ID wird für alle Anfragen in dieser CLI-Sitzung verwendet
SESSION_ID = str(uuid.uuid4())


# =============================================================================
# ANSI FARB-CODES
# =============================================================================

class Colors:
    """ANSI Escape-Codes für Terminal-Farben."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        """Deaktiviert Farben."""
        cls.HEADER = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''
        cls.END = ''


# =============================================================================
# CLI KONSTANTEN (aktualisiert für v2.0)
# =============================================================================

BANNER = f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   {Colors.BOLD}STEUERHEUER{Colors.END}{Colors.CYAN} - UStG RAG-Assistent  {Colors.GREEN}[v2.0 mit Memory]{Colors.END}{Colors.CYAN}           ║
║                                                                       ║
║   Ihr intelligenter Assistent für das deutsche Umsatzsteuergesetz    ║
║   {Colors.YELLOW}★ Konversationsgedächtnis aktiviert{Colors.END}{Colors.CYAN}                              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝{Colors.END}
"""

HELP_TEXT = f"""
{Colors.BOLD}VERFÜGBARE BEFEHLE:{Colors.END}

  {Colors.GREEN}[Ihre Frage]{Colors.END}    Stellen Sie eine Frage zum Umsatzsteuergesetz
  
  {Colors.YELLOW}hilfe, help, ?{Colors.END}  Diese Hilfe anzeigen
  {Colors.YELLOW}status{Colors.END}          System-Status und Memory-Info anzeigen
  {Colors.YELLOW}history{Colors.END}         Bisherigen Chatverlauf anzeigen {Colors.GREEN}(NEU!){Colors.END}
  {Colors.YELLOW}reset{Colors.END}           Konversation zurücksetzen {Colors.GREEN}(NEU!){Colors.END}
  {Colors.YELLOW}beispiele{Colors.END}       Beispielfragen anzeigen
  {Colors.YELLOW}exit, quit, q{Colors.END}   Programm beenden

{Colors.BOLD}MEMORY-FEATURE (NEU in v2.0):{Colors.END}

  Das System merkt sich jetzt Ihre vorherigen Fragen und Antworten!
  
  Beispiel:
    Sie: "Mein Name ist Max"
    Assistent: "Hallo Max! Wie kann ich helfen?"
    Sie: "Wie heiße ich?"
    Assistent: "Sie haben mir gesagt, dass Ihr Name Max ist."

{Colors.CYAN}Hinweis: Die Antworten basieren auf dem UStG.
Für individuelle Beratung wenden Sie sich an einen Steuerberater.{Colors.END}
"""

EXAMPLE_QUESTIONS = [
    "Wie hoch ist der normale Umsatzsteuersatz in Deutschland?",
    "Was ist die Kleinunternehmerregelung?",
    "Wie funktioniert der Vorsteuerabzug?",
    "Wann muss ich eine Umsatzsteuervoranmeldung abgeben?",
    "Welche Umsätze sind steuerfrei?",
]

EXIT_COMMANDS = {"exit", "quit", "q", "beenden", "ende"}
HELP_COMMANDS = {"hilfe", "help", "?", "h"}
STATUS_COMMANDS = {"status", "info"}
EXAMPLE_COMMANDS = {"beispiele", "beispiel", "examples"}
HISTORY_COMMANDS = {"history", "verlauf", "historie"}
RESET_COMMANDS = {"reset", "neu", "zurücksetzen", "clear"}


# =============================================================================
# FORMATIERUNGS-FUNKTIONEN
# =============================================================================

def print_divider(char: str = "─", length: int = 70):
    """Gibt eine Trennlinie aus."""
    print(f"{Colors.CYAN}{char * length}{Colors.END}")


def format_answer(answer: str) -> str:
    """Formatiert die Antwort für die Ausgabe."""
    return answer


def print_sources(sources: list):
    """Gibt die Quellenangaben formatiert aus."""
    if not sources:
        return
    
    print()
    print(f"{Colors.BOLD}{Colors.BLUE}QUELLEN:{Colors.END}")
    
    seen = set()
    unique_sources = []
    for src in sources:
        if src not in seen:
            seen.add(src)
            unique_sources.append(src)
    
    for i, source in enumerate(unique_sources, 1):
        print(f"  {Colors.CYAN}[{i}]{Colors.END} {source}")


def print_error(message: str):
    """Gibt eine Fehlermeldung aus."""
    print(f"\n{Colors.RED}FEHLER: {message}{Colors.END}\n")


def print_warning(message: str):
    """Gibt eine Warnung aus."""
    print(f"\n{Colors.YELLOW}HINWEIS: {message}{Colors.END}\n")


def print_success(message: str):
    """Gibt eine Erfolgsmeldung aus."""
    print(f"\n{Colors.GREEN}{message}{Colors.END}\n")


# =============================================================================
# SESSION-INFO (NEU in v2.0)
# =============================================================================

def print_session_info():
    """Zeigt Informationen über die aktuelle Session."""
    print()
    print(f"{Colors.BOLD}SESSION-INFO:{Colors.END}")
    print(f"  Session-ID: {Colors.CYAN}{SESSION_ID[:8]}...{Colors.END}")
    print(f"  Gestartet: {datetime.now().strftime('%H:%M:%S')}")
    print(f"  Memory: {Colors.GREEN}Aktiviert{Colors.END}")
    print()


# =============================================================================
# CONVERSATION HISTORY (NEU in v2.0)
# =============================================================================

def print_conversation_history():
    """Zeigt den bisherigen Chatverlauf."""
    try:
        from src.graph_v2 import get_conversation_state
        
        state = get_conversation_state(SESSION_ID)
        
        if not state or not state.get("messages"):
            print()
            print(f"{Colors.YELLOW}Noch keine Konversation in dieser Session.{Colors.END}")
            print()
            return
        
        messages = state.get("messages", [])
        
        print()
        print(f"{Colors.BOLD}CHATVERLAUF ({len(messages)} Nachrichten):{Colors.END}")
        print_divider()
        
        from langchain_core.messages import HumanMessage, AIMessage
        
        for i, msg in enumerate(messages, 1):
            if isinstance(msg, HumanMessage):
                print(f"{Colors.GREEN}[{i}] Sie:{Colors.END}")
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                print(f"    {content}")
            elif isinstance(msg, AIMessage):
                print(f"{Colors.BLUE}[{i}] Assistent:{Colors.END}")
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                print(f"    {content}")
            print()
        
        print_divider()
        print()
        
    except Exception as e:
        print_error(f"Konnte History nicht laden: {e}")


def reset_conversation():
    """Setzt die Konversation zurück (neue Session-ID)."""
    global SESSION_ID
    
    old_id = SESSION_ID[:8]
    SESSION_ID = str(uuid.uuid4())
    
    print()
    print(f"{Colors.GREEN}Konversation zurückgesetzt!{Colors.END}")
    print(f"  Alte Session: {old_id}...")
    print(f"  Neue Session: {SESSION_ID[:8]}...")
    print()


# =============================================================================
# SYSTEM-STATUS
# =============================================================================

def get_system_status() -> Dict[str, Any]:
    """Sammelt Informationen über den System-Status."""
    status = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": SESSION_ID[:8] + "...",
        "graph_ready": False,
        "vectorstore_ready": False,
        "llm_ready": False,
        "memory_enabled": True,
        "document_count": 0,
        "message_count": 0,
        "errors": [],
    }
    
    try:
        from src.graph_v2 import create_rag_graph, get_conversation_state
        graph = create_rag_graph()
        status["graph_ready"] = True
        
        # Message-Count aus aktuellem State
        state = get_conversation_state(SESSION_ID)
        if state and state.get("messages"):
            status["message_count"] = len(state["messages"])
            
    except Exception as e:
        status["errors"].append(f"Graph: {str(e)}")
    
    try:
        from src.embeddings import get_embedding_function
        from src.vectorstore import get_vectorstore, get_collection_stats
        
        embedding_fn = get_embedding_function()
        vectorstore = get_vectorstore(embedding_fn)
        stats = get_collection_stats(vectorstore)
        
        status["vectorstore_ready"] = True
        status["document_count"] = stats.get("document_count", 0)
    except Exception as e:
        status["errors"].append(f"VectorStore: {str(e)}")
    
    try:
        from src.generator import get_llm_info
        llm_info = get_llm_info()
        status["llm_ready"] = llm_info.get("api_key_status") == "Gesetzt"
        status["llm_model"] = llm_info.get("model", "unbekannt")
    except Exception as e:
        status["errors"].append(f"LLM: {str(e)}")
    
    return status


def print_status():
    """Gibt den System-Status aus."""
    print()
    print(f"{Colors.BOLD}SYSTEM-STATUS:{Colors.END}")
    print_divider()
    
    status = get_system_status()
    
    graph_status = f"{Colors.GREEN}✓{Colors.END}" if status["graph_ready"] else f"{Colors.RED}✗{Colors.END}"
    vs_status = f"{Colors.GREEN}✓{Colors.END}" if status["vectorstore_ready"] else f"{Colors.RED}✗{Colors.END}"
    llm_status = f"{Colors.GREEN}✓{Colors.END}" if status["llm_ready"] else f"{Colors.RED}✗{Colors.END}"
    memory_status = f"{Colors.GREEN}✓{Colors.END}" if status["memory_enabled"] else f"{Colors.RED}✗{Colors.END}"
    
    print(f"  {graph_status} LangGraph Workflow (v2.0 mit Checkpointer)")
    print(f"  {vs_status} ChromaDB VectorStore ({status['document_count']} Dokumente)")
    print(f"  {llm_status} LLM ({status.get('llm_model', 'N/A')})")
    print(f"  {memory_status} Konversationsgedächtnis ({status['message_count']} Nachrichten)")
    print()
    print(f"  Session-ID: {status['session_id']}")
    print(f"  Zeitstempel: {status['timestamp']}")
    
    if status["errors"]:
        print()
        print(f"{Colors.RED}FEHLER:{Colors.END}")
        for error in status["errors"]:
            print(f"  • {error}")
    
    print_divider()
    print()


# =============================================================================
# HAUPT-ABFRAGE-FUNKTION (v2.0 mit thread_id)
# =============================================================================

def ask_question(question: str) -> Optional[Dict[str, Any]]:
    """
    Stellt eine Frage an das RAG-System MIT SESSION-PERSISTENZ.
    
    KRITISCHE ÄNDERUNG (v2.0):
    Die Funktion übergibt jetzt die SESSION_ID als thread_id,
    wodurch der Checkpointer die Konversation speichern kann.
    
    Args:
        question: Die Benutzerfrage
        
    Returns:
        dict: Ergebnis mit 'answer', 'sources', 'error'
    """
    try:
        from src.graph_v2 import ask_graph
        
        # KRITISCHE ÄNDERUNG: thread_id für Memory übergeben!
        result = ask_graph(question, thread_id=SESSION_ID)
        return result
        
    except ImportError as e:
        print_error(f"Modul konnte nicht geladen werden: {e}")
        print_warning("Versuche Fallback auf v1...")
        
        try:
            from src.graph import ask_graph as ask_graph_v1
            result = ask_graph_v1(question)
            print_warning("Fallback erfolgreich, aber Memory nicht verfügbar!")
            return result
        except:
            return None
            
    except Exception as e:
        return {
            "answer": "",
            "sources": [],
            "error": str(e),
        }


# =============================================================================
# INTERAKTIVE SCHLEIFE
# =============================================================================

def run_interactive_loop():
    """
    Hauptschleife für interaktive Frage-Antwort-Sitzung MIT MEMORY.
    """
    # Banner anzeigen
    print(BANNER)
    print_session_info()
    
    print(f"Geben Sie {Colors.GREEN}'hilfe'{Colors.END} ein für verfügbare Befehle.")
    print(f"Geben Sie {Colors.YELLOW}'exit'{Colors.END} ein zum Beenden.")
    print()
    
    question_count = 0
    
    while True:
        try:
            print_divider()
            user_input = input(f"\n{Colors.BOLD}Ihre Frage:{Colors.END} ").strip()
            
            if not user_input:
                continue
            
            input_lower = user_input.lower()
            
            # Exit-Befehle
            if input_lower in EXIT_COMMANDS:
                print()
                print(f"{Colors.CYAN}Auf Wiedersehen! Ihre Konversation wurde gespeichert.{Colors.END}")
                print(f"Session-ID: {SESSION_ID[:8]}...")
                print()
                break
            
            # Hilfe-Befehle
            if input_lower in HELP_COMMANDS:
                print(HELP_TEXT)
                continue
            
            # Status-Befehle
            if input_lower in STATUS_COMMANDS:
                print_status()
                continue
            
            # History-Befehle (NEU)
            if input_lower in HISTORY_COMMANDS:
                print_conversation_history()
                continue
            
            # Reset-Befehle (NEU)
            if input_lower in RESET_COMMANDS:
                reset_conversation()
                continue
            
            # Beispiel-Befehle
            if input_lower in EXAMPLE_COMMANDS:
                print()
                print(f"{Colors.BOLD}BEISPIELFRAGEN:{Colors.END}")
                print()
                for i, q in enumerate(EXAMPLE_QUESTIONS, 1):
                    print(f"  {Colors.CYAN}{i}.{Colors.END} {q}")
                print()
                continue
            
            # Frage an das RAG-System stellen
            question_count += 1
            print()
            print(f"{Colors.YELLOW}Verarbeite Anfrage #{question_count} (Session: {SESSION_ID[:8]}...){Colors.END}")
            
            result = ask_question(user_input)
            
            if result is None:
                print_error("System nicht verfügbar. Bitte prüfen Sie den Status mit 'status'.")
                continue
            
            if result.get("error"):
                print_error(result["error"])
                continue
            
            # Antwort ausgeben
            answer = result.get("answer", "Keine Antwort generiert.")
            sources = result.get("sources", [])
            
            print()
            print(f"{Colors.BOLD}{Colors.GREEN}ANTWORT:{Colors.END}")
            print()
            print(format_answer(answer))
            
            print_sources(sources)
            
        except KeyboardInterrupt:
            print()
            print(f"\n{Colors.YELLOW}Abbruch erkannt. Geben Sie 'exit' ein zum Beenden.{Colors.END}")
            continue
            
        except EOFError:
            print()
            print(f"\n{Colors.CYAN}Auf Wiedersehen!{Colors.END}")
            break
            
        except Exception as e:
            print_error(f"Unerwarteter Fehler: {e}")
            continue


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Haupteinstiegspunkt für das CLI."""
    if not sys.stdout.isatty():
        Colors.disable()
    
    if len(sys.argv) > 1:
        # Einzelfrage-Modus
        question = " ".join(sys.argv[1:])
        result = ask_question(question)
        
        if result is None:
            print("FEHLER: System nicht verfügbar")
            sys.exit(1)
        
        if result.get("error"):
            print(f"FEHLER: {result['error']}")
            sys.exit(1)
        
        print(result.get("answer", ""))
        
        sources = result.get("sources", [])
        if sources:
            print()
            print("QUELLEN:")
            for source in sources:
                print(f"  - {source}")
    else:
        # Interaktiver Modus
        run_interactive_loop()


if __name__ == "__main__":
    main()
