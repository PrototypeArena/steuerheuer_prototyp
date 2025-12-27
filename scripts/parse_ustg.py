"""
UStG XML Parser
===============
Konvertiert umsatzsteuergesetz.xml zu Document-Objekten fuer ChromaDB.

Entscheidungen:
- Granularitaet: Pro Absatz (<P>-Element)
- Metadaten: gesetz, abschnitt, paragraph, titel, absatz
- Output: JSON-Datei fuer spaetere Verarbeitung
"""

from lxml import etree
from pathlib import Path
import json
import re
from datetime import datetime

# === PFADE AUTOMATISCH BERECHNEN ===
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "umsatzsteuergesetz.xml"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "ustg_documents.json"


def extract_absatz_nummer(text):
    """Extrahiert die Absatznummer aus dem Text, z.B. '1' aus '(1) Der Umsatz...'"""
    match = re.match(r'^\((\d+[a-z]?)\)', text.strip())
    if match:
        return match.group(1)
    return None


def extract_full_text(p_element):
    """Extrahiert den vollstaendigen Text aus einem <P>-Element inkl. aller Kinder."""
    return ''.join(p_element.itertext()).strip()


def parse_ustg(xml_path):
    """
    Parst die UStG XML-Datei und gibt eine Liste von Document-Dictionaries zurueck.
    
    Returns:
        list: Liste von dicts mit 'page_content' und 'metadata'
    """
    tree = etree.parse(str(xml_path))
    documents = []
    
    current_abschnitt = "Kein Abschnitt"
    
    for norm in tree.xpath('//norm'):
        # Pruefe ob es ein Abschnitt ist (hat <gliederungstitel>)
        gliederung = norm.find('.//gliederungstitel')
        if gliederung is not None and gliederung.text:
            current_abschnitt = gliederung.text.replace('\n', ' ').strip()
            continue
        
        # Pruefe ob es ein Paragraph ist (hat <enbez> mit "§")
        enbez = norm.find('.//enbez')
        if enbez is None or enbez.text is None:
            continue
        if not enbez.text.startswith('§'):
            continue
        
        # Metadaten extrahieren
        paragraph = enbez.text.strip()
        
        titel_elem = norm.find('.//titel')
        titel = titel_elem.text.strip() if titel_elem is not None and titel_elem.text else ""
        
        jurabk_elem = norm.find('.//jurabk')
        gesetz = jurabk_elem.text.strip() if jurabk_elem is not None and jurabk_elem.text else "UStG"
        # Normalisiere: "UStG 1980" -> "UStG"
        if "UStG" in gesetz:
            gesetz = "UStG"
        
        # Alle <P>-Elemente durchgehen (= Absaetze)
        for p_elem in norm.xpath('.//P'):
            full_text = extract_full_text(p_elem)
            
            if not full_text:
                continue
            
            absatz = extract_absatz_nummer(full_text)
            
            doc = {
                "page_content": full_text,
                "metadata": {
                    "gesetz": gesetz,
                    "abschnitt": current_abschnitt,
                    "paragraph": paragraph,
                    "titel": titel,
                    "absatz": absatz
                }
            }
            documents.append(doc)
    
    return documents


def main():
    """Hauptfunktion."""
    print("=== UStG Parser gestartet ===")
    print(f"Input:  {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    
    if not INPUT_FILE.exists():
        print(f"FEHLER: Input-Datei nicht gefunden: {INPUT_FILE}")
        return
    
    print("[OK] Input-Datei gefunden")
    print("\nParsing laeuft...")
    
    documents = parse_ustg(INPUT_FILE)
    
    print(f"[OK] {len(documents)} Documents erstellt")
    
    # Output-Verzeichnis erstellen falls nicht vorhanden
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # JSON-Struktur mit Metadaten
    output_data = {
        "metadata": {
            "source_file": str(INPUT_FILE.name),
            "parsed_at": datetime.now().isoformat(),
            "parser_version": "1.0",
            "total_documents": len(documents),
            "granularity": "absatz"
        },
        "documents": documents
    }
    
    # Speichern
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Gespeichert: {OUTPUT_FILE}")
    
    # Statistiken
    print("\n=== Statistiken ===")
    paragraphen = set(d['metadata']['paragraph'] for d in documents)
    abschnitte = set(d['metadata']['abschnitt'] for d in documents)
    print(f"Paragraphen: {len(paragraphen)}")
    print(f"Abschnitte:  {len(abschnitte)}")
    print(f"Absaetze:    {len(documents)}")
    
    # Beispiel
    print("\n=== Beispiel: Erstes Document ===")
    doc = documents[0]
    print(f"Paragraph: {doc['metadata']['paragraph']}")
    print(f"Titel:     {doc['metadata']['titel']}")
    print(f"Absatz:    {doc['metadata']['absatz']}")
    print(f"Text:      {doc['page_content'][:100]}...")
    
    print("\n=== Parsing abgeschlossen ===")


if __name__ == "__main__":
    main()
