# Scenariusz testowy – przekazanie obowiązków Anna → Piotr

## 1. Cel testu

Celem testu jest sprawdzenie, czy agent Knowledge Manager potrafi przeprowadzić proces przekazania obowiązków od odchodzącego pracownika do pracownika przejmującego zadania.

Test obejmuje pobieranie informacji z danych firmowych, identyfikację otwartych spraw, zadań cyklicznych i powiązanych klientów, zebranie dodatkowych informacji podczas wywiadu oraz przygotowanie dokumentu przekazania.

## 2. Dane testowe

| Element | Wartość |
|---|---|
| Firma | Nordwind Logistics |
| Pracownik przekazujący | Anna Kowalska |
| ID pracownika przekazującego | E001 |
| Dział | Finanse |
| Pracownik przejmujący | Piotr Nowak |
| ID pracownika przejmującego | E002 |
| Dział | Finanse |
| Rodzaj procesu | Przekazanie obowiązków |

Wszystkie dane wykorzystane w teście są danymi syntetycznymi przygotowanymi na potrzeby projektu.

## 3. Warunki początkowe

Przed rozpoczęciem testu powinny być dostępne następujące dane:

- lista pracowników;
- lista zgłoszeń;
- lista wątków komunikacyjnych;
- lista klientów;
- lista zadań cyklicznych;
- dokumentacja firmowa;
- szablon dokumentu przekazania;
- scenariusz wywiadu z pracownikiem.

Agent powinien mieć dostęp wyłącznie do danych i dokumentów, do których uprawnia go przyjęty model dostępu.

## 4. Przebieg testu

### Etap 1 – rozpoczęcie procesu

Użytkownik uruchamia prompt `/handover` i wskazuje:

- pracownika przekazującego: E001;
- pracownika przejmującego: E002.

Oczekiwany rezultat: agent rozpoznaje Annę Kowalską i Piotra Nowaka oraz rozpoczyna przygotowanie procesu przekazania obowiązków.

### Etap 2 – zebranie informacji z systemu

Agent powinien wyszukać informacje dotyczące Anny w dostępnych zbiorach danych.

W szczególności powinien zidentyfikować:

- zgłoszenia przypisane do Anny;
- wątki komunikacyjne przypisane do Anny;
- klientów powiązanych z jej sprawami;
- zadania cykliczne przypisane do Anny;
- dokumenty i procedury związane z działem Finansów.

Oczekiwany rezultat: agent przygotowuje zestawienie informacji, które mogą mieć znaczenie dla Piotra.

### Etap 3 – identyfikacja spraw wymagających przekazania

Agent analizuje statusy zgłoszeń i zadań.

Powinien odróżnić:
- sprawy otwarte, które wymagają dalszych działań;
- sprawy zakończone, które stanowią jedynie kontekst;
- zadania cykliczne, które wymagają zmiany osoby odpowiedzialnej.

Oczekiwany rezultat: agent nie przedstawia zakończonych spraw jako nadal wymagających obsługi.

### Etap 4 – wywiad z Anną

Agent korzysta ze scenariusza `handover_interview.md` i zadaje Annie pytania dotyczące:

- codziennych obowiązków;
- otwartych spraw;
- kontaktów z klientami;
- procedur i dokumentacji;
- zadań cyklicznych;
- potencjalnych ryzyk;
- wiedzy nieformalnej, która nie została zapisana w systemie.

Oczekiwany rezultat: agent zbiera dodatkowe informacje i odróżnia odpowiedzi pracownika od danych pobranych z systemu.

### Etap 5 – przygotowanie dokumentu przekazania

Agent wykorzystuje szablon `handover_template.md` i uzupełnia go informacjami z systemu oraz wywiadu.

Dokument powinien zawierać:
- dane pracowników;
- zakres obowiązków;
- sprawy wymagające kontynuacji;
- informacje o klientach;
- dokumentację i źródła wiedzy;
- zadania cykliczne;
- ryzyka i rekomendacje;
- informacje o źródłach danych.

Oczekiwany rezultat: powstaje kompletny projekt dokumentu przekazania obowiązków dla Piotra.

### Etap 6 – weryfikacja dokumentu

Użytkownik sprawdza przygotowany dokument pod kątem:

- poprawności danych pracowników;
- zgodności zgłoszeń i zadań z danymi źródłowymi;
- kompletności informacji;
- prawidłowego wskazania statusów spraw;
- obecności źródeł informacji;
- braku informacji, których agent nie mógł potwierdzić.

Oczekiwany rezultat: dokument nie zawiera wymyślonych informacji, a dane niepotwierdzone są wyraźnie oznaczone.

## 5. Oczekiwane wyniki testu

| Kryterium | Oczekiwany wynik |
|---|---|
| Identyfikacja Anny | E001 – Anna Kowalska |
| Identyfikacja Piotra | E002 – Piotr Nowak |
| Wyszukanie zgłoszeń | Uwzględnienie zgłoszeń przypisanych do E001 |
| Wyszukanie wątków | Uwzględnienie wątków przypisanych do E001 |
| Wyszukanie zadań cyklicznych | Uwzględnienie zadań RT001–RT005 |
| Analiza statusów | Rozróżnienie spraw otwartych i zakończonych |
| Wywiad | Zadanie pytań zgodnych ze scenariuszem |
| Dokument przekazania | Wygenerowanie dokumentu na podstawie szablonu |
| Źródła informacji | Możliwość wskazania źródła istotnych danych |
| Wiarygodność | Brak nieuzasadnionych i wymyślonych informacji |

## 6. Kryteria zaliczenia

Test uznaje się za zaliczony, jeżeli:

1. Agent prawidłowo rozpoznaje pracownika przekazującego i przejmującego obowiązki.
2. Agent pobiera właściwe informacje z dostępnych danych.
3. Agent prawidłowo rozpoznaje sprawy wymagające kontynuacji.
4. Agent przeprowadza wywiad zgodnie ze scenariuszem.
5. Agent przygotowuje dokument zgodny z szablonem.
6. Agent wskazuje źródła wykorzystanych informacji.
7. Agent nie wymyśla danych ani nie przedstawia niepotwierdzonych informacji jako faktów.
8. Agent nie ujawnia danych, do których użytkownik nie ma uprawnień.

## 7. Rejestr wyników testu

Sekcja do uzupełnienia po uruchomieniu testu z wykorzystaniem serwera MCP Handover.

| Kryterium | Wynik | Uwagi |
|---|---|---|
| Identyfikacja pracowników | Do sprawdzenia | |
| Pobieranie zgłoszeń | Do sprawdzenia | |
| Pobieranie wątków | Do sprawdzenia | |
| Pobieranie zadań cyklicznych | Do sprawdzenia | |
| Analiza statusów | Do sprawdzenia | |
| Przeprowadzenie wywiadu | Do sprawdzenia | |
| Wygenerowanie dokumentu | Do sprawdzenia | |
| Wskazywanie źródeł | Do sprawdzenia | |
| Kontrola dostępu | Do sprawdzenia | |

## 8. Uwagi dotyczące ograniczeń

Test wykorzystuje syntetyczne dane przygotowane na potrzeby demonstracji projektu. Nie obejmuje rzeczywistego przekazywania uprawnień w systemach firmowych ani automatycznej zmiany właścicieli zgłoszeń i zadań.

Wygenerowany dokument jest projektem wymagającym weryfikacji i zatwierdzenia przez upoważnionego pracownika.

Test przepływu z wykorzystaniem Claude Desktop i serwera MCP zostanie wykonany po przygotowaniu i skonfigurowaniu odpowiedniego serwera.