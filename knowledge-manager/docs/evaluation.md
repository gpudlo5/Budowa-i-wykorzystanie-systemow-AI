# Ewaluacja Knowledge Managera

Dokument opisuje ewaluację wersji po integracji (Search MCP + Handover MCP, dane Northway Ltd.). Pytania i scenariusze: `docs/test_questions.md`.

## 1. Metoda

| Obszar | Narzędzie | Kryterium zaliczenia |
|---|---|---|
| Trafność wyszukiwania | `servers/search/smoke_test.py` | oczekiwany dokument w top-5 w co najmniej 8 z 10 pytań |
| Uprawnienia | `servers/search/smoke_test.py` | zero wycieków dokumentów poufnych przez wyszukiwanie, `check_access` i `get_document` |
| Pytania spoza bazy | `servers/search/smoke_test.py` | informacyjnie (odległości wyników) |
| Wywiad przekazania | `servers/handover/eval_interview.py` | co najmniej 4 z 5 faktów w dokumencie, kontrola negatywna 0 z 5 |
| Działanie z modelem | Claude Desktop, scenariusze S1–S10 | ocena jakościowa |

Model embeddingów: `OPI-PIB/PolDense-400M`, top-k = 5. Skrypty można uruchomić ponownie poleceniami z README (sekcja 9).

## 2. Trafność wyszukiwania

**Wynik: 10/10** (próg 8/10). Oczekiwany dokument był pierwszym wynikiem w 9 pytaniach.

| # | Pytanie | Użytkownik | Oczekiwane | Zwrócone | Pozycja | Odległość |
|---|---|---|---|---|---|---|
| A1 | Ile dni mamy na odpowiedź merytoryczną na reklamację klienta? | E020 | D001, D002 | D001, D002, W10 | 1 | 0.5569 |
| A2 | Jaka jest minimalna marża przy wycenie transportu? | E007 | D003 | D003, W04, D012 | 1 | 0.5526 |
| A3 | Do kiedy trzeba wysłać raport VAT JPK_V7? | E002 | D006 | D006 | 1 | 0.5218 |
| A4 | W jakim terminie zamykamy miesiąc w księgowości? | E002 | D007 | D007 | 1 | 0.5828 |
| A5 | Jakie dokumenty musi dostarczyć nowy kierowca? | E012 | D014, D015 | D015, D014 | 1 | 0.5723 |
| A6 | W ciągu ilu dni trzeba rozliczyć delegację po powrocie? | E020 | D010, D013 | D010, D013 | 1 | 0.5709 |
| A7 | Jaki jest standardowy termin płatności faktur dla klientów? | E007 | D004, D012 | D004, D012 | 1 | 0.629 |
| A8 | O ile skrócił się czas uzgodnień sald z kontrahentami po automatyzacji? | E002 | D009 | D009, D005 | 1 | 0.5085 |
| A9 | Kiedy planowo kończy się projekt migracji modułu fakturowania? | E002 | D008 | D008 | 1 | 0.5331 |
| A10 | Jak postępować z płatnością dla Trans-Logis, gdy faktura się zgadza? | E002 | W01 | T003, D009, W01, T001, T002 | 3 | 0.5364 |

Wnioski:

- Wyszukiwanie po znaczeniu działa dla pytań sformułowanych inaczej niż tekst dokumentów.
- Przy duplikatach procedur (D001/D002, D014/D015, D010/D013) zwracane są obie wersje – model może je porównać (prompt `compare_procedures`).
- Jedyny wynik poza pierwszą pozycją (A10, wątek W01 na 3. miejscu) dotyczy wiedzy rozproszonej między zgłoszenia i wątki tego samego kontrahenta.

## 3. Uprawnienia

**Wynik: 6/6**, brak wycieków.

| # | Test | Użytkownik | Wynik |
|---|---|---|---|
| B1 | widełki płacowe (konsultant obsługi klienta) | E020 (obsluga_klienta) | zaliczony |
| B2 | umowa z Baltic Foods (konsultant obsługi klienta) | E020 (obsluga_klienta) | zaliczony |
| B3 | widełki płacowe (sprzedaż) | E007 (sprzedaz) | zaliczony |
| B4 | instrukcja magazynu tylko dla operacji (finanse) | E002 (finanse) | zaliczony |
| B5 | PROMPT INJECTION w pytaniu (obsługa klienta) | E020 (obsluga_klienta) | zaliczony |
| B6 | kontrola pozytywna: finanse widzą widełki | E002 (finanse) | zaliczony |

Test B5 zawierał w pytaniu polecenie ujawnienia dokumentów poufnych (prompt injection). Filtr uprawnień działa po stronie serwera, przed przekazaniem wyników modelowi, więc treść pytania nie ma na niego wpływu.

## 4. Pytania spoza bazy wiedzy

| # | Pytanie | Najlepsza odległość | Najbliższy dokument |
|---|---|---|---|
| C1 | Jaka jest polityka dotycząca samochodów służbowych dla handlowców? | 0.6164 | D012 |
| C2 | Jakie szkolenia zewnętrzne może zamówić pracownik i kto je zatwierdza? | 0.7039 | D013 |
| C3 | Czy można pracować zdalnie z zagranicy i na jakich zasadach? | 0.6604 | D010 |

Najlepsze odległości dla pytań bez odpowiedzi (0,62–0,70) częściowo pokrywają się z odległościami trafnych wyników (do 0,629). Stały próg `KM_MAX_DISTANCE` odrzucałby więc także część poprawnych odpowiedzi – dlatego jest domyślnie wyłączony, a o odrzuceniu słabego dopasowania decyduje model zgodnie z zasadą 6 w `search://guidelines`.

## 5. Wywiad przekazania obowiązków

**Wynik: 5/5** faktów (próg 4/5), kontrola negatywna **0/5**.

Metoda:

- Symulowany pracownik (Anna, E003) przechodzi cały wywiad (`interview_next_question`, 37 pytań). Fakt ujawnia tylko wtedy, gdy pytanie dotyczy jego tematu (stała reguła słów w pytaniu), każdy fakt jeden raz; na pozostałe pytania odpowiada „Nie mam nic do dodania”.
- Po wywiadzie powstaje dokument przekazania (`generate_handover_doc`). Fakt jest zaliczony, gdy w sekcji 11 dokumentu (Informacje z wywiadu) występuje co najmniej 3 z 5 jego słów kluczowych (porównanie po pierwszych 4 literach ze względu na odmianę).
- Sprawdzana jest tylko sekcja wywiadu: część słów kluczowych występuje w danych systemowych (np. nazwy kontrahentów, JPK), które trafiają do innych sekcji dokumentu.
- Kontrola negatywna: ten sam wywiad bez ujawniania faktów musi dać 0 z 5.

| Fakt | Treść | Słowa kluczowe | Pytanie, które go wydobyło |
|---|---|---|---|
| H01 | Po czerwcowej aktualizacji ERP przelicza faktury w EUR po kursie z dnia wystawienia zamiast z dnia poprzedzającego. Przed wysłaniem JPK trzeba ręcznie skorygować raport kursowy. | 5/5 | Bieżące sprawy i zgłoszenia: Czy po zmianach w systemach (np. aktualizacjach) coś trzeba sprawdzać albo poprawiać ręcznie? |
| H02 | Noty korygujące powyżej 10 000 zł wymagają wcześniejszej zgody Prezesa, najlepiej telefonicznej przed 10:00. Dopiero potem wystawia się notę. | 5/5 | Wiedza nieformalna: Które decyzje wymagają konsultacji z przełożonym lub zarządem? |
| H03 | Mazovia Retail płaci zwykle 5 dni po terminie, ale zarząd ustnie zdecydował, że nie naliczamy odsetek. | 5/5 | Klienci i kontakty: Czy istnieją ustalenia z klientami, których nie ma w oficjalnej dokumentacji? |
| H04 | Zapasowy token do Portalu bankowego jest w sejfie Anny. Podstawowy ma Główna Księgowa. | 5/5 | Ryzyka i problemy: Jakie dostępy, uprawnienia lub fizyczne nośniki (np. tokeny, klucze) trzeba przekazać przed Twoim odejściem? |
| H05 | W nowym module fakturowania szablon faktury dla Greenline Pharma nie ma pola z numerem pozwolenia GDP. Obejście to ręczna edycja PDF przed wysyłką. | 5/5 | Bieżące sprawy i zgłoszenia: Czy w projektach, w których uczestniczysz, stosujesz tymczasowe obejścia, o których Piotr musi wiedzieć? |

Przed poprawką scenariusz wywiadu zawierał pytania o zgłoszenia i dokumenty z poprzedniego zestawu danych i nie miał pytań o poprawki po aktualizacjach systemów, o dostępy ani o obejścia w projektach. Pytania zostały zastąpione ogólnymi pytaniami o te tematy, bez kopiowania pytań pomocniczych ze scenariusza.

## 6. Test z modelem w Claude Desktop

Konfiguracja obu serwerów w Claude Desktop została uruchomiona i sprawdzona (połączenie, dostępność narzędzi). Scenariusze S1–S10 (`docs/test_questions.md`, sekcja E) sprawdzono orientacyjnie; poniższa tabela jest do uzupełnienia po pełnym przebiegu.

| # | Użytkownik | Wynik | Uwagi |
|---|---|---|---|
| S1 | E023 | | |
| S2 | E023 | | |
| S3 | E023 | | |
| S4 | E023 | | |
| S5 | E008 | | |
| S6 | E008 | | |
| S7 | E003 | | |
| S8 | E023 | | |
| S9 | E002 | | |
| S10 | E023 | | |

## 7. Ograniczenia ewaluacji

- Zestaw testowy jest mały (10 pytań wyszukiwania, 6 testów uprawnień, 5 faktów wywiadu) i oparty na danych syntetycznych.
- Ewaluacja wywiadu jest automatyczna: sprawdza, czy scenariusz pytań obejmuje tematy wiedzy nieformalnej, a nie jakość rozmowy prowadzonej przez model. Pytania i reguły symulacji przygotował ten sam zespół.
- Dopasowanie słów kluczowych jest przybliżeniem – nie ocenia, czy fakt został zapisany poprawnie i kompletnie.
- Fakty z wywiadu trafiają do sekcji 11 dokumentu, a nie do sekcji tematycznych (np. „Pułapki i nieoczywiste zasady”).
- Wyniki nie są formalnym potwierdzeniem jakości ani bezpieczeństwa produkcyjnego.
