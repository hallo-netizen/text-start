# K0 Real Multi-Portal Proof — 2026-10-02

## Ergebnis
Die zentrale K0-Engine wurde mit drei echten, fachlich stark unterschiedlichen Artikeln geprüft.

### Positiv 1 — Hobby Depot
- Thema: Was braucht man für Linolschnitt?
- echte Quellen: V&A, MoMA, The Met
- Run: 37000206164
- Artifact: 11222869632
- Ergebnis: READY_FOR_OUTPUT
- 609 Wörter, 5 H2, 9 Absätze

### Positiv 2 — Gaumen Atelier
- Thema: Was ist der Unterschied zwischen Arabica und Robusta?
- echte Quellen: Kew und International Coffee Organization
- Run: 37000210695
- Artifact: 11223171526
- Ergebnis: READY_FOR_OUTPUT
- 557 Wörter, 5 H2, 9 Absätze

### Positiv 3 — Neutraler Fremdthemen-Test
- Thema: Warum schwimmt Eis auf Wasser?
- echte Quellen: U.S. Geological Survey, Yale, Lunar and Planetary Institute
- Run: 37000216234
- Artifact: 11223761177
- Ergebnis: READY_FOR_OUTPUT
- 557 Wörter, 5 H2, 9 Absätze

## Negativ
Ein naturwissenschaftlicher Artikel wurde absichtlich dem Portal gaumenatelier zugewiesen.
- Run: 37000387358
- erwarteter Block: CATEGORY_NOT_ALLOWED_FOR_PORTAL:naturwissenschaft
- Harness: K0_NEGATIVE_EXPECTED_BLOCK_PASS

## Isolation
K0 verwendet ausschließlich K0-eigene Engine-, Profil-, Current-, Test- und Run-Dateien.
Kein K9-/K10-Modul wird importiert oder aufgerufen.
Publish bleibt false.

## Aussagekraft
Bewiesen ist die zentrale Portalarchitektur und ihre Isolation.
Noch nicht bewiesen ist eine vollautonome Produktion ab bloßem Upload: Research- und Artikelpakete wurden für diese Proof-Läufe real erstellt und danach durch K0 validiert/finalisiert.
Der nächste Schritt ist deshalb die K0-eigene Automatisierung von Upload -> Research -> Write -> Check -> Output.
