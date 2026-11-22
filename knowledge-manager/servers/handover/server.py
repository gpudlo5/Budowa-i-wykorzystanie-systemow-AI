
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP


# --------------------------------------------------
# KONFIGURACJA
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
HANDOVER_OUTPUT_DIR = PROCESSED_DIR / "handovers"
PROMPT_FILE = BASE_DIR / "prompts" / "handover.md"

mcp = FastMCP("Nordwind Handover")

CLOSED_STATUSES = {
    "completed",
    "closed",
    "resolved",
    "cancelled",
    "done"
}


# --------------------------------------------------
# FUNKCJE POMOCNICZE
# --------------------------------------------------

def load_csv(filename: str) -> list[dict]:
    """Odczytuje dane z pliku CSV."""
    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {file_path}")

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def find_employee(employee_id: str) -> dict:
    """Wyszukuje pracownika po identyfikatorze."""
    employees = load_csv("employees.csv")

    employee = next(
        (
            item for item in employees
            if item["employee_id"] == employee_id
        ),
        None
    )

    if employee is None:
        raise ValueError(f"Nie znaleziono pracownika: {employee_id}")

    return employee


def format_result(data) -> str:
    """Zwraca dane w czytelnym formacie JSON."""
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )


def is_closed(item: dict) -> bool:
    """Sprawdza, czy element ma status oznaczający zakończenie."""
    status = item.get("status", "").strip().lower()
    return status in CLOSED_STATUSES


def collect_footprint_data(employee_id: str) -> dict:
    """
    Zbiera ślad pracy pracownika:
    zgłoszenia, wątki, zadania cykliczne i powiązanych klientów.
    """
    employee = find_employee(employee_id)

    tickets = [
        item for item in load_csv("tickets.csv")
        if item["assigned_to"] == employee_id
    ]

    threads = [
        item for item in load_csv("threads.csv")
        if item["assigned_to"] == employee_id
    ]

    tasks = [
        item for item in load_csv("recurring_tasks.csv")
        if item["assigned_to"] == employee_id
    ]

    client_ids = {
        item["client_id"]
        for item in tickets + threads
        if item.get("client_id")
    }

    clients = [
        client for client in load_csv("clients.csv")
        if client["client_id"] in client_ids
    ]

    return {
        "employee": employee,
        "tickets": tickets,
        "threads": threads,
        "recurring_tasks": tasks,
        "related_clients": clients,
        "summary": {
            "total_tickets": len(tickets),
            "total_threads": len(threads),
            "total_recurring_tasks": len(tasks),
            "total_related_clients": len(clients)
        }
    }


def extract_open_items_data(employee_id: str) -> dict:
    """
    Wyodrębnia sprawy wymagające dalszej uwagi.
    """
    footprint = collect_footprint_data(employee_id)

    open_tickets = [
        item for item in footprint["tickets"]
        if not is_closed(item)
    ]

    completed_tickets = [
        item for item in footprint["tickets"]
        if is_closed(item)
    ]

    # Wątki bez statusu również wymagają przejrzenia.
    threads_to_review = [
        item for item in footprint["threads"]
        if not is_closed(item)
    ]

    active_tasks = [
        item for item in footprint["recurring_tasks"]
        if not is_closed(item)
    ]

    return {
        "employee": footprint["employee"],
        "open_tickets": open_tickets,
        "completed_tickets": completed_tickets,
        "threads_to_review": threads_to_review,
        "recurring_tasks_to_continue": active_tasks,
        "summary": {
            "open_tickets": len(open_tickets),
            "completed_tickets": len(completed_tickets),
            "threads_to_review": len(threads_to_review),
            "recurring_tasks_to_continue": len(active_tasks)
        },
        "note": (
            "Wątki i zadania wymagają weryfikacji przez pracownika. "
            "Sam brak statusu nie potwierdza, że sprawa jest otwarta."
        )
    }


def append_records(lines: list, title: str, records: list[dict]):
    """Dodaje rekordy do dokumentu Markdown."""
    lines.append(f"## {title}")
    lines.append("")

    if not records:
        lines.append("Brak zarejestrowanych pozycji.")
        lines.append("")
        return

    for index, record in enumerate(records, start=1):
        lines.append(f"### {index}.")

        for key, value in record.items():
            formatted_value = json.dumps(
                value,
                ensure_ascii=False
            )
            lines.append(f"- **{key}:** {formatted_value}")

        lines.append("")


# --------------------------------------------------
# NARZĘDZIE 1 – INFORMACJE O PRACOWNIKU
# --------------------------------------------------

@mcp.tool()
def get_employee_info(employee_id: str) -> str:
    """Pobiera podstawowe informacje o pracowniku."""
    employee = find_employee(employee_id)
    return format_result(employee)


# --------------------------------------------------
# NARZĘDZIE 2 – ZGŁOSZENIA PRACOWNIKA
# --------------------------------------------------

@mcp.tool()
def get_employee_tickets(employee_id: str) -> str:
    """Pobiera zgłoszenia przypisane do pracownika."""
    find_employee(employee_id)

    tickets = load_csv("tickets.csv")

    employee_tickets = [
        ticket for ticket in tickets
        if ticket["assigned_to"] == employee_id
    ]

    return format_result(employee_tickets)


# --------------------------------------------------
# NARZĘDZIE 3 – WĄTKI KOMUNIKACYJNE
# --------------------------------------------------

@mcp.tool()
def get_employee_threads(employee_id: str) -> str:
    """Pobiera wątki komunikacyjne przypisane do pracownika."""
    find_employee(employee_id)

    threads = load_csv("threads.csv")

    employee_threads = [
        thread for thread in threads
        if thread["assigned_to"] == employee_id
    ]

    return format_result(employee_threads)


# --------------------------------------------------
# NARZĘDZIE 4 – ZADANIA CYKLICZNE
# --------------------------------------------------

@mcp.tool()
def get_employee_recurring_tasks(employee_id: str) -> str:
    """Pobiera zadania cykliczne przypisane do pracownika."""
    find_employee(employee_id)

    tasks = load_csv("recurring_tasks.csv")

    employee_tasks = [
        task for task in tasks
        if task["assigned_to"] == employee_id
    ]

    return format_result(employee_tasks)


# --------------------------------------------------
# NARZĘDZIE 5 – ZBIORCZY PRZEGLĄD HANDOVER
# --------------------------------------------------

@mcp.tool()
def get_handover_overview(
    from_employee_id: str,
    to_employee_id: str
) -> str:
    """Przygotowuje zbiorcze zestawienie danych do handover."""
    source_employee = find_employee(from_employee_id)
    target_employee = find_employee(to_employee_id)

    if source_employee["department"] != target_employee["department"]:
        return format_result({
            "error": "Pracownicy należą do różnych działów.",
            "from_department": source_employee["department"],
            "to_department": target_employee["department"]
        })

    footprint = collect_footprint_data(from_employee_id)
    open_items = extract_open_items_data(from_employee_id)

    return format_result({
        "process": "Handover",
        "organization": "Nordwind Logistics",
        "from_employee": source_employee,
        "to_employee": target_employee,
        "tickets": footprint["tickets"],
        "open_tickets": open_items["open_tickets"],
        "completed_tickets": open_items["completed_tickets"],
        "threads": footprint["threads"],
        "recurring_tasks": footprint["recurring_tasks"],
        "related_clients": footprint["related_clients"],
        "summary": {
            **footprint["summary"],
            **open_items["summary"]
        },
        "note": (
            "To zestawienie jest projektem przekazania. "
            "Nie zmienia automatycznie przypisania zadań "
            "ani zgłoszeń nowemu pracownikowi."
        )
    })


# --------------------------------------------------
# NARZĘDZIE 6 – ZEBRANIE ŚLADU PRACY
# --------------------------------------------------

@mcp.tool()
def collect_footprint(employee_id: str) -> str:
    """
    Zbiera informacje o pracy pracownika:
    zgłoszenia, wątki, zadania cykliczne i klientów.
    """
    footprint = collect_footprint_data(employee_id)

    return format_result({
        "operation": "collect_footprint",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        **footprint
    })


# --------------------------------------------------
# NARZĘDZIE 7 – WYODRĘBNIANIE OTWARTYCH SPRAW
# --------------------------------------------------

@mcp.tool()
def extract_open_items(employee_id: str) -> str:
    """
    Wyodrębnia otwarte zgłoszenia, wątki do przejrzenia
    oraz zadania cykliczne wymagające kontynuacji.
    """
    result = extract_open_items_data(employee_id)

    return format_result({
        "operation": "extract_open_items",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        **result
    })


# --------------------------------------------------
# NARZĘDZIE 8 – GENEROWANIE DOKUMENTU HANDOVER
# --------------------------------------------------

@mcp.tool()
def generate_handover_doc(
    from_employee_id: str,
    to_employee_id: str
) -> str:
    """
    Generuje dokument Markdown przekazania obowiązków.
    Dokument jest zapisywany w data/processed/handovers.
    """
    source_employee = find_employee(from_employee_id)
    target_employee = find_employee(to_employee_id)

    if source_employee["department"] != target_employee["department"]:
        raise ValueError(
            "Pracownicy należą do różnych działów. "
            "Generowanie dokumentu zostało wstrzymane."
        )

    footprint = collect_footprint_data(from_employee_id)
    open_items = extract_open_items_data(from_employee_id)

    generated_at = datetime.now(timezone.utc).isoformat()

    lines = [
        "# Dokument przekazania obowiązków",
        "",
        "**Organizacja:** Nordwind Logistics",
        f"**Data wygenerowania (UTC):** {generated_at}",
        "",
        "## 1. Pracownicy",
        "",
        f"- **Przekazujący:** {source_employee['first_name']} "
        f"{source_employee['last_name']} "
        f"({from_employee_id})",
        f"- **Przejmujący:** {target_employee['first_name']} "
        f"{target_employee['last_name']} "
        f"({to_employee_id})",
        f"- **Dział:** {source_employee['department']}",
        "",
        "## 2. Podsumowanie",
        "",
        f"- Wszystkie zgłoszenia: {footprint['summary']['total_tickets']}",
        f"- Otwarte zgłoszenia: {open_items['summary']['open_tickets']}",
        f"- Zakończone zgłoszenia: {open_items['summary']['completed_tickets']}",
        f"- Wątki do przejrzenia: {open_items['summary']['threads_to_review']}",
        f"- Zadania cykliczne do kontynuacji: "
        f"{open_items['summary']['recurring_tasks_to_continue']}",
        f"- Powiązani klienci: {footprint['summary']['total_related_clients']}",
        "",
    ]

    append_records(
        lines,
        "3. Otwarte zgłoszenia",
        open_items["open_tickets"]
    )

    append_records(
        lines,
        "4. Zakończone zgłoszenia – historia",
        open_items["completed_tickets"]
    )

    append_records(
        lines,
        "5. Wątki komunikacyjne do przejrzenia",
        open_items["threads_to_review"]
    )

    append_records(
        lines,
        "6. Zadania cykliczne do kontynuacji",
        open_items["recurring_tasks_to_continue"]
    )

    append_records(
        lines,
        "7. Powiązani klienci",
        footprint["related_clients"]
    )

    lines.extend([
        "## 8. Zalecane dalsze działania",
        "",
        "1. Zweryfikować status wszystkich otwartych zgłoszeń.",
        "2. Przejrzeć wątki komunikacyjne i ustalić wymagane odpowiedzi.",
        "3. Potwierdzić terminy i odpowiedzialność za zadania cykliczne.",
        "4. Zweryfikować informacje dotyczące klientów.",
        "5. Uzupełnić dokument o wiedzę nieformalną przekazywaną podczas wywiadu.",
        "",
        "## 9. Ograniczenia i weryfikacja",
        "",
        "Dokument został wygenerowany na podstawie danych dostępnych "
        "w plikach CSV systemu Knowledge Manager.",
        "",
        "Nie zawiera automatycznie informacji, których nie zapisano "
        "w źródłach danych.",
        "",
        "Wszystkie informacje wymagają weryfikacji przez pracowników.",
        "Wygenerowanie dokumentu nie zmienia przypisań zgłoszeń ani zadań.",
        ""
    ])

    document = "\n".join(lines)

    HANDOVER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    safe_from_id = re.sub(r"[^a-zA-Z0-9_-]", "_", from_employee_id)
    safe_to_id = re.sub(r"[^a-zA-Z0-9_-]", "_", to_employee_id)

    output_file = (
        HANDOVER_OUTPUT_DIR
        / f"handover_{safe_from_id}_to_{safe_to_id}.md"
    )

    output_file.write_text(document, encoding="utf-8")

    return format_result({
        "status": "generated",
        "file_path": str(output_file.relative_to(BASE_DIR)),
        "from_employee": from_employee_id,
        "to_employee": to_employee_id,
        "generated_at": generated_at,
        "document": document
    })


# --------------------------------------------------
# ZASÓB MCP – INSTRUKCJA PROCESU
# --------------------------------------------------

@mcp.resource("handover://guidelines")
def handover_guidelines() -> str:
    """Udostępnia zasady bezpiecznego procesu przekazania obowiązków."""
    return """
    PROCES HANDOVER – NORDWIND LOGISTICS

    1. Zidentyfikuj pracownika przekazującego obowiązki.
    2. Zidentyfikuj pracownika przejmującego obowiązki.
    3. Użyj collect_footprint, aby zebrać ślad pracy.
    4. Użyj extract_open_items, aby wyodrębnić sprawy wymagające uwagi.
    5. Przeanalizuj zgłoszenia, wątki i zadania cykliczne.
    6. Zidentyfikuj klientów powiązanych ze sprawami.
    7. Przeprowadź wywiad z pracownikiem.
    8. Użyj generate_handover_doc, aby przygotować dokument.
    9. Wskaż źródła informacji.
    10. Oznacz dane wymagające potwierdzenia.
    11. Nie zmieniaj automatycznie przypisania zadań.

    Dane demonstracyjne nie zastępują rzeczywistej weryfikacji
    przez upoważnionego pracownika.
    """


# --------------------------------------------------
# PROMPT MCP – HANDOVER
# --------------------------------------------------

@mcp.prompt()
def handover(
    from_employee_id: str = "E001",
    to_employee_id: str = "E002"
) -> str:
    """Przygotowuje instrukcję procesu przekazania obowiązków."""

    if not PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"Nie znaleziono promptu: {PROMPT_FILE}"
        )

    instructions = PROMPT_FILE.read_text(encoding="utf-8")

    return (
        f"{instructions}\n\n"
        f"Pracownik przekazujący: {from_employee_id}\n"
        f"Pracownik przejmujący: {to_employee_id}\n\n"
        "Rozpocznij proces od zebrania śladu pracy za pomocą "
        "collect_footprint. Następnie użyj extract_open_items. "
        "Po analizie przygotuj dokument za pomocą generate_handover_doc. "
        "Nie zmieniaj automatycznie przypisań zadań."
    )


# --------------------------------------------------
# URUCHOMIENIE SERWERA
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
