# Dokument przekazania obowiązków

## Nordwind Logistics

**Wersja:** 1.0
**Typ dokumentu:** Dokument przekazania obowiązków
**Status:** Do weryfikacji

## 1. Dane pracowników

| Pole | Informacja |
|---|---|
| Pracownik przekazujący | Anna Kowalska |
| Identyfikator | E001 |
| Dział | Finanse |
| Pracownik przejmujący | Piotr Nowak |
| Identyfikator | E002 |
| Data przekazania | Do uzupełnienia |
| Data zakończenia pracy przez przekazującego | Do uzupełnienia |

## 2. Zakres przekazywanych obowiązków

| Obowiązek | Częstotliwość | Priorytet | Uwagi |
|---|---|---|---|
| Weryfikacja faktur od dostawców | Codziennie | Wysoki | Źródło: task_id: RT001 |
| Uzgadnianie sald kontrahentów | Co miesiąc | Wysoki | Źródło: task_id: RT002 |
| Przygotowanie raportu VAT | Co miesiąc | Wysoki | Źródło: task_id: RT003 |
| Kontrola płatności dostawców | Co tydzień | Średni | Źródło: task_id: RT004 |
| Archiwizacja dokumentów finansowych | Co miesiąc | Niski | Źródło: task_id: RT005 |

## 3. Sprawy w toku

| ID zgłoszenia | Sprawa | Status | Termin | Zalecane następne działanie |
|---|---|---|---|---|
| T001 | Weryfikacja faktury FV/2026/101 | W trakcie realizacji | 2026-11-24 | Do ustalenia z przekazującym (ticket_id: T001) |
| T002 | Rozbieżność kwoty na fakturze | Otwarte | 2026-11-23 | Do ustalenia z przekazującym (ticket_id: T002) |
| T003 | Brak potwierdzenia wykonania usługi | W trakcie realizacji | 2026-11-25 | Do ustalenia z przekazującym (ticket_id: T003) |
| T004 | Przygotowanie raportu VAT | Otwarte | 2026-11-26 | Do ustalenia z przekazującym (ticket_id: T004) |
| T005 | Potwierdzenie salda kontrahenta | W trakcie realizacji | 2026-11-27 | Do ustalenia z przekazującym (ticket_id: T005) |
| T006 | Korekta danych na fakturze | Otwarte | 2026-11-28 | Do ustalenia z przekazującym (ticket_id: T006) |
| T010 | Przygotowanie danych do zamknięcia miesiąca | W trakcie realizacji | 2026-11-30 | Do ustalenia z przekazującym (ticket_id: T010) |

## 4. Kontakty i relacje biznesowe

| Klient | Osoba kontaktowa | Temat współpracy | Otwarte sprawy |
|---|---|---|---|
| TransPol Logistics | Adam Mazur | Do potwierdzenia | T001, T005, T010 |
| EuroCargo Sp. z o.o. | Ewa Nowicka | Do potwierdzenia | T002, T006 |
| Baltic Freight | Piotr Wójcik | Do potwierdzenia | T003 |
| FreshMarket Distribution | Anna Kaczmarek | Do potwierdzenia | T004 |

### Wątki komunikacyjne do przejrzenia

| ID wątku | ID zgłoszenia | Klient | Temat rozmowy | Podsumowanie | Ostatnia wiadomość | Status |
|---|---|---|---|---|---|---|
| TH001 | T001 | C001 | Weryfikacja faktury FV/2026/101 | Klient przesłał fakturę i oczekuje potwierdzenia zgodności z zamówieniem | 2026-11-20 | Otwarte |
| TH002 | T002 | C002 | Rozbieżność kwoty na fakturze | Wyjaśniana jest różnica między kwotą faktury a wartością zamówienia | 2026-11-19 | Otwarte |
| TH003 | T003 | C003 | Brak potwierdzenia wykonania usługi | Klient ma dosłać brakujące potwierdzenie wykonania usługi | 2026-11-18 | Oczekujące |
| TH004 | T004 | C004 | Przygotowanie raportu VAT | Klient oczekuje informacji o rozliczeniu dokumentów za bieżący okres | 2026-11-20 | Otwarte |
| TH005 | T005 | C001 | Potwierdzenie salda kontrahenta | Wysłano prośbę o potwierdzenie salda i oczekujemy na odpowiedź | 2026-11-17 | Otwarte |


## 5. Dokumentacja i źródła wiedzy

| ID dokumentu | Nazwa | Znaczenie | Relacja pracownika |
|---|---|---|---|
| D002 | Procedura rozliczania faktur | Faktury od dostawcow nalezy zweryfikowac z zamowieniem i potwierdzeniem wykonania uslugi. W przypadku rozbieznosci pracownik kontaktuje sie z dostawca przed zaksięgowaniem faktury. | Autor i właściciel |
| D003 | Instrukcja zamkniecia miesiaca | Zamkniecie miesiaca obejmuje uzgodnienie sald kontrahentow, weryfikacje faktur i przygotowanie raportu VAT. Proces rozpoczyna sie pierwszego dnia roboczego kolejnego miesiaca. | Autor i właściciel |

### Dokumenty dostępne dla pracownika przejmującego

| ID dokumentu | Nazwa | Dział |
|---|---|---|
| D002 | Procedura rozliczania faktur | Finanse |
| D003 | Instrukcja zamkniecia miesiaca | Finanse |


Pracownik przejmujący powinien zapoznać się z dokumentacją przed samodzielnym realizowaniem obowiązków.
Uprawnienia pracownika przejmującego sprawdzono na podstawie jego roli i wpisów w pliku ACL.

## 6. Zadania cykliczne i nadchodzące terminy


| ID | Nazwa zadania lub sprawy | Rodzaj | Częstotliwość | Termin | Priorytet |
|---|---|---|---|---|---|
| RT001 | Weryfikacja faktur od dostawców | Zadanie cykliczne | Codziennie | 2026-11-23 | Wysoki |
| RT002 | Uzgadnianie sald kontrahentów | Zadanie cykliczne | Co miesiąc | 2026-12-03 | Wysoki |
| RT003 | Przygotowanie raportu VAT | Zadanie cykliczne | Co miesiąc | 2026-12-05 | Wysoki |
| RT004 | Kontrola płatności dostawców | Zadanie cykliczne | Co tydzień | 2026-11-27 | Średni |
| RT005 | Archiwizacja dokumentów finansowych | Zadanie cykliczne | Co miesiąc | 2026-12-05 | Niski |
| T002 | Rozbieżność kwoty na fakturze | Zgłoszenie | — | 2026-11-23 | Wysoki |
| T001 | Weryfikacja faktury FV/2026/101 | Zgłoszenie | — | 2026-11-24 | Wysoki |
| T003 | Brak potwierdzenia wykonania usługi | Zgłoszenie | — | 2026-11-25 | Średni |
| T004 | Przygotowanie raportu VAT | Zgłoszenie | — | 2026-11-26 | Wysoki |
| T005 | Potwierdzenie salda kontrahenta | Zgłoszenie | — | 2026-11-27 | Średni |
| T006 | Korekta danych na fakturze | Zgłoszenie | — | 2026-11-28 | Średni |
| T010 | Przygotowanie danych do zamknięcia miesiąca | Zgłoszenie | — | 2026-11-30 | Wysoki |


## 7. Ryzyka i ważne informacje


### Sygnały wymagające uwagi

| Rodzaj | Opis | Status | Termin | Źródło |
|---|---|---|---|---|
| Zgłoszenie o wysokim priorytecie | Weryfikacja faktury FV/2026/101 | W trakcie realizacji | 2026-11-24 | ticket_id: T001 |
| Zgłoszenie o wysokim priorytecie | Rozbieżność kwoty na fakturze | Otwarte | 2026-11-23 | ticket_id: T002 |
| Zgłoszenie o wysokim priorytecie | Przygotowanie raportu VAT | Otwarte | 2026-11-26 | ticket_id: T004 |
| Zgłoszenie o wysokim priorytecie | Przygotowanie danych do zamknięcia miesiąca | W trakcie realizacji | 2026-11-30 | ticket_id: T010 |
| Projekt w trakcie realizacji | Migracja modulu fakturowania | W trakcie realizacji | Brak terminu | project_id: P001 |

### Projekty w toku

| ID projektu | Nazwa | Właściciel | Status | Opis | Źródło |
|---|---|---|---|---|---|
| P001 | Migracja modulu fakturowania | E001 | W trakcie realizacji | Przeniesienie procesu fakturowania do nowego modulu | project_id: P001 |

### Historia zakończonych zgłoszeń

| ID zgłoszenia | Sprawa | Status | Termin | Źródło |
|---|---|---|---|---|
| T008 | Archiwizacja faktur za październik | Zakończone | 2026-11-05 | ticket_id: T008 |


### Pułapki i nieoczywiste zasady

- Przed zaksięgowaniem faktury należy sprawdzić jej zgodność z zamówieniem i potwierdzeniem wykonania usługi. W przypadku rozbieżności należy skontaktować się z dostawcą przed zaksięgowaniem (źródło: D002).

- Proces zamknięcia miesiąca obejmuje uzgodnienie sald kontrahentów, weryfikację faktur i raport VAT (źródło: D003).

- W sprawie T003 oczekiwane jest potwierdzenie wykonania usługi od klienta. Należy zweryfikować, czy dokument został już dostarczony (źródła: T003, TH003).

- Pracownik przejmujący ma dostęp do D002 i D003 na podstawie przypisanej roli R_FINANCE oraz wpisów w ACL (źródło: acl.csv).

## 8. Rekomendacje dla pracownika przejmującego

1. W pierwszej kolejności przeanalizować zgłoszenia o wysokim priorytecie: T001, T002, T004 i T010.
2. Sprawdzić zgłoszenie T002, którego termin przypada na 2026-11-23.
3. W sprawie T003 zweryfikować, czy klient C003 przesłał brakujące potwierdzenie wykonania usługi (źródła: T003, TH003).
4. W sprawie T001 sprawdzić zgodność faktury FV/2026/101 z zamówieniem i potwierdzeniem wykonania usługi (źródła: T001, TH001, D002).
5. Zapoznać się z procedurą rozliczania faktur i instrukcją zamknięcia miesiąca (D002, D003).
6. Ustalić aktualny stan projektu P001 oraz uzgodnić, kto będzie odpowiedzialny za jego dalszą realizację.
7. Zweryfikować nadchodzące terminy zadań cyklicznych RT001–RT005.
8. Potwierdzić z Anną nieformalne ustalenia, kontakty z klientami i decyzje, których nie zapisano w systemie.

## 9. Potwierdzenie przekazania

| Osoba | Imię i nazwisko | Data | Podpis |
|---|---|---|---|
| Przekazujący | Anna Kowalska | | |
| Przejmujący | Piotr Nowak | | |
| Przełożony | Do uzupełnienia | | |

## 10. Informacja o wykorzystaniu AI

Dokument został przygotowany przez agenta Knowledge Manager na podstawie dostępnych danych firmowych.

Agent:
- korzysta z danych dostępnych w źródłach systemowych;
- wskazuje identyfikatory rekordów źródłowych;
- oznacza informacje brakujące jako wymagające uzupełnienia;
- nie traktuje symulowanych odpowiedzi z wywiadu jako faktów;
- nie zmienia automatycznie przypisań zadań ani zgłoszeń;

**Status dokumentu:** Wymaga weryfikacji i zatwierdzenia przez pracowników.

**Data wygenerowania (UTC):** 2026-11-25T10:23:08.463039+00:00