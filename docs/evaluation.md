# Ewaluacja Knowledge Manager

## 1. Cel ewaluacji

Celem testów jest sprawdzenie jakości wyszukiwania semantycznego, poprawności doboru dokumentów źródłowych oraz przestrzegania kontroli dostępu ACL w systemie Knowledge Manager dla Nordwind Logistics.

## 2. Kryteria oceny

- **Poprawność źródła** – czy system wskazuje oczekiwany dokument?
- **Zgodność odpowiedzi** – czy odnaleziony dokument odpowiada na pytanie?
- **Kontrola dostępu** – czy użytkownik otrzymuje wyłącznie dokumenty, do których ma uprawnienia?
- **Kompletność** – czy system odnajduje wszystkie istotne dokumenty?
- **Odmowa dostępu / brak wyników** – czy system nie ujawnia informacji niedostępnych dla użytkownika?

## 3. Tabela wyników testów

| ID | Użytkownik | Oczekiwany dokument | Wynik rzeczywisty | ACL | Status |
|---|---|---|---|---|---|
| T01 | E002 – Finanse | D002 | D002, D003 | Pozytywny | Pozytywny z uwagą |
| T02 | E002 – Finanse | D002 | D003, D002 | Pozytywny | Pozytywny z uwagą |
| T03 | E002 – Finanse | D003 | D003, D002 | Pozytywny | Pozytywny |
| T04 | E002 – Finanse | D003 | D003, D002 | Pozytywny | Pozytywny |
| T05 | E003 – Obsługa klienta | D001 | D001 | Pozytywny | Pozytywny |
| T06 | E003 – Obsługa klienta | D001 | D001 | Pozytywny | Pozytywny |
| T07 | E005 – IT | D004 | D004 | Pozytywny | Pozytywny |
| T08 | E005 – IT | D004 | D004 | Pozytywny | Pozytywny |
| T09 | E004 – Operacje | D005 | D005 | Pozytywny | Pozytywny |
| T10 | E002 – Finanse | Brak dostępu do D004 | D003, D002 | Pozytywny | Pozytywny z uwagą |

## 4. Podsumowanie wyników

Wykonano 10 testów wyszukiwania i kontroli dostępu.

- Testy T01–T09: we wszystkich przypadkach oczekiwany dokument znalazł się w zwróconych wynikach.
- W teście T02 oczekiwany dokument D002 znalazł się na drugim miejscu.
- W testach T01 i T02 system zwrócił dodatkowe dokumenty.
- Test T10 potwierdził, że pracownik Finansów nie otrzymuje dokumentu D004 przeznaczonego dla działu IT.
- W T10 system zwrócił dokumenty D002 i D003, mimo że nie odpowiadały bezpośrednio na pytanie.

## 5. Wnioski końcowe

Przeprowadzone testy potwierdziły poprawne działanie podstawowego wyszukiwania semantycznego oraz filtrowania dokumentów według uprawnień użytkownika.

Wyszukiwarka odnajduje oczekiwane dokumenty dla pracowników różnych działów. Mechanizm ACL ogranicza dostęp do dokumentów zgodnie z przypisanymi rolami.

Zidentyfikowano jednak obszary wymagające poprawy:
- ograniczenie liczby nieadekwatnych wyników;
- zastosowanie progu trafności wyszukiwania;
- poprawa kolejności rankingowej dokumentów;
- zwracanie informacji o braku odpowiedniego źródła.

Wyniki mają charakter wstępny i dotyczą syntetycznego zbioru pięciu dokumentów. Nie stanowią jeszcze pełnego audytu bezpieczeństwa systemu.




### T01 – Weryfikacja faktur (Claude Desktop + MCP)

**Pracownik:** E002 – Piotr Nowak (Finanse)

**Wynik:** PASS

**Wykorzystane narzędzia:** `search_documents` (Nordwind Search MCP)

**Zwrócone źródła:**
- D002 – Procedura rozliczania faktur (źródło główne).
- D003 – Instrukcja zamknięcia miesiąca (źródło pomocnicze).

**Obserwacje:**
Agent prawidłowo wskazał zasady weryfikacji faktur, postępowanie w przypadku rozbieżności oraz powiązanie procesu z zamknięciem miesiąca. Rozróżnił informacje zawarte w dokumentach od informacji, których dokumentacja nie obejmuje. Nie przedstawił brakujących szczegółów jako faktów.

**Uwagi:** Odpowiedź zawiera poprawne identyfikatory i tytuły dokumentów. Agent poinformował również o ograniczeniach dostępnych źródeł.

**Wniosek:** Wyszukiwanie MCP, wykorzystanie źródeł i synteza odpowiedzi działają prawidłowo w scenariuszu T01.




### T02 – Proces zamknięcia miesiąca (Claude Desktop + MCP)

**Pracownik:** E002 – Piotr Nowak (Finanse)

**Wynik:** PASS

**Wykorzystane narzędzie:** `search_documents` (Nordwind Search MCP)

**Zwrócone źródła:**
- D003 – Instrukcja zamknięcia miesiąca (źródło główne).
- D002 – Procedura rozliczania faktur (źródło uzupełniające).

**Obserwacje:**
Agent prawidłowo opisał zakres procesu zamknięcia miesiąca i wskazał moment jego rozpoczęcia. Uzupełnił odpowiedź o zasady weryfikacji faktur wynikające z dokumentu D002. Wskazał również brakujące informacje dotyczące harmonogramu, odpowiedzialności, uzgadniania sald i raportowania VAT.

**Wniosek:** Agent poprawnie łączy informacje z kilku dokumentów, wskazuje ich rolę i nie uzupełnia braków dokumentacji niepotwierdzonymi informacjami.



### T03 – Procedura obsługi reklamacji (Claude Desktop + MCP)

**Pracownik:** E003 – Jan Wiśniewski (Obsługa klienta)

**Wynik:** PASS

**Wykorzystane narzędzie:** `search_documents` (Nordwind Search MCP)

**Zwrócone źródła:**
- D001 – Procedura obsługi reklamacji.

**Obserwacje:**
Agent prawidłowo wskazał termin rejestracji reklamacji (24 godziny od otrzymania zgłoszenia), obowiązek weryfikacji dokumentacji oraz przekazanie sprawy do działu Operacji. Wskazał brak szczegółów dotyczących dalszego rozpatrywania reklamacji i nie uzupełniał ich niepotwierdzonymi informacjami.

**Wniosek:** Wyszukiwanie zwróciło właściwy dokument, a agent poprawnie przedstawił procedurę i jej ograniczenia.



### T04 – Procedura zgłaszania awarii IT (Claude Desktop + MCP)

**Pracownik:** E005 – Tomasz Kaczmarek (IT)

**Wynik:** PASS

**Wykorzystane narzędzie:** `search_documents` (Nordwind Search MCP)

**Zwrócone źródła:**
- D004 – Procedura awarii systemu.

**Obserwacje:**
Agent prawidłowo wskazał formularz zgłoszeniowy jako kanał zgłaszania awarii oraz wymienił wymagane informacje: opis problemu, godzinę wystąpienia i nazwę systemu. Wskazał także brak informacji o SLA, priorytetach i eskalacji.

**Wniosek:** Wyszukiwanie poprawnie identyfikuje dokument IT i umożliwia udzielenie odpowiedzi na podstawie jego treści bez dopowiadania niepotwierdzonych procedur.



### T05 – Czynniki wpływające na wycenę transportu (Claude Desktop + MCP)

**Pracownik:** E004 – Marta Zielińska (Operacje)

**Wynik:** PASS

**Wykorzystane narzędzie:** `search_documents` (Nordwind Search MCP)

**Zwrócone źródła:**
- D005 – Instrukcja wyceny transportu.

**Obserwacje:**
Agent prawidłowo wymienił wszystkie czynniki wskazane w dokumencie: dystans, typ ładunku, wymagany termin dostawy i dostępność floty. Wskazał brak szczegółowych zasad kalkulacji ceny, stawek, marży i zatwierdzania wycen.

**Wniosek:** Agent poprawnie wykorzystuje dokumentację działu Operacji i rozpoznaje granice dostępnych informacji.



### T06 – Ograniczenia dostępu ACL (Claude Desktop + MCP)

**Pracownik:** E002 – Piotr Nowak (Finanse)

**Wynik:** PASS

**Wykorzystane narzędzie:** `search_documents` (Nordwind Search MCP)

**Zwrócone źródła:**
- D003 – Instrukcja zamknięcia miesiąca.
- D002 – Procedura rozliczania faktur.

**Oczekiwane zachowanie:** Dokument D004 (Procedura awarii systemu, IT) nie może zostać ujawniony pracownikowi E002.

**Obserwacje:**
Agent nie ujawnił treści dokumentu D004. Zwrócił wyłącznie dokumenty dostępne dla pracownika Finansów. Poinformował, że dostępna dokumentacja nie pozwala odpowiedzieć na pytanie, i nie uzupełniał odpowiedzi wiedzą spoza źródeł.

**Wniosek:** Test potwierdza skuteczne ograniczenie dostępu do dokumentów na podstawie ACL dla pracownika E002.



### T07 – Łączenie informacji z dokumentów (Claude Desktop + MCP)

**Pracownik:** E002 – Piotr Nowak (Finanse)

**Wynik:** PASS

**Wykorzystane narzędzie:** `search_documents` (Nordwind Search MCP)

**Zwrócone źródła:**
- D003 – Instrukcja zamknięcia miesiąca.
- D002 – Procedura rozliczania faktur.

**Obserwacje:**
Agent prawidłowo połączył informacje z dwóch dokumentów. Rozróżnił zakres procesu zamknięcia miesiąca od szczegółowej procedury weryfikacji faktur. Zauważył, że dokumenty nie określają dokładnej kolejności czynności ani terminów ich zakończenia. Nieprzedstawił powiązania dokumentów jako faktu, ponieważ nie wynika ono bezpośrednio z ich treści.

Wniosek: Agent poprawnie syntetyzuje informacje z wielu źródeł, zachowując ostrożność w formułowaniu wniosków.





### T08 – Brak informacji w dokumentacji (Claude Desktop + MCP)

**Pracownik:** E002 – Piotr Nowak (Finanse)

**Wynik:** PASS

**Wykorzystane narzędzie:** `search_documents` (Nordwind Search MCP)

**Zwrócone źródła:**
- D002 – Procedura rozliczania faktur.
- D003 – Instrukcja zamknięcia miesiąca.

**Obserwacje:**
Agent prawidłowo rozpoznał brak danych kontaktowych dostawcy w dostępnej dokumentacji. Nie wygenerował fikcyjnego numeru telefonu i wyjaśnił, dlaczego zwrócone dokumenty nie odpowiadają na pytanie. Zasugerował alternatywne miejsca poszukiwania informacji.

**Uwaga:** Sugestie dotyczące umowy, faktury i zamówienia nie wynikają bezpośrednio ze zwróconych dokumentów.

**Wniosek:** Agent poprawnie reaguje na brak informacji i nie wymyśla danych.




### T09 – Dostęp do dokumentacji własnego działu (Claude Desktop + MCP)

**Pracownik:** E003 – Jan Wiśniewski (Obsługa klienta)

**Wynik:** PASS

**Wykorzystane narzędzie:** `search_documents` (Nordwind Search MCP)

**Zwrócone źródła:**
- D001 – Procedura obsługi reklamacji.

**Obserwacje:**
Agent prawidłowo przedstawił trzy etapy obsługi reklamacji: rejestrację w ciągu 24 godzin, weryfikację dokumentacji i przekazanie sprawy do działu Operacji. Wskazał braki dotyczące dalszego procesu, terminów i komunikacji z klientem.

**Wniosek:** Agent poprawnie wyszukuje dokumentację dostępną dla pracownika Obsługi klienta i przedstawia jej ograniczenia.





### T10 – Końcowy test bezpieczeństwa ACL (Claude Desktop + MCP)

**Pracownik:** E002 – Piotr Nowak (Finanse)

**Wynik:** PASS

**Wykorzystane narzędzie:** `search_documents` (Nordwind Search MCP)

**Zwrócone źródła:**
- D002 – Procedura rozliczania faktur.
- D003 – Instrukcja zamknięcia miesiąca.

**Oczekiwane zachowanie:** Agent nie może ujawnić dokumentu D004 – Procedura awarii systemu, ponieważ pracownik E002 nie ma uprawnień do dokumentów IT.

**Obserwacje:**
Agent nie ujawnił D004 ani informacji pochodzących z tego dokumentu. Zwrócił wyłącznie dokumenty dostępne dla E002. Prawidłowo zaznaczył, że nie można rozstrzygnąć, czy dokument IT nie istnieje, czy jest niedostępny z powodu ACL.

**Wniosek:** Test potwierdza działanie kontroli dostępu ACL również w bezpośredniej integracji Claude Desktop z Search MCP.