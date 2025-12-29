"""
Retrieval-Qualitaetstest fuer das Steuerheuer RAG-System.
=========================================================

Aufgabe 4.2: Systematische Ueberpruefung der Retrieval-Qualitaet
mit 15 definierten Testfragen in 3 Schwierigkeitsstufen.

Quellen:
- Aufgabenliste S. 18-19
- Buch S. 336-339: "Test retrieval quality before moving to generation"

Metriken:
- Recall@5: (Relevante in Top-5) / (Alle Relevanten) - Ziel: >= 80%
- Precision@1: Relevante auf Platz 1 - Ziel: >= 60%
- MRR: Mean Reciprocal Rank
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

# Projekt-Root zu sys.path hinzufuegen
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retriever import retrieve_documents


@dataclass
class TestQuestion:
    """Eine Testfrage mit erwarteten Ergebnissen."""
    id: int
    category: str
    question: str
    expected_paragraphs: List[str]
    description: str


TEST_QUESTIONS = [
    # === EINFACH FAKTISCH (5) ===
    TestQuestion(1, "einfach", "Was ist der normale Umsatzsteuersatz in Deutschland?", ["§ 12"], "Steuersatz 19%"),
    TestQuestion(2, "einfach", "Wie hoch ist der ermaessigte Steuersatz?", ["§ 12"], "Ermaessigt 7%"),
    TestQuestion(3, "einfach", "Wer ist Unternehmer im Sinne des Umsatzsteuergesetzes?", ["§ 2"], "Unternehmer"),
    TestQuestion(4, "einfach", "Welche Umsaetze unterliegen der Umsatzsteuer?", ["§ 1"], "Steuerbare Umsaetze"),
    TestQuestion(5, "einfach", "Wann entsteht die Umsatzsteuer?", ["§ 13"], "Entstehung"),
    
    # === MODERAT KOMPLEX (5) ===
    TestQuestion(6, "moderat", "Wie funktioniert der Vorsteuerabzug?", ["§ 15"], "Vorsteuer"),
    TestQuestion(7, "moderat", "Wann muss ich eine Umsatzsteuervoranmeldung abgeben?", ["§ 18"], "Voranmeldung"),
    TestQuestion(8, "moderat", "Was ist die Kleinunternehmerregelung?", ["§ 19"], "Kleinunternehmer"),
    TestQuestion(9, "moderat", "Was ist die Bemessungsgrundlage fuer die Umsatzsteuer?", ["§ 10"], "Bemessung"),
    TestQuestion(10, "moderat", "Welche Leistungen sind von der Umsatzsteuer befreit?", ["§ 4"], "Befreiungen"),
    
    # === KOMPLEX / SYNTHESE (5) ===
    TestQuestion(11, "komplex", "Wie werden grenzueberschreitende Dienstleistungen besteuert?", ["§ 3a"], "Ort der Leistung"),
    TestQuestion(12, "komplex", "Wann schuldet der Leistungsempfaenger die Steuer?", ["§ 13b"], "Reverse Charge"),
    TestQuestion(13, "komplex", "Was gilt bei innergemeinschaftlichen Lieferungen?", ["§ 4", "§ 6a"], "EU-Lieferung"),
    TestQuestion(14, "komplex", "Wie wird die Steuer bei Differenzbesteuerung berechnet?", ["§ 25a"], "Differenz"),
    TestQuestion(15, "komplex", "Was sind die Aufzeichnungspflichten fuer Unternehmer?", ["§ 22"], "Aufzeichnung"),
]


def check_hit(retrieved_docs, expected_paragraphs: List[str]) -> dict:
    """Prueft ob erwartete Paragraphen in den abgerufenen Dokumenten sind."""
    found_paragraphs = []
    first_rank = None
    
    for i, doc in enumerate(retrieved_docs, 1):
        doc_paragraph = doc.metadata.get("paragraph", "")
        
        for expected in expected_paragraphs:
            if doc_paragraph == expected or doc_paragraph.startswith(expected.replace("§ ", "§")):
                if doc_paragraph not in found_paragraphs:
                    found_paragraphs.append(doc_paragraph)
                if first_rank is None:
                    first_rank = i
                break
    
    return {"hit": len(found_paragraphs) > 0, "rank": first_rank, "found_paragraphs": found_paragraphs}


def calculate_mrr(ranks: List[Optional[int]]) -> float:
    """Berechnet Mean Reciprocal Rank."""
    reciprocals = [1.0 / r if r else 0.0 for r in ranks]
    return sum(reciprocals) / len(reciprocals) if reciprocals else 0.0


def run_retrieval_tests(k: int = 5, verbose: bool = True) -> dict:
    """Fuehrt alle Testfragen durch und berechnet Metriken."""
    results = []
    
    print("=" * 70)
    print("RETRIEVAL-QUALITAETSTEST")
    print(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Anzahl Testfragen: {len(TEST_QUESTIONS)}")
    print(f"Top-K: {k}")
    print("=" * 70)
    print()
    
    for tq in TEST_QUESTIONS:
        if verbose:
            print(f"[{tq.id:02d}] {tq.category.upper()}: {tq.question[:50]}...")
        
        docs = retrieve_documents(tq.question, k=k)
        hit_info = check_hit(docs, tq.expected_paragraphs)
        
        result = {
            "id": tq.id,
            "category": tq.category,
            "question": tq.question,
            "expected": tq.expected_paragraphs,
            "hit": hit_info["hit"],
            "rank": hit_info["rank"],
            "found": hit_info["found_paragraphs"],
            "top5_paragraphs": [d.metadata.get("paragraph", "?") for d in docs]
        }
        results.append(result)
        
        status = "HIT" if hit_info["hit"] else "MISS"
        if verbose:
            print(f"     Erwartet: {tq.expected_paragraphs}")
            print(f"     Gefunden: {hit_info['found_paragraphs']} (Rang: {hit_info['rank']})")
            print(f"     Top-5: {result['top5_paragraphs']}")
            print(f"     -> {status}")
            print()
    
    hits = [r for r in results if r["hit"]]
    precision_at_1 = sum(1 for r in results if r["rank"] == 1) / len(results)
    recall_at_k = len(hits) / len(results)
    mrr = calculate_mrr([r["rank"] for r in results])
    
    by_category = {}
    for cat in ["einfach", "moderat", "komplex"]:
        cat_results = [r for r in results if r["category"] == cat]
        cat_hits = [r for r in cat_results if r["hit"]]
        by_category[cat] = {"total": len(cat_results), "hits": len(cat_hits), "recall": len(cat_hits) / len(cat_results) if cat_results else 0}
    
    metrics = {"total_questions": len(results), "total_hits": len(hits), "recall_at_k": recall_at_k, "precision_at_1": precision_at_1, "mrr": mrr, "by_category": by_category, "k": k}
    
    return {"results": results, "metrics": metrics}


def print_summary(test_results: dict):
    """Gibt eine formatierte Zusammenfassung aus."""
    metrics = test_results["metrics"]
    results = test_results["results"]
    
    print()
    print("=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print()
    print(f"Gesamt: {metrics['total_hits']}/{metrics['total_questions']} Treffer")
    print()
    print("METRIKEN:")
    print(f"  Recall@{metrics['k']}:    {metrics['recall_at_k']:.1%} (Ziel: >= 80%)")
    print(f"  Precision@1:  {metrics['precision_at_1']:.1%} (Ziel: >= 60%)")
    print(f"  MRR:          {metrics['mrr']:.3f}")
    print()
    
    recall_ok = metrics['recall_at_k'] >= 0.80
    precision_ok = metrics['precision_at_1'] >= 0.60
    
    print("STATUS:")
    print(f"  Recall@{metrics['k']}:    {'PASS' if recall_ok else 'FAIL'}")
    print(f"  Precision@1:  {'PASS' if precision_ok else 'FAIL'}")
    print()
    print("NACH KATEGORIE:")
    for cat, data in metrics["by_category"].items():
        print(f"  {cat.upper():10s}: {data['hits']}/{data['total']} ({data['recall']:.0%})")
    print()
    
    misses = [r for r in results if not r["hit"]]
    if misses:
        print("FEHLGESCHLAGEN:")
        for r in misses:
            print(f"  [{r['id']:02d}] {r['question'][:40]}...")
            print(f"       Erwartet: {r['expected']}, Bekommen: {r['top5_paragraphs']}")
    print()
    print("=" * 70)


def main():
    """Hauptfunktion."""
    print("\nStarte Retrieval-Qualitaetstest...\n")
    
    try:
        test_results = run_retrieval_tests(k=5, verbose=True)
        print_summary(test_results)
        
        metrics = test_results["metrics"]
        if metrics["recall_at_k"] >= 0.80 and metrics["precision_at_1"] >= 0.60:
            print("[OK] ALLE ZIELE ERREICHT")
            return 0
        else:
            print("[!] ZIELE NICHT VOLLSTAENDIG ERREICHT")
            return 1
            
    except Exception as e:
        print(f"[FEHLER] {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    exit(main())
