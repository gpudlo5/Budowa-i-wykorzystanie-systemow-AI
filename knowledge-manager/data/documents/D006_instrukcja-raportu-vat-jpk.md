---
doc_id: D006
title: Instrukcja przygotowania raportu VAT (JPK_V7)
doc_type: instrukcja
process_id: PR06
department_id: D02
owner_id: E003
author_id: E003
created_date: 2020-01-20
last_modified: 2026-01-12
allowed_groups: [finanse, zarzad]
related_docs: [D004, D007]
version: "3.1"
---

# Instrukcja przygotowania raportu VAT (JPK_V7)

## Cel

Instrukcja opisuje przygotowanie, kontrolę i wysyłkę miesięcznego pliku JPK_V7 z ewidencją VAT, tak aby został wysłany w terminie i bez błędów.

## Wymagania wstępne

- Zamknięte księgowania sprzedaży i zakupów za dany miesiąc w ERP Northway, moduł Finanse (S01).
- Dostęp do funkcji generowania JPK w ERP oraz do kanału wysyłki do urzędu.
- Zakończone uzgodnienia sald, jeśli wpływają na korekty VAT (patrz D005).

## Krok po kroku

1. Po zamknięciu księgowań wygeneruj z ERP (S01) wersję roboczą pliku JPK_V7 za miesiąc.
2. Sprawdź kompletność ewidencji sprzedaży i zakupów: czy numeracja faktur jest ciągła (FV/RRRR/MM/NNNN) i czy nie brakuje dokumentów.
3. Skontroluj faktury korygujące z miesiąca. Każda korekta musi mieć powiązanie z fakturą pierwotną i zatwierdzenie Głównej Księgowej.
4. Zweryfikuj oznaczenia i kody w pliku względem zestawienia kontrolnego z ERP. Różnice wyjaśnij przed wysyłką.
5. Przekaż plik do zatwierdzenia Głównej Księgowej (Katarzyna Zielińska, E002). Bez jej zatwierdzenia plik nie jest wysyłany.
6. Wyślij plik najpóźniej do 25. dnia następnego miesiąca.
7. Pobierz urzędowe poświadczenie odbioru i zapisz je w dokumentacji miesiąca.

## Najczęstsze błędy

- Wysyłka pliku przed zatwierdzeniem korekt.
- Niezgodność liczby dokumentów w ewidencji z zestawieniem kontrolnym.
- Brak poświadczenia odbioru w dokumentacji.

## Wskazówki praktyczne

- Ustaw sobie wewnętrzny termin wysyłki na 22. dzień miesiąca. Daje to bufor na poprawki i niedostępność systemu.
- Kontrolę korekt rób osobno od kontroli ewidencji. Połączone sprawdzanie sprzyja pominięciom.

## Powiązane dokumenty

- D004 Procedura fakturowania i rozliczania zleceń
- D007 Procedura zamknięcia miesiąca
