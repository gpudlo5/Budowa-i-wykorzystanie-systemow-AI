# Northway Ltd. – szkielet firmy (dane syntetyczne)

Fikcyjna firma logistyczna. Wszystkie dane są wymyślone. Pliki CSV: UTF-8, separator przecinek, daty w formacie RRRR-MM-DD, listy identyfikatorów rozdzielone średnikiem.

| Plik | Zawartość | Wierszy |
|---|---|---|
| departments.csv | Działy i ich kierownicy | 7 |
| roles.csv | Role (stanowiska) z grupą dostępu | 20 |
| employees.csv | Pracownicy | 23 |
| projects.csv | Projekty | 3 |
| processes.csv | Procesy firmy (podstawa do generowania dokumentów) | 14 |
| systems.csv | Systemy IT firmy | 7 |
| access_groups.csv | Grupy dostępu do filtrowania uprawnień | 7 |

## Obsada działów

| Dział | Osób |
|---|---|
| Zarząd | 1 (prezes) |
| Księgowość | 3 (główna księgowa + 2 pracowników) + 1 następca (Piotr Nowak, status „nowy”) |
| HR | 2 |
| Sprzedaż | 5 |
| Operacje | 5 |
| IT | 3 |
| Obsługa klienta | 3 |

Razem 22 osoby zgodnie ze specyfikacją plus następca z scenariusza przekazania wiedzy.

## Scenariusz przekazania wiedzy

- Odchodzi: Anna Kowalska (E003), Starszy Specjalista ds. Rozliczeń, ostatni dzień pracy 2026-12-15.
- Następca: Piotr Nowak (E023), ta sama rola (R03), start 2026-12-01 (dwa tygodnie na przekazanie).
- Procesy Anny: PR03 (fakturowanie), PR05 (uzgodnienia z kontrahentami), PR06 (raport VAT); współuczestniczy w PR04 (zamknięcie miesiąca).
- Projekty Anny: P01 (w toku) i P03 (zakończony).

## Zasady spójności

- Każdy `employee_id`, `role_id`, `department_id`, `system_id` i `access_group` użyty w jednym pliku istnieje w pliku źródłowym (sprawdzone skryptem).
- Identyfikatory: E (pracownik), R (rola), D (dział), P (projekt), PR (proces), S (system).
- Dokumenty o ograniczonym dostępie w kolejnych krokach: dostęp tylko dla grup `zarzad` i `finanse`.

## Pliki planu generowania (dzień 1, część 2)

- `documents_plan.csv` – 22 dokumenty do wygenerowania (typ, autor, daty, uprawnienia, fakty, zasiane problemy).
- `prompt_templates.md` – szablony promptów do dokumentów, zgłoszeń, wątków, scenariusza wywiadu i pytań testowych, wraz z kanonem faktów, listą tematów zakazanych i kontrahentami i zadaniami cyklicznymi jako danymi stałymi.

## Dokumenty (katalog `documents/`)

22 dokumenty markdown z front-matter zgodnym z `documents_plan.csv`. Zasiane problemy: duplikaty D001–D002 i D014–D015; sprzeczności D004–D012 (termin płatności 30 vs 21 dni) i D010–D013 (limit delegacji 1500 vs 1000 zł); nieaktualne D011, D017, D019; poufne D021 i D022. Walidacja: identyfikatory, daty zatrudnienia autorów, tematy zakazane i ukryte fakty H01–H05 (brak trafień).

## Pozostałe dane (dzień 1–2)

- `tickets.json` – 30 zgłoszeń (8 prowadzonych przez Annę, w tym 2 otwarte; 4 otwarte poza nią).
- `threads.json` – 10 wątków; W01–W03 zawierają nieoczywistą wiedzę Anny (styl luźny, forumowy).
- `counterparties.csv` – 8 kontrahentów; `recurring_tasks.json` – 5 zadań cyklicznych.
- `interview_scenario.json` – scenariusz wywiadu Anny: 5 ukrytych faktów (H01–H05) z pytaniem naprowadzającym, odpowiedzią i słowami kluczowymi do weryfikacji oraz 5 pytań ogólnych.
