"""
UStG XML Parser (v2.2)
======================
Konvertiert umsatzsteuergesetz.xml zu Document-Objekten fuer ChromaDB.

v2.2 Aenderungen:
- Vollstaendige Metadaten (full_reference, chunk_id, token_count)
- Praezise Token-Zaehlung mit tiktoken
- UUID fuer eindeutige Chunk-IDs

Entscheidungen:
- Normale Paragraphen: Pro Absatz (<P>-Element mit (1), (2), ...)
- Grosse Listen-Paragraphen (> 1000 Tokens): Pro Nummer splitten
- Kleine Listen-Paragraphen: Als EIN Document behalten
"""

from lxml import etree
from pathlib import Path
import json
import re
import uuid
from datetime import datetime

import tiktoken

# === KONFIGURATION ===
MIN_TOKENS_FOR_SPLIT = 1000  # Nur Listen > 1000 Tokens werden gesplittet
TIKTOKEN_MODEL = "gpt-4o-mini"  # Fuer praezise Token-Zaehlung

# === PFADE AUTOMATISCH BERECHNEN ===
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "umsatzsteuergesetz.xml"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "ustg_documents.json"

# === TIKTOKEN ENCODER (einmal initialisieren) ===
ENCODER = tiktoken.encoding_for_model(TIKTOKEN_MODEL)


def count_tokens(text):
    """Zaehlt Tokens praezise mit tiktoken."""
    return len(ENCODER.encode(text))


def extract_absatz_nummer(text):
    """Extrahiert die Absatznummer aus dem Text, z.B. '1' aus '(1) Der Umsatz...'"""
    match = re.match(r'^\((\d+[a-z]?)\)', text.strip())
    if match:
        return match.group(1)
    return None


def extract_full_text(element):
    """Extrahiert den vollstaendigen Text aus einem Element inkl. aller Kinder."""
    return ''.join(element.itertext()).strip()


def build_full_reference(gesetz, paragraph, absatz, is_nummer=False):
    """
    Erstellt die vollstaendige Rechtsreferenz.
    
    Beispiele:
    - "UStG § 1 Abs. 1"      (normaler Absatz)
    - "UStG § 4 Nr. 4a"      (Listen-Nummer)
    - "UStG § 4b"            (ohne Absatz)
    """
    if absatz is None:
        return f"{gesetz} {paragraph}"
    elif is_nummer:
        return f"{gesetz} {paragraph} Nr. {absatz}"
    else:
        return f"{gesetz} {paragraph} Abs. {absatz}"


def create_document(page_content, gesetz, abschnitt, paragraph, titel, absatz, is_nummer=False):
    """
    Erstellt ein Document-Dictionary mit allen Metadaten.
    """
    full_reference = build_full_reference(gesetz, paragraph, absatz, is_nummer)
    token_count = count_tokens(page_content)
    
    return {
        "page_content": page_content,
        "metadata": {
            "gesetz": gesetz,
            "abschnitt": abschnitt,
            "paragraph": paragraph,
            "titel": titel,
            "absatz": absatz,
            "full_reference": full_reference,
            "chunk_id": str(uuid.uuid4()),
            "token_count": token_count
        }
    }


def get_list_info(norm):
    """
    Prueft ob ein Paragraph eine Listen-Struktur hat und gibt Infos zurueck.
    """
    content = norm.find('.//Content')
    if content is None:
        return None
    
    p_elements = content.findall('P')
    
    if len(p_elements) != 1:
        return None
    
    p_elem = p_elements[0]
    full_text = extract_full_text(p_elem)
    
    if extract_absatz_nummer(full_text) is not None:
        return None
    
    dl_elem = p_elem.find('DL')
    if dl_elem is None:
        return None
    
    token_count = count_tokens(full_text)
    
    return {
        "is_list": True,
        "p_elem": p_elem,
        "dl_elem": dl_elem,
        "full_text": full_text,
        "token_count": token_count,
        "dt_count": len(dl_elem.findall('DT'))
    }


def extract_metadata(norm):
    """Extrahiert gemeinsame Metadaten aus einem norm-Element."""
    enbez = norm.find('.//enbez')
    paragraph = enbez.text.strip() if enbez is not None and enbez.text else ""
    
    titel_elem = norm.find('.//titel')
    titel = titel_elem.text.strip() if titel_elem is not None and titel_elem.text else ""
    
    jurabk_elem = norm.find('.//jurabk')
    gesetz = jurabk_elem.text.strip() if jurabk_elem is not None and jurabk_elem.text else "UStG"
    if "UStG" in gesetz:
        gesetz = "UStG"
    
    return gesetz, paragraph, titel


def parse_list_paragraph_split(norm, current_abschnitt, list_info):
    """
    Parst einen GROSSEN Listen-Paragraph in mehrere Documents.
    """
    documents = []
    gesetz, paragraph, titel = extract_metadata(norm)
    
    first_dl = list_info["dl_elem"]
    dt_elements = first_dl.findall('DT')
    dd_elements = first_dl.findall('DD')
    
    for i, (dt, dd) in enumerate(zip(dt_elements, dd_elements)):
        nummer = dt.text.strip() if dt.text else f"{i+1}."
        dd_text = extract_full_text(dd)
        full_text = f"{nummer} {dd_text}"
        
        absatz = nummer.rstrip('.')  # "4a." -> "4a"
        
        doc = create_document(
            page_content=full_text,
            gesetz=gesetz,
            abschnitt=current_abschnitt,
            paragraph=paragraph,
            titel=titel,
            absatz=absatz,
            is_nummer=True  # Listen-Nummer, nicht Absatz
        )
        documents.append(doc)
    
    return documents


def parse_list_paragraph_whole(norm, current_abschnitt, list_info):
    """
    Parst einen KLEINEN Listen-Paragraph als EIN Document.
    """
    gesetz, paragraph, titel = extract_metadata(norm)
    
    doc = create_document(
        page_content=list_info["full_text"],
        gesetz=gesetz,
        abschnitt=current_abschnitt,
        paragraph=paragraph,
        titel=titel,
        absatz=None,
        is_nummer=False
    )
    
    return [doc]


def parse_normal_paragraph(norm, current_abschnitt):
    """Parst einen normalen Paragraph mit (1), (2), ... Absaetzen."""
    documents = []
    gesetz, paragraph, titel = extract_metadata(norm)
    
    for p_elem in norm.xpath('.//P'):
        full_text = extract_full_text(p_elem)
        
        if not full_text:
            continue
        
        absatz = extract_absatz_nummer(full_text)
        
        doc = create_document(
            page_content=full_text,
            gesetz=gesetz,
            abschnitt=current_abschnitt,
            paragraph=paragraph,
            titel=titel,
            absatz=absatz,
            is_nummer=False  # Normaler Absatz
        )
        documents.append(doc)
    
    return documents


def parse_ustg(xml_path):
    """
    Parst die UStG XML-Datei und gibt eine Liste von Document-Dictionaries zurueck.
    """
    tree = etree.parse(str(xml_path))
    documents = []
    
    current_abschnitt = "Kein Abschnitt"
    
    stats = {
        "list_split": [],
        "list_whole": [],
        "normal": 0
    }
    
    for norm in tree.xpath('//norm'):
        gliederung = norm.find('.//gliederungstitel')
        if gliederung is not None and gliederung.text:
            current_abschnitt = gliederung.text.replace('\n', ' ').strip()
            continue
        
        enbez = norm.find('.//enbez')
        if enbez is None or enbez.text is None:
            continue
        if not enbez.text.startswith('§'):
            continue
        
        list_info = get_list_info(norm)
        
        if list_info is not None:
            if list_info["token_count"] > MIN_TOKENS_FOR_SPLIT:
                stats["list_split"].append(f"{enbez.text} ({list_info['token_count']} Tokens)")
                docs = parse_list_paragraph_split(norm, current_abschnitt, list_info)
            else:
                stats["list_whole"].append(f"{enbez.text} ({list_info['token_count']} Tokens)")
                docs = parse_list_paragraph_whole(norm, current_abschnitt, list_info)
        else:
            stats["normal"] += 1
            docs = parse_normal_paragraph(norm, current_abschnitt)
        
        documents.extend(docs)
    
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
    print("=== UStG Parser v2.2 gestartet ===")
    print(f"Input:  {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Token-Schwelle: {MIN_TOKENS_FOR_SPLIT}")
    print(f"Tiktoken-Modell: {TIKTOKEN_MODEL}")
    print()
    
    if not INPUT_FILE.exists():
        print(f"FEHLER: Input-Datei nicht gefunden: {INPUT_FILE}")
        return
    
    print("[OK] Input-Datei gefunden")
    print("\nParsing laeuft...")
    
    documents = parse_ustg(INPUT_FILE)
    
    print(f"\n[OK] {len(documents)} Documents erstellt")
    
    # Token-Statistiken
    token_counts = [d["metadata"]["token_count"] for d in documents]
    total_tokens = sum(token_counts)
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "metadata": {
            "source_file": str(INPUT_FILE.name),
            "parsed_at": datetime.now().isoformat(),
            "parser_version": "2.2",
            "total_documents": len(documents),
            "total_tokens": total_tokens,
            "avg_tokens_per_doc": total_tokens // len(documents),
            "max_tokens": max(token_counts),
            "min_tokens": min(token_counts),
            "granularity": "absatz_und_nummer",
            "min_tokens_for_split": MIN_TOKENS_FOR_SPLIT,
            "tiktoken_model": TIKTOKEN_MODEL
        },
        "documents": documents
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Gespeichert: {OUTPUT_FILE}")
    
    # Statistiken
    print("\n=== Statistiken ===")
    paragraphen = set(d['metadata']['paragraph'] for d in documents)
    abschnitte = set(d['metadata']['abschnitt'] for d in documents)
    print(f"Paragraphen:     {len(paragraphen)}")
    print(f"Abschnitte:      {len(abschnitte)}")
    print(f"Documents:       {len(documents)}")
    print(f"Gesamt-Tokens:   {total_tokens:,}")
    print(f"Durchschnitt:    {total_tokens // len(documents)} Tokens/Doc")
    print(f"Maximum:         {max(token_counts)} Tokens")
    print(f"Minimum:         {min(token_counts)} Tokens")
    
    # Beispiel-Document
    print("\n=== Beispiel: Erstes Document ===")
    doc = documents[0]
    for key, value in doc["metadata"].items():
        print(f"  {key}: {value}")
    
    print("\n=== Parsing abgeschlossen ===")


if __name__ == "__main__":
    main()
