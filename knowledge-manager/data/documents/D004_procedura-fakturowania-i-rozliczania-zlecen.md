---
doc_id: D004
title: Procedura fakturowania i rozliczania zleceń
doc_type: procedura
process_id: PR03
department_id: D02
owner_id: E003
author_id: E003
created_date: 2019-12-02
last_modified: 2026-03-18
allowed_groups: [finanse, zarzad, sprzedaz]
related_docs: [D005, D007, D008]
version: "3.2"
---

# Procedura fakturowania i rozliczania zleceń

## 1. Cel

Procedura określa, jak w Northway Ltd. wystawiamy faktury za zlecenia transportowe i rozliczamy je po stronie księgowej, żeby każda faktura była wystawiona na czas, na właściwy podmiot i z kompletem danych potrzebnych klientowi do zapłaty.

## 2. Zakres

Dotyczy wszystkich zleceń transportowych zakończonych dostawą oraz usług dodatkowych (postój, magazynowanie), rozliczanych w ERP Northway, moduł Finanse (S01). Nie obejmuje zakupów od dostawców ani rozliczeń wewnętrznych.

## 3. Odpowiedzialności

- Starszy Specjalista ds. Rozliczeń (Anna Kowalska, E003) wystawia faktury, weryfikuje dane zleceń i prowadzi rozliczenie zleceń.
- Księgowy ds. Zobowiązań i Należności (Marek Lewandowski, E004) księguje wpłaty i dopasowuje je do faktur.
- Główna Księgowa (Katarzyna Zielińska, E002) zatwierdza faktury korygujące i wyjątki od zasad rozliczania.
- Dyspozytorzy Transportu (E013, E014) potwierdzają zakończenie zlecenia w TMS Northway Route (S02) i dostarczają potwierdzenie dostawy (POD).
- Kierownik Sprzedaży (Joanna Wójcik, E007) odpowiada za warunki handlowe uzgodnione z klientem.

## 4. Kroki

1. Potwierdzenie dostawy. Dyspozytor oznacza zlecenie jako zrealizowane w TMS Northway Route (S02) i załącza POD.
2. Weryfikacja zlecenia. W ciągu 3 dni roboczych od potwierdzenia dostawy Anna sprawdza zgodność zlecenia z wyceną i umową: stawkę, trasę, usługi dodatkowe oraz dane nabywcy.
3. Wystawienie faktury. Faktura jest wystawiana w ERP Northway (S01) w ciągu 3 dni roboczych od potwierdzenia dostawy. Numeracja ma format FV/RRRR/MM/NNNN, np. FV/2026/03/0142.
4. Rozliczenia w walucie obcej. Faktury w EUR wystawiamy po kursie NBP z dnia poprzedzającego dzień wystawienia faktury.
5. Wysyłka. Fakturę wysyłamy klientowi e-mailem na adres księgowy z umowy, z numerem zlecenia w treści wiadomości.
6. Termin płatności. Standardowy termin płatności wynosi 30 dni od daty wystawienia, chyba że umowa z klientem stanowi inaczej.
7. Rozliczenie wpłaty. Marek księguje wpłatę z Portalu bankowego (S06) i oznacza fakturę jako rozliczoną. Brak wpłaty po terminie jest zgłaszany do Anny, która kontaktuje się z klientem.
8. Korekty. Błędną fakturę korygujemy fakturą korygującą zatwierdzoną przez Główną Księgową. Nie edytujemy faktur wystawionych w poprzednich okresach.

## 5. Wyjątki i eskalacja

- Brak POD: faktury nie wystawiamy, tylko prosimy dyspozytora o dokument. Jeśli POD nie wpłynie w 3 dni, informujemy Kierownika Operacji (Robert Mazur, E012).
- Klienci kluczowi mogą mieć indywidualne warunki zapisane w umowie ramowej; przed wystawieniem faktury sprawdzamy je u właściciela relacji (Key Account Manager).
- Spory o kwotę przekazujemy do Obsługi Klienta, a po rozstrzygnięciu wystawiamy fakturę korygującą.
- Zlecenia z końca miesiąca wystawiamy zgodnie z harmonogramem zamknięcia miesiąca (D007).

## 6. Wskazówki praktyczne

- Przed wystawieniem faktury zawsze porównaj NIP nabywcy z danymi w umowie. Zmiana formy prawnej klienta jest najczęstszą przyczyną faktur korygujących.
- Numer zlecenia wpisuj w polu uwag faktury. Klienci z działami zakupów otwierają faktury właśnie po tym numerze, a bez niego odsyłają je do wyjaśnienia.
- Faktury za zlecenia z kilku dni zgrupuj tylko wtedy, gdy umowa wprost to dopuszcza. Domyślnie jedna faktura odpowiada jednemu zleceniu.

## 7. Powiązane dokumenty

- D005 Instrukcja uzgodnień sald z kontrahentami
- D007 Procedura zamknięcia miesiąca
- D008 Notatki projektowe: migracja modułu fakturowania

## 8. Historia zmian

| Wersja | Data | Zmiana |
|---|---|---|
| 1.0 | 2019-12-02 | Pierwsza wersja procedury |
| 2.0 | 2021-06-14 | Uzależnienie wystawienia faktury od POD z TMS |
| 3.0 | 2024-09-30 | Ujednolicony format numeracji i zasady rozliczeń w EUR |
| 3.2 | 2026-03-18 | Doprecyzowanie zasad korekt i terminów wystawienia |
