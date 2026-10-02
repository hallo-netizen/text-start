# K0 Architektur

## Zentraler Aufbau

```
Campus
└── K0
    ├── Engine
    │   ├── Intake
    │   ├── Portalprofil laden
    │   ├── Research
    │   ├── Schreiben
    │   ├── Regeln
    │   ├── Sprache
    │   ├── Fakten
    │   ├── Finalisierung
    │   └── Ausgabe
    ├── Portalprofile
    ├── Current
    └── Evidence
```

## Grundsatz

Die Engine ist genau einmal vorhanden. Ein Portal besitzt keine eigene Textmaschine.

Portalunterschiede gehören ausschließlich in ein Profil, zum Beispiel:
- Portal-ID;
- eigene Domain;
- Redaktions-/Metadatenquelle;
- interne Linkquelle;
- Ausgabeschnittstelle;
- erlaubte Artikeltypen;
- portalindividuelle Zusatzregeln.

Die Engine darf keine Portallogik anhand des Themas erraten.

## Intake

K0 verwendet einen zentralen Umschlag:

```json
{
  "contract": "K0_CENTRAL_INTAKE_V1",
  "portal_key": "portal_a",
  "item": {
    "article_type": "Beratung",
    "category": "beispiel",
    "plan_slot": "64-hex-id",
    "target_keyword": "Beispiel",
    "title": "Beispielartikel"
  },
  "publish_allowed": false
}
```

Die fünf Artikelfelder bleiben als Artikelidentität erhalten. `portal_key` liegt bewusst außerhalb der fünf Felder und bestimmt ausschließlich das Portalprofil.

## Isolation

K0 besitzt eigene Verträge, eigene Current-Autorität und eigene Tests. Fremde Produktionszustände dürfen weder gelesen noch als Fallback verwendet werden.

## Teststrategie

1. Isolationstest.
2. Positiv: zwei unterschiedliche Testportale werden mit derselben Engine korrekt geroutet.
3. Negativ: unbekanntes Portal blockiert.
4. Negativ: deaktiviertes Portal blockiert.
5. Negativ: fehlendes `portal_key` blockiert.
6. Negativ: Zusatzfelder im Artikel blockieren.
7. Negativ: `publish_allowed=true` blockiert.
8. Erst danach Aufbau der eigentlichen Textproduktion.
