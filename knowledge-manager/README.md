# Knowledge Manager – Northway Ltd.

## 1. Opis projektu

Knowledge Manager to prototyp systemu zarządzania wiedzą organizacyjną dla fikcyjnej firmy logistycznej Northway Ltd. Wszystkie dane są syntetyczne.

Projekt ma dwa cele:

- **wyszukiwanie wiedzy** – pracownik zadaje pytanie po polsku i dostaje odpowiedź opartą na dokumentach, zgłoszeniach i wątkach firmy, ze wskazaniem źródeł i z uwzględnieniem swoich uprawnień;
- **przekazanie obowiązków (handover)** – gdy pracownik odchodzi, system zbiera ślad jego pracy, przeprowadza z nim wywiad o wiedzy nieformalnej i przygotowuje dokument przekazania dla następcy.

System działa jako dwa serwery Model Context Protocol (MCP) używane przez Claude Desktop.

## 2. Architektura

| Element | Rola |
|---|---|
| **Claude Desktop** | Klient LLM, z którym rozmawia pracownik. |
| **Northway Search MCP** (`servers/search/`) | Wyszukiwanie semantyczne z filtrowaniem według uprawnień, odczyt dokumentów, audyt. |
| **Northway Handover MCP** (`servers/handover/`) | Proces przekazania obowiązków: ślad pracy, wywiad, dokument, potwierdzenia, publikacja. |
| **Wspólny moduł** (`servers/common/`) | Konfiguracja (`config.py`), dane organizacji (`org.py`), wczytywanie plików (`data.py`), uprawnienia (`access.py`). |
| **ChromaDB** | Wektorowa baza fragmentów dokumentów, zgłoszeń i wątków (`data/processed/chroma_db/`). |
| **Model embeddingów** | `OPI-PIB/PolDense-400M` (sentence-transformers), polski model do wyszukiwania. |
| **Dane** (`data/`) | Syntetyczne dane firmy: CSV, JSON i dokumenty Markdown (opis w `data/README.md`). |

Oba serwery korzystają z tej samej konfiguracji i tych samych reguł uprawnień, więc wyszukiwarka i proces przekazania zawsze zgadzają się co do tego, kto co widzi.

### Search MCP

| Rodzaj | Nazwa | Opis |
|---|---|---|
| Narzędzie | `search_documents` | Wyszukiwanie semantyczne fragmentów (pytanie pełnym zdaniem po polsku); zwraca tylko to, do czego użytkownik ma dostęp. |
| Narzędzie | `get_document` | Pełna treść dokumentu, zgłoszenia lub wątku. |
| Narzędzie | `check_access` | Czy bieżący użytkownik ma dostęp do wskazanego dokumentu. |
| Narzędzie | `log_event` | Zapis własnego zdarzenia w dzienniku audytu. |
| Zasób | `search://guidelines` | Zasady wyszukiwania i odpowiadania (źródła, brak zgadywania, poufność). |
| Zasób | `search://catalog` | Lista dokumentów dostępnych dla bieżącego użytkownika (bez treści). |
| Zasób | `doc://{doc_id}` | Pełna treść dokumentu, z tymi samymi uprawnieniami co `get_document`. |
| Zasób | `org://me`, `org://processes`, `org://systems` | Profil użytkownika, procesy i systemy firmy. |
| Prompt | `ask_knowledge_base` | Odpowiedź na pytanie wyłącznie na podstawie bazy wiedzy, ze źródłami. |
| Prompt | `compare_procedures` | Porównanie różnych wersji procedury na dany temat. |
| Prompt | `onboarding_brief` | Wprowadzenie dla nowego pracownika: procesy działu i dokumenty do przeczytania. |

### Handover MCP

| Rodzaj | Nazwa | Opis |
|---|---|---|
| Narzędzia | `get_employee_info`, `get_employee_tickets`, `get_employee_threads`, `get_employee_recurring_tasks` | Dane pracownika i jego aktywność. |
| Narzędzia | `get_handover_overview`, `collect_footprint`, `extract_open_items` | Ślad pracy i sprawy wymagające uwagi. |
| Narzędzie | `interview_next_question` | Wywiad z pracownikiem przekazującym (37 pytań w 7 obszarach, z `docs/handover_interview.md`). |
| Narzędzie | `generate_handover_doc` | Dokument przekazania z danych systemowych i odpowiedzi z wywiadu. |
| Narzędzie | `confirm_handover_doc` | Potwierdzenie zapoznania się z dokumentem przez przekazującego albo przejmującego. |
| Narzędzie | `approve_handover_doc` | Zatwierdzenie dokumentu przez przełożonego przekazującego. |
| Narzędzie | `publish_to_onboarding` | Publikacja zatwierdzonego dokumentu w katalogu onboardingowym. |
| Zasób | `handover://guidelines` | Zasady procesu przekazania. |
| Prompt | `handover` | Prowadzi cały proces (domyślnie Anna Kowalska E003 → Piotr Nowak E023). |

## 3. Proces przekazania obowiązków

Scenariusz demonstracyjny: **Anna Kowalska (E003)**, Starszy Specjalista ds. Rozliczeń, odchodzi 2026-12-15. Jej obowiązki przejmuje **Piotr Nowak (E023)**. Przełożoną obojga jest **Katarzyna Zielińska (E002)**.

1. **Ślad pracy** – `collect_footprint` i `extract_open_items` zbierają dokumenty, projekty, zgłoszenia, wątki, zadania cykliczne i kontrahentów przekazującego oraz wskazują otwarte sprawy.
2. **Wywiad** – `interview_next_question` zadaje przekazującemu kolejne pytania o zakres obowiązków, bieżące sprawy, klientów, procedury, terminy, ryzyka i wiedzę nieformalną. Odpowiedzi są zapisywane w `data/processed/interviews/`.
3. **Dokument** – `generate_handover_doc` tworzy dokument według szablonu `docs/handover_template.md`. Dane z systemów mają podane źródła (ID zgłoszeń, wątków, dokumentów), a odpowiedzi z wywiadu są w osobnej sekcji jako informacje niezweryfikowane.
4. **Potwierdzenia** – przekazujący i przejmujący, każdy we własnej sesji, potwierdzają dokument narzędziem `confirm_handover_doc`.
5. **Zatwierdzenie** – przełożony przekazującego zatwierdza dokument (`approve_handover_doc`) po obu potwierdzeniach.
6. **Publikacja** – `publish_to_onboarding` sprawdza, czy przejmujący ma dostęp do wszystkich dokumentów wskazanych w przekazaniu, i publikuje dokument w `data/processed/onboarding/`.

System nie zmienia automatycznie przypisań zgłoszeń ani zadań.

## 4. Tożsamość i uprawnienia

**Użytkownik** jest ustawiany w konfiguracji serwera zmienną środowiskową `KM_USER_ID` (np. `E023`), a nie w rozmowie. Model nie może zmienić tożsamości ani działać w imieniu innej osoby. Zmiana użytkownika wymaga zmiany konfiguracji i ponownego uruchomienia Claude Desktop.

**Dostęp do dokumentów** wynika z grupy dostępu pracownika (`access_group` w `employees.csv`: `zarzad`, `finanse`, `hr`, `sprzedaz`, `operacje`, `it`, `obsluga_klienta`) i kolumny `allowed_groups` dokumentu w `documents_plan.csv`. Dokument z `all` jest dostępny dla wszystkich. Zgłoszenia i wątki są dostępne dla wszystkich. Dla brakującego dokumentu i dokumentu bez uprawnień system zwraca ten sam komunikat, żeby nie ujawniać, że dokument istnieje.

**Uprawnienia w procesie przekazania:**

| Czynność | Kto może |
|---|---|
| Przeglądanie danych i śladu pracy pracownika | on sam, jego przełożony, osoby z jego działu |
| Odpowiadanie na pytania wywiadu | tylko pracownik przekazujący |
| Potwierdzenie dokumentu | pracownik przekazujący i przejmujący (każdy za siebie) |
| Zatwierdzenie i publikacja | przełożony pracownika przekazującego |

Wyszukiwania, odczyty dokumentów i sprawdzenia dostępu są zapisywane w dzienniku audytu `data/processed/audit_log.jsonl`.

## 5. Struktura projektu

```text
knowledge-manager/
├── data/
│   ├── README.md                 # opis danych syntetycznych
│   ├── documents/                # 22 dokumenty firmowe (D001–D022, Markdown)
│   ├── documents_plan.csv        # metadane dokumentów, w tym allowed_groups
│   ├── employees.csv, roles.csv, departments.csv, access_groups.csv
│   ├── processes.csv, systems.csv, projects.csv, counterparties.csv
│   ├── tickets.json, threads.json, recurring_tasks.json
│   ├── interview_scenario.json   # fakty do ewaluacji wywiadu
│   ├── validate_data.py          # walidacja spójności danych
│   └── processed/                # pliki generowane (baza, audyt, dokumenty) – poza repozytorium
├── servers/
│   ├── common/                   # config.py, org.py, data.py, access.py
│   ├── search/
│   │   ├── server.py             # Search MCP
│   │   ├── search_engine.py      # wyszukiwanie w ChromaDB z filtrem uprawnień
│   │   ├── ingest.py             # budowa bazy wektorowej
│   │   └── smoke_test.py         # test trafności i uprawnień
│   └── handover/
│       ├── server.py             # Handover MCP
│       └── eval_interview.py     # ewaluacja wywiadu
├── docs/                         # szablon i scenariusz wywiadu, scenariusze testowe, ewaluacja
├── prompts/
│   └── handover.md               # instrukcja procesu przekazania dla modelu
├── pyproject.toml, uv.lock       # zależności (uv)
├── requirements.txt              # zależności dla pip
└── README.md
```

## 6. Wymagania

- Python 3.10 lub nowszy.
- [uv](https://docs.astral.sh/uv/) – menedżer środowiska i zależności.
- Claude Desktop.
- Połączenie z internetem przy pierwszym uruchomieniu (pobranie modelu embeddingów z Hugging Face).
- Opcjonalnie Node.js – tylko do uruchomienia MCP Inspector (`uv run mcp dev ...`).

## 7. Instalacja i przygotowanie danych

```bash
git clone https://github.com/gpudlo5/Budowa-i-wykorzystanie-systemow-AI.git
cd Budowa-i-wykorzystanie-systemow-AI/knowledge-manager
uv sync
```

`uv sync` tworzy środowisko `.venv` z wersjami zapisanymi w `uv.lock` (m.in. `mcp` 1.x – projekt nie jest zgodny z `mcp` 2.x). Wszystkie polecenia uruchamiaj z katalogu `knowledge-manager` przez `uv run`. Nowe pakiety dodawaj poleceniem `uv add`, nie `pip install`.

Alternatywnie, bez uv: `pip install -r requirements.txt` w aktywnym środowisku wirtualnym.

Następnie przygotuj dane:

```bash
uv run data/validate_data.py       # sprawdzenie spójności danych
uv run servers/search/ingest.py    # budowa bazy wektorowej w data/processed/chroma_db/
```

Bazę trzeba zbudować ponownie po każdej zmianie dokumentów albo modelu embeddingów.

## 8. Konfiguracja

### Zmienne środowiskowe

| Zmienna | Znaczenie | Domyślnie |
|---|---|---|
| `KM_USER_ID` | Pracownik, w imieniu którego działa serwer (np. `E023`). Wymagana. | brak |
| `KM_DATA_DIR` | Katalog z danymi. | `data/` |
| `KM_EMBEDDING_MODEL` | Model embeddingów (po zmianie trzeba przebudować bazę). | `OPI-PIB/PolDense-400M` |
| `KM_QUERY_PREFIX` | Przedrostek pytania wymagany przez model. | `[query]: ` |
| `KM_MAX_DISTANCE` | Opcjonalny próg odległości odrzucający słabe wyniki. | wyłączony |
| `HF_HUB_OFFLINE` | `1` = nie sprawdzaj aktualizacji modelu w Hugging Face (gdy model jest już pobrany). | – |

### Claude Desktop

Plik konfiguracyjny:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "northway-search": {
      "command": "uv",
      "args": ["--directory", "C:\\SCIEZKA\\DO\\knowledge-manager", "run", "servers/search/server.py"],
      "env": { "KM_USER_ID": "E023", "ANONYMIZED_TELEMETRY": "False" }
    },
    "northway-handover": {
      "command": "uv",
      "args": ["--directory", "C:\\SCIEZKA\\DO\\knowledge-manager", "run", "servers/handover/server.py"],
      "env": { "KM_USER_ID": "E023" }
    }
  }
}
```

- Ścieżkę zastąp rzeczywistą ścieżką do katalogu `knowledge-manager` (w systemie Windows z podwójnymi `\\`).
- Ustaw ten sam `KM_USER_ID` dla obu serwerów – w jednej sesji jesteś jedną osobą.
- Jeśli Claude Desktop nie znajduje `uv`, podaj pełną ścieżkę (`where.exe uv` w Windows, `which uv` w macOS).
- Po każdej zmianie zamknij Claude Desktop całkowicie (także z zasobnika systemowego) i uruchom ponownie.
- Plik `claude_desktop_config.json` zawiera lokalne ścieżki i jest wykluczony z repozytorium.

## 9. Testy i ewaluacja

```bash
uv run servers/search/smoke_test.py           # trafność wyszukiwania i uprawnienia (po ingest.py)
uv run servers/handover/eval_interview.py     # ewaluacja wywiadu przekazania
```

Oba skrypty kończą się kodem 0 przy zaliczeniu i zapisują wyniki w `data/processed/` (`smoke_test_results.json`, `interview_eval_results.json`).

**Search (`smoke_test.py`):**

- trafność: 10 pytań z dokumentem oczekiwanym w pierwszych 5 wynikach (próg 8/10);
- uprawnienia: 5 prób dostępu do dokumentów poufnych (w tym prompt injection w pytaniu) przez wyszukiwanie, `check_access` i `get_document` oraz kontrola pozytywna;
- pytania bez odpowiedzi w bazie: odległości najlepszych wyników, informacyjnie, do kalibracji `KM_MAX_DISTANCE`.

**Wywiad (`eval_interview.py`):** sprawdza, czy wywiad wydobywa 5 faktów (H01–H05) z `data/interview_scenario.json`, których nie ma w dokumentach, zgłoszeniach ani wątkach. Symulowany pracownik ujawnia fakt tylko wtedy, gdy pytanie dotyczy jego tematu. Fakt jest zaliczony, gdy w sekcji wywiadu dokumentu przekazania występują co najmniej 3 z 5 jego słów kluczowych. Próg: 4 z 5 faktów. Kontrola negatywna (wywiad bez ujawniania faktów) musi dać 0 z 5.

Serwery można też sprawdzić w MCP Inspector (wymaga Node.js):

```bash
uv run mcp dev servers/search/server.py
```

Zmienną `KM_USER_ID` ustaw przed uruchomieniem (PowerShell: `$env:KM_USER_ID = "E023"`, bash: `export KM_USER_ID=E023`).

### Scenariusze demonstracyjne w Claude Desktop

| Użytkownik (`KM_USER_ID`) | Scenariusz | Oczekiwany wynik |
|---|---|---|
| E023 Piotr Nowak (finanse) | „Jak rozliczyć delegację?” | Odpowiedź z D010 z datą dokumentu |
| E008 Michał Szymański (sprzedaż) | „Jakie są widełki płacowe w 2026?” | Brak odpowiedzi – D021 jest dostępny tylko dla zarządu i finansów |
| E023 | Prompt `onboarding_brief` | Procesy Księgowości i dokumenty do przeczytania |
| E003 Anna Kowalska | Prompt `handover` → wywiad → dokument → `confirm_handover_doc` | Dokument przekazania, potwierdzenie Anny |
| E023 | `confirm_handover_doc` | Potwierdzenie Piotra |
| E002 Katarzyna Zielińska | `approve_handover_doc`, `publish_to_onboarding` | Zatwierdzenie i publikacja |

## 10. Wyniki

| Test | Wynik |
|---|---|
| Trafność wyszukiwania | 10/10 (oczekiwany dokument na 1. miejscu w 9 pytaniach, na 3. w jednym) |
| Uprawnienia | 6/6, brak wycieku dokumentów poufnych, także przy próbie prompt injection |
| Wywiad przekazania | 5/5 faktów, kontrola negatywna 0/5 |

Szczegóły i wnioski: `docs/evaluation.md`. Wyniki dotyczą przygotowanego zestawu testowego i nie są formalnym potwierdzeniem jakości ani bezpieczeństwa produkcyjnego.

## 11. Ograniczenia prototypu

- Dane są syntetyczne; system nie jest połączony z rzeczywistymi systemami ERP, CRM ani zgłoszeniowymi.
- `KM_USER_ID` to konfiguracja, a nie uwierzytelnianie – kto ma dostęp do konfiguracji, może ustawić dowolnego pracownika.
- Pełny proces przekazania wymaga trzech sesji (przekazujący, przejmujący, przełożony), każda z innym `KM_USER_ID`.
- Próg odległości dla wyników wyszukiwania jest domyślnie wyłączony; przy pytaniach spoza bazy wiedzy wyniki mogą być słabo dopasowane i to model musi je odrzucić.
- Ewaluacja wywiadu jest automatyczna i oparta na słowach kluczowych: sprawdza pokrycie tematów przez scenariusz pytań, a nie jakość rozmowy prowadzonej przez model.
- Odpowiedzi z wywiadu trafiają do dokumentu jako informacje niezweryfikowane, w osobnej sekcji.

## 12. Bezpieczeństwo i prywatność

- Uprawnienia są sprawdzane po stronie serwera przy każdym wyszukiwaniu i odczycie; model nie dostaje treści dokumentów, do których użytkownik nie ma dostępu.
- Brakujący dokument i dokument bez uprawnień dają ten sam komunikat.
- Zasoby nie udostępniają pełnej listy pracowników z danymi kontaktowymi.
- Operacje są zapisywane w dzienniku audytu.
- Przed zastosowaniem produkcyjnym potrzebne jest prawdziwe uwierzytelnianie użytkowników i integracja z firmowym systemem uprawnień.

## 13. Repozytorium

https://github.com/gpudlo5/Budowa-i-wykorzystanie-systemow-AI

Projekt przygotowany w ramach pracy zespołowej dotyczącej budowy i wykorzystania systemów AI.
