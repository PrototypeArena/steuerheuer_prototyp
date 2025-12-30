#!/usr/bin/env python3
"""
Steuerheuer CLI - Interaktives Command-Line Interface.
=======================================================

Aufgabe 7.1: CLI-Interface erstellen

Dieses Skript stellt eine interaktive Kommandozeilen-Schnittstelle
fuer das Steuerheuer RAG-System bereit.

Quellen:
- Aufgabenliste S. 897-916 (Phase 7: Benutzeroberflaeche)
- Buch S. 147: "Source attribution explicitly connects generated 
  information to the retrieved sources."

Verwendung:
    python scripts/cli.py
    
    # Oder direkt aus dem Projektverzeichnis:
    python -m scripts.cli

Features:
    - Kontinuierliche Frage-Antwort-Schleife
    - Formatierte Antworten mit Quellenangaben
    - Exit-Befehle: "exit", "quit", "q", "beenden"
    - Hilfe-Befehl: "hilfe", "help", "?"
    - Status-Befehl: "status"
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Projekt-Root zu sys.path hinzufuegen
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# ANSI FARB-CODES (fuer farbige Terminal-Ausgabe)
# =============================================================================

class Colors:
    """ANSI Escape-Codes fuer Terminal-Farben."""
    HEADER = '\033[95m'      # Magenta
    BLUE = '\033[94m'        # Blau
    CYAN = '\033[96m'        # Cyan
    GREEN = '\033[92m'       # Gruen
    YELLOW = '\033[93m'      # Gelb
    RED = '\033[91m'         # Rot
    BOLD = '\033[1m'         # Fett
    UNDERLINE = '\033[4m'    # Unterstrichen
    END = '\033[0m'          # Reset

    @classmethod
    def disable(cls):
        """Deaktiviert Farben (z.B. fuer nicht-interaktive Terminals)."""
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
# CLI KONSTANTEN
# =============================================================================

BANNER = f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   {Colors.BOLD}STEUERHEUER{Colors.END}{Colors.CYAN} - UStG RAG-Assistent                               ║
║                                                                       ║
║   Ihr intelligenter Assistent fuer das deutsche Umsatzsteuergesetz   ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝{Colors.END}
"""

HELP_TEXT = f"""
{Colors.BOLD}VERFUEGBARE BEFEHLE:{Colors.END}

  {Colors.GREEN}[Ihre Frage]{Colors.END}    Stellen Sie eine Frage zum Umsatzsteuergesetz
  
  {Colors.YELLOW}hilfe, help, ?{Colors.END}  Diese Hilfe anzeigen
  {Colors.YELLOW}status{Colors.END}          System-Status anzeigen
  {Colors.YELLOW}beispiele{Colors.END}       Beispielfragen anzeigen
  {Colors.YELLOW}exit, quit, q{Colors.END}   Programm beenden

{Colors.BOLD}BEISPIELFRAGEN:{Colors.END}

  • Wie hoch ist der normale Umsatzsteuersatz?
  • Was ist die Kleinunternehmerregelung?
  • Wie funktioniert der Vorsteuerabzug?
  • Wann muss ich eine Umsatzsteuervoranmeldung abgeben?

{Colors.CYAN}Hinweis: Die Antworten basieren ausschliesslich auf dem UStG.
Fuer individuelle Beratung wenden Sie sich an einen Steuerberater.{Colors.END}
"""

EXAMPLE_QUESTIONS = [
    "Wie hoch ist der normale Umsatzsteuersatz in Deutschland?",
    "Was ist die Kleinunternehmerregelung?",
    "Wie funktioniert der Vorsteuerabzug?",
    "Wann muss ich eine Umsatzsteuervoranmeldung abgeben?",
    "Welche Umsaetze sind steuerfrei?",
]

EXIT_COMMANDS = {"exit", "quit", "q", "beenden", "ende"}
HELP_COMMANDS = {"hilfe", "help", "?", "h"}
STATUS_COMMANDS = {"status", "info"}
EXAMPLE_COMMANDS = {"beispiele", "beispiel", "examples"}


# =============================================================================
# FORMATIERUNGS-FUNKTIONEN
# =============================================================================

def print_divider(char: str = "─", length: int = 70):
    """Gibt eine Trennlinie aus."""
    print(f"{Colors.CYAN}{char * length}{Colors.END}")


def format_answer(answer: str) -> str:
    """Formatiert die Antwort fuer die Ausgabe."""
    # Zeilenumbrueche bei langen Zeilen
    lines = answer.split('\n')
    formatted_lines = []
    for line in lines:
        formatted_lines.append(line)
    return '\n'.join(formatted_lines)


def print_sources(sources: list):
    """Gibt die Quellenangaben formatiert aus."""
    if not sources:
        return
    
    print()
    print(f"{Colors.BOLD}{Colors.BLUE}QUELLEN:{Colors.END}")
    
    # Duplikate entfernen, Reihenfolge beibehalten
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
# SYSTEM-STATUS
# =============================================================================

def get_system_status() -> Dict[str, Any]:
    """
    Sammelt Informationen ueber den System-Status.
    
    Returns:
        dict: Status-Informationen
    """
    status = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "graph_ready": False,
        "vectorstore_ready": False,
        "llm_ready": False,
        "document_count": 0,
        "errors": [],
    }
    
    try:
        from src.graph import create_rag_graph
        graph = create_rag_graph()
        status["graph_ready"] = True
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
    
    # Status-Anzeige
    graph_status = f"{Colors.GREEN}✓{Colors.END}" if status["graph_ready"] else f"{Colors.RED}✗{Colors.END}"
    vs_status = f"{Colors.GREEN}✓{Colors.END}" if status["vectorstore_ready"] else f"{Colors.RED}✗{Colors.END}"
    llm_status = f"{Colors.GREEN}✓{Colors.END}" if status["llm_ready"] else f"{Colors.RED}✗{Colors.END}"
    
    print(f"  {graph_status} LangGraph Workflow")
    print(f"  {vs_status} ChromaDB VectorStore ({status['document_count']} Dokumente)")
    print(f"  {llm_status} LLM ({status.get('llm_model', 'N/A')})")
    print()
    print(f"  Zeitstempel: {status['timestamp']}")
    
    if status["errors"]:
        print()
        print(f"{Colors.RED}FEHLER:{Colors.END}")
        for error in status["errors"]:
            print(f"  • {error}")
    
    print_divider()
    print()


# =============================================================================
# HAUPT-ABFRAGE-FUNKTION
# =============================================================================

def ask_question(question: str) -> Optional[Dict[str, Any]]:
    """
    Stellt eine Frage an das RAG-System.
    
    Args:
        question: Die Benutzerfrage
        
    Returns:
        dict: Ergebnis mit 'answer', 'sources', 'error'
        None: Bei kritischem Fehler
    """
    try:
        from src.graph import ask_graph
        
        result = ask_graph(question)
        return result
        
    except ImportError as e:
        print_error(f"Modul konnte nicht geladen werden: {e}")
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
    Hauptschleife fuer interaktive Frage-Antwort-Sitzung.
    
    Diese Funktion implementiert:
    - Kontinuierliche Eingabe-Schleife
    - Formatierte Ausgabe mit Quellen
    - Befehlserkennung (exit, help, status)
    
    Quelle: Aufgabenliste S. 897-916
    """
    # Banner anzeigen
    print(BANNER)
    print(f"Geben Sie {Colors.GREEN}'hilfe'{Colors.END} ein fuer verfuegbare Befehle.")
    print(f"Geben Sie {Colors.YELLOW}'exit'{Colors.END} ein zum Beenden.")
    print()
    
    # Frage-Zaehler
    question_count = 0
    
    while True:
        try:
            # Eingabe-Prompt
            print_divider()
            user_input = input(f"\n{Colors.BOLD}Ihre Frage:{Colors.END} ").strip()
            
            # Leere Eingabe ignorieren
            if not user_input:
                continue
            
            # Kleinbuchstaben fuer Befehlserkennung
            input_lower = user_input.lower()
            
            # Exit-Befehle
            if input_lower in EXIT_COMMANDS:
                print()
                print(f"{Colors.CYAN}Auf Wiedersehen! Vielen Dank fuer die Nutzung von Steuerheuer.{Colors.END}")
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
            print(f"{Colors.YELLOW}Verarbeite Anfrage #{question_count}...{Colors.END}")
            
            result = ask_question(user_input)
            
            if result is None:
                print_error("System nicht verfuegbar. Bitte pruefen Sie den Status mit 'status'.")
                continue
            
            # Fehler behandeln
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
            
            # Quellen ausgeben
            print_sources(sources)
            
        except KeyboardInterrupt:
            # Ctrl+C behandeln
            print()
            print(f"\n{Colors.YELLOW}Abbruch erkannt. Geben Sie 'exit' ein zum Beenden.{Colors.END}")
            continue
            
        except EOFError:
            # Ctrl+D behandeln
            print()
            print(f"\n{Colors.CYAN}Auf Wiedersehen!{Colors.END}")
            break
            
        except Exception as e:
            print_error(f"Unerwarteter Fehler: {e}")
            continue


# =============================================================================
# EINZELFRAGE-MODUS (fuer Scripting)
# =============================================================================

def run_single_query(question: str):
    """
    Fuehrt eine einzelne Anfrage aus (nicht-interaktiver Modus).
    
    Args:
        question: Die Benutzerfrage
    """
    result = ask_question(question)
    
    if result is None:
        print("FEHLER: System nicht verfuegbar")
        sys.exit(1)
    
    if result.get("error"):
        print(f"FEHLER: {result['error']}")
        sys.exit(1)
    
    # Ausgabe im einfachen Format
    print(result.get("answer", ""))
    
    sources = result.get("sources", [])
    if sources:
        print()
        print("QUELLEN:")
        for source in sources:
            print(f"  - {source}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """
    Haupteinstiegspunkt fuer das CLI.
    
    Unterstuetzt zwei Modi:
    1. Interaktiv (ohne Argumente): Kontinuierliche Frage-Antwort-Schleife
    2. Einzelfrage (mit Argument): Beantwortet eine Frage und beendet
    
    Verwendung:
        # Interaktiver Modus
        python cli.py
        
        # Einzelfrage-Modus
        python cli.py "Wie hoch ist der Umsatzsteuersatz?"
    """
    # Farbunterstuetzung pruefen
    if not sys.stdout.isatty():
        Colors.disable()
    
    # Argumente pruefen
    if len(sys.argv) > 1:
        # Einzelfrage-Modus
        question = " ".join(sys.argv[1:])
        run_single_query(question)
    else:
        # Interaktiver Modus
        run_interactive_loop()


if __name__ == "__main__":
    main()
