# Retrieval-Qualitätsbericht

**Datum:** 29-12-2025  
**Aufgabe:** 4.2 - Retrieval-Qualität testen  
**Branch:** `retrieval/qualitaet/testen`

---

## Zusammenfassung

| Metrik | Ergebnis | Ziel | Status |
|--------|----------|------|--------|
| Recall@5 | 80.0% | ≥ 80% | ✅ PASS |
| Precision@1 | 53.3% | ≥ 60% | ❌ FAIL |
| MRR | 0.656 | - | Akzeptabel |

**Gesamtergebnis:** 12/15 Treffer (80%)

---

## Ergebnisse nach Kategorie

| Kategorie | Treffer | Quote |
|-----------|---------|-------|
| EINFACH | 4/5 | 80% |
| MODERAT | 4/5 | 80% |
| KOMPLEX | 4/5 | 80% |

---

## Fehlgeschlagene Fragen

### Frage 5: "Wann entsteht die Umsatzsteuer?"
- **Erwartet:** § 13
- **Erhalten:** § 10, § 21, § 1, § 21, § 18h
- **Analyse:** Semantische Lücke - "entsteht" vs. juristische Formulierung

### Frage 10: "Welche Leistungen sind von der Umsatzsteuer befreit?"
- **Erwartet:** § 4
- **Erhalten:** § 19, § 15, § 1, § 25a, § 4b
- **Analyse:** § 4 ist eine lange Nummernliste ohne das Wort "befreit"

### Frage 11: "Wie werden grenzüberschreitende Dienstleistungen besteuert?"
- **Erwartet:** § 3a
- **Erhalten:** § 18, § 26, § 4, § 18h, § 16
- **Analyse:** "grenzüberschreitend" vs. "Ort der sonstigen Leistung"

---

## Ursachenanalyse

**Hauptproblem: Semantic Gap**

Die Nutzersprache (Alltagsdeutsch) unterscheidet sich stark von der Gesetzessprache (juristische Fachsprache):

| Nutzer sagt | Gesetz sagt |
|-------------|-------------|
| "Mehrwertsteuer" | "Umsatzsteuer" |
| "befreit" | "steuerfrei" |
| "grenzüberschreitend" | "Ort der sonstigen Leistung" |
| "Wann entsteht" | "Entstehung der Steuer" |

---

## Empfohlene Optimierungen (Post-MVP)

1. **Hybrid Search (BM25 + Vektor)** - Erwartete Verbesserung: 15-25%
2. **Query Expansion mit LLM** - Erwartete Verbesserung: 20-30%
3. **Re-Ranking mit LLM** - Erwartete Verbesserung: 30-40%

---

## Entscheidung

**Prototyp fortsetzen** - 80% Recall ist für MVP akzeptabel.

Das LLM erhält alle 5 Dokumente und kann den korrekten § selbst identifizieren.
Optimierungen werden nach Fertigstellung des Basis-Prototyps implementiert.

---

## Nächste Schritte

- [x] Aufgabe 4.1: Retriever konfigurieren
- [x] Aufgabe 4.2: Retrieval-Qualität testen
- [ ] **Phase 5: Generierung & LLM-Integration**
  - [ ] 5.1: LLM-Modell konfigurieren
  - [ ] 5.2: System-Prompt entwickeln
  - [ ] 5.3: RAG-Chain zusammenbauen

---

*Bericht erstellt basierend auf: Buch S. 336-339 "Test retrieval quality before moving to generation"*

Starte Retrieval-Qualitaetstest...

======================================================================
RETRIEVAL-QUALITAETSTEST
Datum: 2025-12-29 11:20:47
Anzahl Testfragen: 15
Top-K: 5
======================================================================

[01] EINFACH: Was ist der normale Umsatzsteuersatz in Deutschlan...
     Erwartet: ['§ 12']
     Gefunden: ['§ 12'] (Rang: 1)
     Top-5: ['§ 12', '§ 10', '§ 23a', '§ 25a', '§ 23a']
     -> HIT

[02] EINFACH: Wie hoch ist der ermaessigte Steuersatz?...
     Erwartet: ['§ 12']
     Gefunden: ['§ 12'] (Rang: 2)
     Top-5: ['§ 23a', '§ 12', '§ 16', '§ 24', '§ 23a']
     -> HIT

[03] EINFACH: Wer ist Unternehmer im Sinne des Umsatzsteuergeset...
     Erwartet: ['§ 2']
     Gefunden: ['§ 2'] (Rang: 1)
     Top-5: ['§ 2', '§ 23a', '§ 22', '§ 19', '§ 13b']
     -> HIT

[04] EINFACH: Welche Umsaetze unterliegen der Umsatzsteuer?...
     Erwartet: ['§ 1']
     Gefunden: ['§ 1'] (Rang: 2)
     Top-5: ['§ 10', '§ 1', '§ 19', '§ 25a', '§ 21']
     -> HIT

[05] EINFACH: Wann entsteht die Umsatzsteuer?...
     Erwartet: ['§ 13']
     Gefunden: [] (Rang: None)
     Top-5: ['§ 10', '§ 21', '§ 1', '§ 21', '§ 18h']
     -> MISS

[06] MODERAT: Wie funktioniert der Vorsteuerabzug?...
     Erwartet: ['§ 15']
     Gefunden: ['§ 15'] (Rang: 1)
     Top-5: ['§ 15', '§ 15', '§ 15', '§ 23a', '§ 15a']
     -> HIT

[07] MODERAT: Wann muss ich eine Umsatzsteuervoranmeldung abgebe...
     Erwartet: ['§ 18']
     Gefunden: ['§ 18'] (Rang: 2)
     Top-5: ['§ 19a', '§ 18', '§ 18b', '§ 18', '§ 18j']
     -> HIT

[08] MODERAT: Was ist die Kleinunternehmerregelung?...
     Erwartet: ['§ 19']
     Gefunden: ['§ 19'] (Rang: 3)
     Top-5: ['§ 19a', '§ 19a', '§ 19', '§ 2', '§ 15']
     -> HIT

[09] MODERAT: Was ist die Bemessungsgrundlage fuer die Umsatzste...
     Erwartet: ['§ 10']
     Gefunden: ['§ 10'] (Rang: 1)
     Top-5: ['§ 10', '§ 12', '§ 25a', '§ 28', '§ 19']
     -> HIT

[10] MODERAT: Welche Leistungen sind von der Umsatzsteuer befrei...
     Erwartet: ['§ 4']
     Gefunden: [] (Rang: None)
     Top-5: ['§ 19', '§ 15', '§ 1', '§ 25a', '§ 4b']
     -> MISS

[11] KOMPLEX: Wie werden grenzueberschreitende Dienstleistungen ...
     Erwartet: ['§ 3a']
     Gefunden: [] (Rang: None)
     Top-5: ['§ 18', '§ 26', '§ 4', '§ 18h', '§ 16']
     -> MISS

[12] KOMPLEX: Wann schuldet der Leistungsempfaenger die Steuer?...
     Erwartet: ['§ 13b']
     Gefunden: ['§ 13b'] (Rang: 1)
     Top-5: ['§ 13b', '§ 14a', '§ 27', '§ 13c', '§ 18']
     -> HIT

[13] KOMPLEX: Was gilt bei innergemeinschaftlichen Lieferungen?...
     Erwartet: ['§ 4', '§ 6a']
     Gefunden: ['§ 6a'] (Rang: 1)
     Top-5: ['§ 6a', '§ 18a', '§ 6a', '§ 3', '§ 6b']
     -> HIT

[14] KOMPLEX: Wie wird die Steuer bei Differenzbesteuerung berec...
     Erwartet: ['§ 25a']
     Gefunden: ['§ 25a'] (Rang: 1)
     Top-5: ['§ 25a', '§ 16', '§ 18', '§ 16', '§ 25a']
     -> HIT

[15] KOMPLEX: Was sind die Aufzeichnungspflichten fuer Unternehm...
     Erwartet: ['§ 22']
     Gefunden: ['§ 22'] (Rang: 1)
     Top-5: ['§ 22', '§ 22', '§ 22b', '§ 18d', '§ 22']
     -> HIT


======================================================================
ZUSAMMENFASSUNG
======================================================================

Gesamt: 12/15 Treffer

METRIKEN:
  Recall@5:    80.0% (Ziel: >= 80%)
  Precision@1:  53.3% (Ziel: >= 60%)
  MRR:          0.656

STATUS:
  Recall@5:    PASS
  Precision@1:  FAIL

NACH KATEGORIE:
  EINFACH   : 4/5 (80%)
  MODERAT   : 4/5 (80%)
  KOMPLEX   : 4/5 (80%)

FEHLGESCHLAGEN:
  [05] Wann entsteht die Umsatzsteuer?...
       Erwartet: ['§ 13'], Bekommen: ['§ 10', '§ 21', '§ 1', '§ 21', '§ 18h']
  [10] Welche Leistungen sind von der Umsatzste...
       Erwartet: ['§ 4'], Bekommen: ['§ 19', '§ 15', '§ 1', '§ 25a', '§ 4b']
  [11] Wie werden grenzueberschreitende Dienstl...
       Erwartet: ['§ 3a'], Bekommen: ['§ 18', '§ 26', '§ 4', '§ 18h', '§ 16']

======================================================================
[!] ZIELE NICHT VOLLSTAENDIG ERREICHT
