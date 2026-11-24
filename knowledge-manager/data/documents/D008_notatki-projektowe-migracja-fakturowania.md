---
doc_id: D008
title: "Notatki projektowe: migracja modułu fakturowania"
doc_type: wiki
process_id: PR03
department_id: D02
owner_id: E003
author_id: E003
created_date: 2026-06-02
last_modified: 2026-10-28
allowed_groups: [finanse, it, zarzad]
related_docs: [D004, D006]
version: "1.6"
---

# Notatki projektowe: migracja modułu fakturowania

## Kontekst

Projekt P01: przenosimy fakturowanie do nowej wersji modułu Finanse w ERP Northway (S01). Start 2026-06-01, planowany koniec 2027-02-28. Właścicielka projektu: Katarzyna Zielińska (E002). Zespół: Katarzyna Zielińska (E002), Anna Kowalska (E003), Marek Lewandowski (E004), Dominika Król (E018, IT). Notatki prowadzę na bieżąco, więc wpisy bywają skrótowe.

## Plan i etapy

1. Analiza (czerwiec do lipca 2026): spis obecnych szablonów faktur, numeracji i integracji z TMS i Portalem bankowym.
2. Konfiguracja (sierpień do października 2026): ustawienia nowego modułu, mapowanie kont, szablony dokumentów.
3. Testy równoległe (listopad 2026 do stycznia 2027): te same faktury wystawiane w starym i nowym module, porównanie wyników.
4. Przełączenie (luty 2027): przejście na nowy moduł po zamknięciu miesiąca, okres wsparcia po wdrożeniu.

## Stan na koniec października 2026

- Analiza zakończona, konfiguracja w większości gotowa.
- Numeracja FV/RRRR/MM/NNNN działa w nowym module zgodnie z procedurą (D004).
- Integracja z TMS Northway Route (S02) przetestowana na danych próbnych.
- Dominika zamknęła zgłoszenia dotyczące uprawnień użytkowników.

## Ryzyka

- Stare szablony faktur: część szablonów ma niestandardowe pola i trzeba je odtworzyć ręcznie w nowym module. Lista do przeglądu z Kierownikiem Sprzedaży.
- Czas testów równoległych zbiega się z zamknięciem roku, więc obciążenie Księgowości będzie duże.
- Zależność od okien serwisowych ERP ustalanych z IT.

## Otwarte problemy

- Różnice w zaokrągleniach VAT w nowym module względem starego. Sprawa zgłoszona dostawcy, czekamy na odpowiedź. Do czasu rozwiązania nie uruchamiamy testów dla faktur z wieloma stawkami.

## Następne kroki

- Dokończyć przegląd szablonów i podział na te do odtworzenia i te do wygaszenia.
- Ustalić z Główną Księgową harmonogram testów równoległych.
- Zaktualizować procedurę fakturowania (D004) i instrukcję raportu VAT (D006) po wyborze finalnej konfiguracji.

## Przydatne linki

- D004 Procedura fakturowania i rozliczania zleceń
- D006 Instrukcja przygotowania raportu VAT (JPK_V7)
