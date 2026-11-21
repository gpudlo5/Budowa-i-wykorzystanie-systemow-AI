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