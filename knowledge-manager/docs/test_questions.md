
# Knowledge Manager – zestaw pytań testowych

## Cel testów

Sprawdzenie jakości wyszukiwania semantycznego oraz kontroli
dostępu do dokumentów na podstawie ról pracowników.

## Pytania testowe

| ID | Pracownik | Pytanie | Oczekiwany dokument | Oczekiwany wynik |
|---|---|---|---|---|
| T01 | E002 – Piotr (Finanse) | Jak należy weryfikować faktury od dostawców? | D002 | Procedura rozliczania faktur |
| T02 | E002 – Piotr (Finanse) | Co należy zrobić, jeśli faktura zawiera rozbieżności względem zamówienia? | D002 | Kontakt z dostawcą przed zaksięgowaniem |
| T03 | E002 – Piotr (Finanse) | Jakie czynności obejmuje zamknięcie miesiąca? | D003 | Uzgodnienie sald, weryfikacja faktur i raport VAT |
| T04 | E002 – Piotr (Finanse) | Kiedy rozpoczyna się proces zamknięcia miesiąca? | D003 | Pierwszy dzień roboczy kolejnego miesiąca |
| T05 | E003 – Jan (Obsługa klienta) | W jakim czasie należy zarejestrować reklamację transportową? | D001 | W ciągu 24 godzin |
| T06 | E003 – Jan (Obsługa klienta) | Kto weryfikuje dokumentację reklamacyjną i komu przekazuje sprawę? | D001 | Obsługa klienta weryfikuje dokumentację i przekazuje sprawę do Operacji |
| T07 | E005 – Tomasz (IT) | Jak należy zgłosić awarię systemu? | D004 | Przez formularz zgłoszeniowy |
| T08 | E005 – Tomasz (IT) | Jakie informacje powinno zawierać zgłoszenie awarii? | D004 | Opis problemu, godzina wystąpienia i nazwa systemu |
| T09 | E004 – Marta (Operacje) | Jakie czynniki uwzględnia się przy wycenie transportu? | D005 | Dystans, typ ładunku, termin dostawy i dostępność floty |
| T10 | E002 – Piotr (Finanse) | Jak zgłosić awarię systemu IT? | BRAK DOSTĘPU DO D004 | Dokument IT nie może zostać udostępniony pracownikowi Finansów |

## Kryteria oceny

Każde pytanie oceniamy pod kątem:

1. Czy wyszukiwarka znalazła oczekiwany dokument?
2. Czy odpowiedź jest zgodna z treścią dokumentu?
3. Czy system wskazał właściwe źródło?
4. Czy system przestrzega uprawnień użytkownika?

## Ważna uwaga

Pytanie T10 jest testem bezpieczeństwa ACL.
Piotr z Finansów nie może uzyskać dostępu do dokumentu D004,
który jest przeznaczony dla pracowników IT.

Wyszukiwarka może zwrócić inne dokumenty dostępne dla Piotra,
ale nie może ujawnić treści dokumentu D004.


## Wyniki testów ACL

### Test T10 – próba dostępu do dokumentu IT przez pracownika Finansów

- Użytkownik: E002 – Piotr Nowak
- Dział: Finanse
- Pytanie: Jak zgłosić awarię systemu?
- Oczekiwany rezultat: brak dostępu do dokumentu D004.
- Rzeczywisty rezultat: zwrócono D003 i D002.
- Dokument D004 nie został zwrócony.
- Status: POZYTYWNY – kontrola ACL zadziałała.
- Uwaga: system zwrócił dwa dostępne dokumenty, które nie odpowiadają bezpośrednio na pytanie. Warto dodać próg trafności wyszukiwania.



