
import csv
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP


# --------------------------------------------------
# KONFIGURACJA
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "raw"
PROMPT_FILE = BASE_DIR / "prompts" / "handover.md"

mcp = FastMCP("Nordwind Handover")


# --------------------------------------------------
# FUNKCJE POMOCNICZE
# --------------------------------------------------

def load_csv(filename: str) -> list[dict]:
    """Odczytuje dane z pliku CSV."""
    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Nie znaleziono pliku: {file_path}"
        )

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
        raise ValueError(
            f"Nie znaleziono pracownika: {employee_id}"
        )

    return employee


def format_result(data) -> str:
    """Zwraca dane w czytelnym formacie JSON."""
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )


# --------------------------------------------------
# NARZĘDZIE 1 – INFORMACJE O PRACOWNIKU
# --------------------------------------------------

@mcp.tool()
def get_employee_info(employee_id: str) -> str:
    """
    Pobiera podstawowe informacje o pracowniku.

    Args:
        employee_id: Identyfikator pracownika, np. E001.
    """
    employee = find_employee(employee_id)
    return format_result(employee)


# --------------------------------------------------
# NARZĘDZIE 2 – ZGŁOSZENIA PRACOWNIKA
# --------------------------------------------------

@mcp.tool()
def get_employee_tickets(employee_id: str) -> str:
    """
    Pobiera zgłoszenia przypisane do pracownika.

    Args:
        employee_id: Identyfikator pracownika, np. E001.
    """
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
    """
    Pobiera wątki komunikacyjne przypisane do pracownika.

    Args:
        employee_id: Identyfikator pracownika, np. E001.
    """
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
    """
    Pobiera zadania cykliczne przypisane do pracownika.

    Args:
        employee_id: Identyfikator pracownika, np. E001.
    """
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
    """
    Przygotowuje zestawienie danych do przekazania obowiązków.

    Args:
        from_employee_id: ID pracownika przekazującego obowiązki.
        to_employee_id: ID pracownika przejmującego obowiązki.
    """
    source_employee = find_employee(from_employee_id)
    target_employee = find_employee(to_employee_id)

    if source_employee["department"] != target_employee["department"]:
        return format_result({
            "error": "Pracownicy należą do różnych działów.",
            "from_department": source_employee["department"],
            "to_department": target_employee["department"]
        })

    tickets = [
        ticket for ticket in load_csv("tickets.csv")
        if ticket["assigned_to"] == from_employee_id
    ]

    threads = [
        thread for thread in load_csv("threads.csv")
        if thread["assigned_to"] == from_employee_id
    ]

    tasks = [
        task for task in load_csv("recurring_tasks.csv")
        if task["assigned_to"] == from_employee_id
    ]

    clients = load_csv("clients.csv")
    client_ids = {
        ticket["client_id"] for ticket in tickets
    }

    related_clients = [
        client for client in clients
        if client["client_id"] in client_ids
    ]

    open_tickets = [
        ticket for ticket in tickets
        if ticket["status"].lower() not in (
            "completed", "closed", "resolved", "cancelled"
        )
    ]

    completed_tickets = [
        ticket for ticket in tickets
        if ticket["status"].lower() in (
            "completed", "closed", "resolved", "cancelled"
        )
    ]

    result = {
        "process": "Handover",
        "organization": "Nordwind Logistics",
        "from_employee": source_employee,
        "to_employee": target_employee,
        "tickets": tickets,
        "open_tickets": open_tickets,
        "completed_tickets": completed_tickets,
        "threads": threads,
        "recurring_tasks": tasks,
        "related_clients": related_clients,
        "summary": {
            "total_tickets": len(tickets),
            "open_tickets": len(open_tickets),
            "completed_tickets": len(completed_tickets),
            "total_threads": len(threads),
            "recurring_tasks": len(tasks),
            "related_clients": len(related_clients)
        },
        "note": (
            "To zestawienie jest projektem przekazania. "
            "Nie zmienia automatycznie przypisania zadań "
            "ani zgłoszeń nowemu pracownikowi."
        )
    }

    return format_result(result)


# --------------------------------------------------
# ZASÓB MCP – INSTRUKCJA PROCESU
# --------------------------------------------------

@mcp.resource("handover://guidelines")
def handover_guidelines() -> str:
    """
    Udostępnia zasady bezpiecznego procesu przekazania obowiązków.
    """
    return """
    PROCES HANDOVER – NORDWIND LOGISTICS

    1. Zidentyfikuj pracownika przekazującego obowiązki.
    2. Zidentyfikuj pracownika przejmującego obowiązki.
    3. Pobierz zgłoszenia, wątki i zadania cykliczne.
    4. Rozróżnij sprawy otwarte i zakończone.
    5. Zidentyfikuj klientów powiązanych ze sprawami.
    6. Przeprowadź wywiad z pracownikiem.
    7. Przygotuj projekt dokumentu przekazania.
    8. Wskaż źródła informacji.
    9. Oznacz dane wymagające potwierdzenia.
    10. Nie zmieniaj automatycznie przypisania zadań.

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
    """
    Przygotowuje instrukcję procesu przekazania obowiązków.

    Args:
        from_employee_id: ID pracownika przekazującego.
        to_employee_id: ID pracownika przejmującego.
    """
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"Nie znaleziono promptu: {PROMPT_FILE}"
        )

    instructions = PROMPT_FILE.read_text(encoding="utf-8")

    return (
        f"{instructions}\n\n"
        f"Pracownik przekazujący: {from_employee_id}\n"
        f"Pracownik przejmujący: {to_employee_id}\n\n"
        "Rozpocznij proces od identyfikacji pracowników "
        "i pobrania dostępnych informacji."
    )


# --------------------------------------------------
# URUCHOMIENIE SERWERA
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
