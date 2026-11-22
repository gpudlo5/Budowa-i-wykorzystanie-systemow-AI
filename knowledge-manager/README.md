# Knowledge Manager – Nordwind Logistics

## 1. Opis projektu

Knowledge Manager to prototyp systemu zarządzania wiedzą organizacyjną dla fikcyjnej firmy Nordwind Logistics.

Celem projektu jest ułatwienie pracownikom wyszukiwania informacji w dokumentacji firmowej oraz wspieranie procesu przekazywania obowiązków pomiędzy pracownikami.

System wykorzystuje architekturę agentową, model językowy (LLM) oraz protokół Model Context Protocol (MCP).

Główne funkcjonalności:
- semantyczne wyszukiwanie dokumentów firmowych,
- kontrola dostępu do dokumentów na podstawie ról pracowników (ACL),
- prezentowanie odpowiedzi wraz z identyfikatorami źródeł,
- pobieranie informacji o obowiązkach i zadaniach pracownika,
- wspieranie procesu przekazywania obowiązków (handover).

Projekt ma charakter demonstracyjny i wykorzystuje syntetyczne dane.

## 2. Architektura systemu

Projekt składa się z następujących elementów:

- **Claude Desktop** – klient LLM wykorzystywany do interakcji z systemem.
- **Nordwind Search MCP** – serwer odpowiedzialny za semantyczne wyszukiwanie dokumentów i filtrowanie wyników według uprawnień ACL.
- **Nordwind Handover MCP** – serwer udostępniający informacje potrzebne do przekazania obowiązków.
- **ChromaDB** – wektorowa baza danych przechowująca reprezentacje dokumentów.
- **Sentence Transformers** – model embeddingowy `paraphrase-multilingual-MiniLM-L12-v2`.
- **CSV** – źródło syntetycznych danych organizacyjnych.

### Serwer Search MCP

Udostępnia narzędzie:
- `search_documents` – wyszukuje dokumenty semantycznie, uwzględniając uprawnienia pracownika.

Udostępnia również zasób:
- `search://guidelines` – wytyczne dotyczące wyszukiwania dokumentów.

### Serwer Handover MCP

Udostępnia pięć narzędzi:
- `get_employee_info`
- `get_employee_tickets`
- `get_employee_threads`
- `get_employee_recurring_tasks`
- `get_handover_overview`

Udostępnia zasób:
- `handover://guidelines`

Udostępnia prompt:
- `handover` – wspiera przygotowanie procesu przekazania obowiązków pomiędzy pracownikami.

## 3. Struktura projektu

```text
knowledge-manager/
├── data/
│   ├── raw/
│   │   ├── employees.csv
│   │   ├── projects.csv
│   │   ├── documents.csv
│   │   ├── acl.csv
│   │   ├── clients.csv
│   │   ├── tickets.csv
│   │   ├── threads.csv
│   │   └── recurring_tasks.csv
│   ├── processed/
│   └── validate_data.py
├── servers/
│   ├── search/
│   │   ├── search_engine.py
│   │   └── server.py
│   ├── handover/
│   │   └── server.py
│   └── documents/
├── governance/
├── host/
├── ui/
├── tests/
├── docs/
│   ├── evaluation.md
│   ├── test_questions.md
│   ├── handover_template.md
│   ├── handover_interview.md
│   └── handover_test_scenario.md
├── prompts/
│   └── handover.md
├── requirements.txt
├── .gitignore
└── README.md
```

## 4. Wymagania

Do uruchomienia projektu potrzebne są:

- Python 3.13 lub kompatybilna wersja.
- Node.js i npm (potrzebne do uruchomienia MCP Inspector).
- Claude Desktop.
- Połączenie z internetem przy pierwszym pobieraniu modelu embeddingowego.

## 5. Instalacja

Sklonuj repozytorium:

```bash
git clone https://github.com/gpudlo5/Budowa-i-wykorzystanie-systemow-AI.git
cd Budowa-i-wykorzystanie-systemow-AI
```

Utwórz środowisko wirtualne:

```bash
python3 -m venv .venv
```

Aktywuj środowisko:

macOS / Linux:

```bash
source .venv/bin/activate
```

Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

## 6. Walidacja danych

Przed uruchomieniem systemu można sprawdzić poprawność danych:

```bash
python data/validate_data.py
```

Walidator sprawdza m.in.:
- unikalność identyfikatorów,
- poprawność relacji między danymi,
- powiązania pracowników, klientów, zgłoszeń i zadań,
- poprawność przypisań dokumentów i uprawnień ACL.

## 7. Konfiguracja Claude Desktop

Plik konfiguracyjny Claude Desktop w systemie macOS znajduje się w:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

Do konfiguracji `mcpServers` należy dodać wpisy dla obu serwerów:

```json
{
  "mcpServers": {
    "nordwind-handover": {
      "command": "/ABSOLUTE/PATH/TO/knowledge-manager/.venv/bin/python",
      "args": [
        "/ABSOLUTE/PATH/TO/knowledge-manager/servers/handover/server.py"
      ]
    },
    "nordwind-search": {
      "command": "/ABSOLUTE/PATH/TO/knowledge-manager/.venv/bin/python",
      "args": [
        "/ABSOLUTE/PATH/TO/knowledge-manager/servers/search/server.py"
      ]
    }
  }
}
```

Należy zastąpić ścieżki przykładowe rzeczywistą ścieżką do projektu.

Po zapisaniu konfiguracji należy ponownie uruchomić Claude Desktop.

## 8. Uruchamianie i testowanie

### Wyszukiwanie dokumentów

Serwer Search MCP można uruchomić przez Claude Desktop po skonfigurowaniu połączenia MCP.

Przykładowe pytanie:

> Jak należy weryfikować faktury od dostawców?

Pracownik powinien zostać zidentyfikowany przez swój identyfikator, np. `E002`.

### Przekazywanie obowiązków

Serwer Handover MCP udostępnia informacje o pracowniku, jego zgłoszeniach, wątkach i zadaniach cyklicznych.

Przykładowy scenariusz:

- pracownik odchodzący: Anna Kowalska (`E001`),
- pracownik przejmujący: Piotr Nowak (`E002`).

Prompt `handover` pomaga przygotować podsumowanie obowiązków i spraw do przekazania.

### Testy

Scenariusze testowe i wyniki ewaluacji znajdują się w katalogu `docs/`:
- `test_questions.md`
- `evaluation.md`
- `handover_test_scenario.md`

## 9. Wyniki wstępnej ewaluacji

W ramach testów Search MCP przygotowano 10 scenariuszy obejmujących:
- wyszukiwanie dokumentów,
- łączenie informacji z kilku źródeł,
- rozpoznawanie braków w dokumentacji,
- kontrolę dostępu ACL,
- ochronę dokumentów niedostępnych dla danego pracownika.

W testach przeprowadzonych w Claude Desktop wszystkie 10 scenariuszy uzyskało wynik PASS.

Wynik dotyczy przygotowanego zestawu testowego i nie stanowi formalnego potwierdzenia bezpieczeństwa produkcyjnego systemu.

## 10. Ograniczenia prototypu

- System wykorzystuje syntetyczne dane, a nie rzeczywiste dane przedsiębiorstwa.
- Wyszukiwanie semantyczne może zwracać dokumenty o niskiej trafności.
- Nie zastosowano jeszcze progu podobieństwa pozwalającego odrzucać nieadekwatne wyniki.
- Serwer Handover nie implementuje produkcyjnego uwierzytelniania i autoryzacji.
- Projekt nie jest połączony z rzeczywistymi systemami ERP, CRM ani systemami zgłoszeniowymi.
- Wyniki zależą od jakości dostępnej dokumentacji oraz modelu językowego.

## 11. Bezpieczeństwo i prywatność

Projekt wykorzystuje syntetyczne dane pracowników i klientów.

W serwerze Search zastosowano mechanizm ACL ograniczający dostęp do dokumentów na podstawie roli pracownika.

Mechanizm ten jest elementem demonstracyjnym i wymaga dalszego rozwoju przed zastosowaniem produkcyjnym. W szczególności konieczne jest wdrożenie wiarygodnego uwierzytelniania tożsamości i kontroli uprawnień po stronie serwera.

## 12. Repozytorium

Kod źródłowy projektu:

https://github.com/gpudlo5/Budowa-i-wykorzystanie-systemow-AI.git

Projekt został przygotowany w ramach pracy zespołowej dotyczącej budowy i wykorzystania systemów AI.