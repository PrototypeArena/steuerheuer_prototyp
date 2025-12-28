"""
UStG XML Parser (v2.1)
======================
Konvertiert umsatzsteuergesetz.xml zu Document-Objekten fuer ChromaDB.

v2.1 Aenderungen:
- Token-Schwelle fuer Listen-Splitting (nur > 1000 Tokens)
- Kleine Listen-Paragraphen bleiben als EIN Document

Entscheidungen:
- Normale Paragraphen: Pro Absatz (<P>-Element mit (1), (2), ...)
- Grosse Listen-Paragraphen (> 1000 Tokens): Pro Nummer splitten
- Kleine Listen-Paragraphen: Als EIN Document behalten
"""

from lxml import etree
from pathlib import Path
import json
import re
from datetime import datetime

# === KONFIGURATION ===
MIN_TOKENS_FOR_SPLIT = 1000  # Nur Listen > 1000 Tokens werden gesplittet
CHARS_PER_TOKEN = 4  # Grobe Schaetzung fuer Deutsche Texte

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


def extract_full_text(element):
    """Extrahiert den vollstaendigen Text aus einem Element inkl. aller Kinder."""
    return ''.join(element.itertext()).strip()


def estimate_tokens(text):
    """Schaetzt die Token-Anzahl basierend auf Zeichenzahl."""
    return len(text) // CHARS_PER_TOKEN


def get_list_info(norm):
    """
    Prueft ob ein Paragraph eine Listen-Struktur hat und gibt Infos zurueck.
    
    Returns:
        dict oder None: {is_list, p_elem, dl_elem, full_text, token_estimate}
    """
    content = norm.find('.//Content')
    if content is None:
        return None
    
    p_elements = content.findall('P')
    
    # Muss genau EIN <P> Element haben
    if len(p_elements) != 1:
        return None
    
    p_elem = p_elements[0]
    full_text = extract_full_text(p_elem)
    
    # Darf KEINE Absatznummer haben
    if extract_absatz_nummer(full_text) is not None:
        return None
    
    # Muss eine DL-Liste enthalten
    dl_elem = p_elem.find('DL')
    if dl_elem is None:
        return None
    
    return {
        "is_list": True,
        "p_elem": p_elem,
        "dl_elem": dl_elem,
        "full_text": full_text,
        "token_estimate": estimate_tokens(full_text),
        "dt_count": len(dl_elem.findall('DT'))
    }


def parse_list_paragraph_split(norm, current_abschnitt, list_info):
    """
    Parst einen GROSSEN Listen-Paragraph in mehrere Documents.
    Jedes DT/DD Paar auf erster Ebene wird ein eigenes Document.
    """
    documents = []
    
    # Metadaten extrahieren
    enbez = norm.find('.//enbez')
    paragraph = enbez.text.strip() if enbez is not None and enbez.text else ""
    
    titel_elem = norm.find('.//titel')
    titel = titel_elem.text.strip() if titel_elem is not None and titel_elem.text else ""
    
    jurabk_elem = norm.find('.//jurabk')
    gesetz = jurabk_elem.text.strip() if jurabk_elem is not None and jurabk_elem.text else "UStG"
    if "UStG" in gesetz:
        gesetz = "UStG"
    
    first_dl = list_info["dl_elem"]
    
    # Iteriere ueber DT/DD Paare auf ERSTER Ebene
    dt_elements = first_dl.findall('DT')
    dd_elements = first_dl.findall('DD')
    
    for i, (dt, dd) in enumerate(zip(dt_elements, dd_elements)):
        nummer = dt.text.strip() if dt.text else f"{i+1}."
        
        # Vollstaendigen Text des DD extrahieren (inkl. Unterlisten)
        dd_text = extract_full_text(dd)
        
        # Kombiniere Nummer + Text
        full_text = f"{nummer} {dd_text}"
        
        doc = {
            "page_content": full_text,
            "metadata": {
                "gesetz": gesetz,
                "abschnitt": current_abschnitt,
                "paragraph": paragraph,
                "titel": titel,
                "absatz": nummer.rstrip('.')  # "4a." -> "4a"
            }
        }
        documents.append(doc)
    
    return documents


def parse_list_paragraph_whole(norm, current_abschnitt, list_info):
    """
    Parst einen KLEINEN Listen-Paragraph als EIN Document.
    """
    # Metadaten extrahieren
    enbez = norm.find('.//enbez')
    paragraph = enbez.text.strip() if enbez is not None and enbez.text else ""
    
    titel_elem = norm.find('.//titel')
    titel = titel_elem.text.strip() if titel_elem is not None and titel_elem.text else ""
    
    jurabk_elem = norm.find('.//jurabk')
    gesetz = jurabk_elem.text.strip() if jurabk_elem is not None and jurabk_elem.text else "UStG"
    if "UStG" in gesetz:
        gesetz = "UStG"
    
    doc = {
        "page_content": list_info["full_text"],
        "metadata": {
            "gesetz": gesetz,
            "abschnitt": current_abschnitt,
            "paragraph": paragraph,
            "titel": titel,
            "absatz": None  # Kein spezifischer Absatz
        }
    }
    
    return [doc]


def parse_normal_paragraph(norm, current_abschnitt):
    """Parst einen normalen Paragraph mit (1), (2), ... Absaetzen."""
    documents = []
    
    # Metadaten extrahieren
    enbez = norm.find('.//enbez')
    paragraph = enbez.text.strip()
    
    titel_elem = norm.find('.//titel')
    titel = titel_elem.text.strip() if titel_elem is not None and titel_elem.text else ""
    
    jurabk_elem = norm.find('.//jurabk')
    gesetz = jurabk_elem.text.strip() if jurabk_elem is not None and jurabk_elem.text else "UStG"
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


def parse_ustg(xml_path):
    """
    Parst die UStG XML-Datei und gibt eine Liste von Document-Dictionaries zurueck.
    """
    tree = etree.parse(str(xml_path))
    documents = []
    
    current_abschnitt = "Kein Abschnitt"
    
    # Statistiken
    stats = {
        "list_split": [],      # Grosse Listen-Paragraphen (gesplittet)
        "list_whole": [],      # Kleine Listen-Paragraphen (behalten)
        "normal": 0            # Normale Paragraphen
    }
    
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
        
        # Pruefe auf Listen-Struktur
        list_info = get_list_info(norm)
        
        if list_info is not None:
            # Es ist ein Listen-Paragraph
            if list_info["token_estimate"] > MIN_TOKENS_FOR_SPLIT:
                # GROSS -> Splitten
                stats["list_split"].append(f"{enbez.text} (~{list_info['token_estimate']} Tokens)")
                docs = parse_list_paragraph_split(norm, current_abschnitt, list_info)
            else:
                # KLEIN -> Als Ganzes behalten
                stats["list_whole"].append(f"{enbez.text} (~{list_info['token_estimate']} Tokens)")
                docs = parse_list_paragraph_whole(norm, current_abschnitt, list_info)
        else:
            # Normaler Paragraph
            stats["normal"] += 1
            docs = parse_normal_paragraph(norm, current_abschnitt)
        
        documents.extend(docs)
    
    # Statistiken ausgeben
    print(f"[INFO] Listen-Paragraphen GESPLITTET (> {MIN_TOKENS_FOR_SPLIT} Tokens):")
    for p in stats["list_split"]:
        print(f"       - {p}")
    print(f"[INFO] Listen-Paragraphen BEHALTEN (< {MIN_TOKENS_FOR_SPLIT} Tokens):")
    for p in stats["list_whole"]:
        print(f"       - {p}")
    print(f"[INFO] Normale Paragraphen: {stats['normal']}")
    
    return documents


def main():
    """Hauptfunktion."""
    print("=== UStG Parser v2.1 gestartet ===")
    print(f"Input:  {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Token-Schwelle fuer Splitting: {MIN_TOKENS_FOR_SPLIT}")
    print()
    
    if not INPUT_FILE.exists():
        print(f"FEHLER: Input-Datei nicht gefunden: {INPUT_FILE}")
        return
    
    print("[OK] Input-Datei gefunden")
    print("\nParsing laeuft...")
    
    documents = parse_ustg(INPUT_FILE)
    
    print(f"\n[OK] {len(documents)} Documents erstellt")
    
    # Output-Verzeichnis erstellen falls nicht vorhanden
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # JSON-Struktur mit Metadaten
    output_data = {
        "metadata": {
            "source_file": str(INPUT_FILE.name),
            "parsed_at": datetime.now().isoformat(),
            "parser_version": "2.1",
            "total_documents": len(documents),
            "granularity": "absatz_und_nummer",
            "min_tokens_for_split": MIN_TOKENS_FOR_SPLIT
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
    print(f"Documents:   {len(documents)}")
    
    # Zeige § 4 Statistik
    para4_docs = [d for d in documents if d['metadata']['paragraph'] == '§ 4']
    print(f"\n§ 4 Documents: {len(para4_docs)}")
    
    print("\n=== Parsing abgeschlossen ===")


if __name__ == "__main__":
    main()
