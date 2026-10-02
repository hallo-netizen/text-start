# K0 Foundation Selftest — 2026-10-02

## Scope
Centraler K0-Prototyp auf eigenem Branch. Keine Live-Produktion und kein Publish.

## Isolation
- K0 liest keine externen Produktionsrepositories.
- K0 schreibt keine externen Produktionsrepositories.
- keine Imports aus bestehenden Textmaschinen;
- eigene Current-Autorität;
- eigener Workflow;
- eigene Tests;
- eigene Testprofile.

## Testlauf
Run `36997500231`: **SUCCESS**

Positiv:
- Alpha-Testportal über dieselbe Engine geroutet: PASS
- Beta-Testportal über dieselbe Engine geroutet: PASS

Negativ:
- unbekanntes Portal: BLOCK
- deaktiviertes Portal: BLOCK
- fehlender portal_key: BLOCK
- Zusatzfeld in Artikelidentität: BLOCK
- publish_allowed=true: BLOCK
- nicht erlaubter Artikeltyp: BLOCK

## Vorlauf
Run `36997439522` blockierte wegen eines Selbsttreffers des Isolation-Guards: seine eigene Deny-Liste wurde als Laufzeitreferenz erkannt. Der Guard wurde ausschließlich so korrigiert, dass er sich selbst nicht auf seine Deny-Liste prüft. Danach vollständiger PASS.

## Nicht-Mutation
`text-start/main` blieb unverändert.
Bestehende externe Maschinenbranches wurden nicht beschrieben oder verändert.
