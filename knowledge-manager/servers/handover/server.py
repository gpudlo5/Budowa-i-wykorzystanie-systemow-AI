
"""
server.py - Handover MCP (Knowledge Manager, Northway Ltd.).

Przekazanie obowiazkow: slad pracy, otwarte sprawy, wywiad, dokument,
potwierdzenia stron, zatwierdzenie przez przelozonego, publikacja.
Uzytkownik: ze zmiennej srodowiskowej KM_USER_ID (konfiguracja serwera).
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from servers.common.access import allowed_groups, can_access  # noqa: E402
from servers.common.config import (  # noqa: E402
    CURRENT_USER_ID,
    HANDOVER_DIR as HANDOVER_OUTPUT_DIR,
    INTERVIEW_DIR as INTERVIEW_OUTPUT_DIR,
    ONBOARDING_DIR as ONBOARDING_OUTPUT_DIR,
    PROCESSED_DIR,
)
from servers.common.data import load_csv, load_json, split_ids  # noqa: E402
from servers.common.org import Org  # noqa: E402

INTERVIEW_FILE = BASE_DIR / "docs" / "handover_interview.md"
PROMPT_FILE = BASE_DIR / "prompts" / "handover.md"

mcp = FastMCP("Northway Handover")
org = Org()

CLOSED_STATUSES = {
    "zamknięte", "zamknięty", "zakończone", "zakończony",
    "completed", "closed", "resolved", "cancelled", "done",
}

# --------------------------------------------------
# FUNKCJE POMOCNICZE
# --------------------------------------------------


def find_employee(employee_id: str) -> dict:
    """Pracownik z Org (imie, nazwisko, dzial, rola, przelozony, grupa dostepu)."""
    employee = org.get_employee(employee_id)
    if employee is None:
        raise ValueError(f"Nie znaleziono pracownika: {employee_id}")
    return employee


def _current_user() -> dict:
    """Pracownik, w imieniu ktorego dziala serwer (KM_USER_ID)."""
    if CURRENT_USER_ID is None:
        raise ValueError(
            "Brak KM_USER_ID w konfiguracji serwera (claude_desktop_config.json, sekcja env)."
        )
    return find_employee(CURRENT_USER_ID)


def _require_view(employee_id: str) -> dict:
    """Dane pracownika widzi on sam, jego przelozony i osoby z jego dzialu."""
    me = _current_user()
    employee = find_employee(employee_id)
    if (
        me["employee_id"] in (employee["employee_id"], employee["manager_id"])
        or me["department_id"] == employee["department_id"]
    ):
        return me
    raise PermissionError("Brak uprawnien do danych tego pracownika.")


def _require_manager_of(employee_id: str) -> dict:
    """Akcja dozwolona tylko dla przelozonego wskazanego pracownika."""
    me = _current_user()
    if me["employee_id"] != find_employee(employee_id)["manager_id"]:
        raise PermissionError(
            "Te czynnosc moze wykonac tylko przelozony pracownika przekazujacego."
        )
    return me


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


def load_interview_questions() -> list[dict]:
    """Odczytuje pytania wywiadu z przygotowanego scenariusza."""

    if not INTERVIEW_FILE.exists():
        raise FileNotFoundError(
            f"Nie znaleziono scenariusza wywiadu: {INTERVIEW_FILE}"
        )

    questions = []
    current_section = None

    for line in INTERVIEW_FILE.read_text(
        encoding="utf-8"
    ).splitlines():

        section_match = re.match(
            r"^## (\d+)\. (.+)$",
            line.strip()
        )

        if section_match:
            section_number = int(section_match.group(1))

            if 2 <= section_number <= 8:
                current_section = section_match.group(2)
            else:
                current_section = None

            continue

        question_match = re.match(
            r"^\d+\.\s+(.+)$",
            line.strip()
        )

        if current_section and question_match:
            questions.append({
                "section": current_section,
                "question": question_match.group(1)
            })

    return questions


@mcp.tool()
def interview_next_question(
    from_employee_id: str,
    to_employee_id: str,
    answer: str | None = None
) -> str:
    """
    Prowadzi wywiad z pracownikiem i zapisuje jego odpowiedzi.
    """

    source_employee = find_employee(from_employee_id)
    target_employee = find_employee(to_employee_id)

    if source_employee["department"] != target_employee["department"]:
        raise ValueError(
            "Pracownicy należą do różnych działów."
        )

    questions = load_interview_questions()

    safe_from_id = re.sub(
        r"[^a-zA-Z0-9_-]", "_", from_employee_id
    )

    safe_to_id = re.sub(
        r"[^a-zA-Z0-9_-]", "_", to_employee_id
    )
    
    safe_from_id = re.sub(
        r"[^a-zA-Z0-9_-]", "_", from_employee_id
    )

    safe_to_id = re.sub(
        r"[^a-zA-Z0-9_-]", "_", to_employee_id
    )

    interview_file = (
        INTERVIEW_OUTPUT_DIR
        / f"interview_{safe_from_id}_to_{safe_to_id}.json"
    )

    if interview_file.exists():
        state = json.loads(
            interview_file.read_text(encoding="utf-8")
        )
    else:
        if answer is not None:
            raise ValueError(
                "Najpierw rozpocznij wywiad bez podawania odpowiedzi."
            )

        state = {
            "from_employee": from_employee_id,
            "to_employee": to_employee_id,
            "status": "in_progress",
            "current_index": 0,
            "answers": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    if state["status"] == "completed":
        return format_result({
            "status": "completed",
            "message": "Wywiad został już zakończony.",
            "answers_count": len(state["answers"])
        })
        
    if state["current_index"] >= len(questions):
        raise ValueError(
            "Nieprawidłowy stan wywiadu: indeks pytania wykracza poza scenariusz."
        )

    if answer is not None:
        if not answer.strip():
            raise ValueError("Odpowiedź nie może być pusta.")

        current_question = questions[state["current_index"]]

        state["answers"].append({
            "section": current_question["section"],
            "question": current_question["question"],
            "answer": answer.strip(),
            "source": "employee_interview",
            "answered_at": datetime.now(timezone.utc).isoformat()
        })

        state["current_index"] += 1

    if state["current_index"] >= len(questions):
        state["status"] = "completed"

        INTERVIEW_OUTPUT_DIR.mkdir(
            parents=True, exist_ok=True
        )

        interview_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return format_result({
            "status": "completed",
            "message": "Wywiad został zakończony.",
            "answers_count": len(state["answers"]),
            "file_path": str(interview_file.relative_to(BASE_DIR))
        })

    current_question = questions[state["current_index"]]

    INTERVIEW_OUTPUT_DIR.mkdir(
        parents=True, exist_ok=True
    )

    interview_file.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return format_result({
        "status": "in_progress",
        "progress": f"{state['current_index'] + 1}/{len(questions)}",
        "section": current_question["section"],
        "question": current_question["question"],
        "answers_saved": len(state["answers"]),
        "file_path": str(interview_file.relative_to(BASE_DIR))
    })


def collect_footprint_data(
    employee_id: str,
    access_check_employee_id: str = None
) -> dict:
    """
    Zbiera slad pracy pracownika: dokumenty, projekty, zgloszenia, watki,
    zadania cykliczne, kontrahentow i dokumenty dostepne dla przejmujacego.
    """
    employee = find_employee(employee_id)

    # 1-2. Dokumenty napisane i posiadane przez pracownika
    all_documents = load_csv("documents_plan.csv")
    authored_documents = [d for d in all_documents if d["author_id"] == employee_id]
    owned_documents = [d for d in all_documents if d["owner_id"] == employee_id]

    # 3. Projekty: wlasciciel albo uczestnik
    projects = [
        p for p in load_csv("projects.csv")
        if p["owner_id"] == employee_id
        or employee_id in split_ids(p["participant_ids"])
    ]

    # 4. Zgloszenia przypisane do pracownika
    tickets = [t for t in load_json("tickets.json") if t["assignee_id"] == employee_id]

    # 5. Watki, w ktorych pracownik pisal
    threads = [
        t for t in load_json("threads.json")
        if any(m["author_id"] == employee_id for m in t["messages"])
    ]

    # 6. Zadania cykliczne: wlasciciel albo wspolpracownik
    tasks = [
        t for t in load_json("recurring_tasks.json")
        if t["owner_id"] == employee_id or employee_id in t["collaborators"]
    ]

    # 7. Kontrahenci: ze zgloszen albo pracownik jest ich opiekunem/kontaktem
    counterparty_names = {t["counterparty"] for t in tickets if t.get("counterparty")}
    clients = [
        c for c in load_csv("counterparties.csv")
        if c["name"] in counterparty_names
        or employee_id in (c["account_owner_id"], c["finance_contact_id"])
    ]

    # 8. Dokumenty dostepne dla pracownika przejmujacego (albo samego pracownika)
    access_employee_id = access_check_employee_id or employee_id
    department_names = org.department_names()
    accessible_documents = [
        {
            "doc_id": d["doc_id"],
            "title": d["title"],
            "department": department_names.get(d["department_id"], d["department_id"]),
            "allowed_groups": allowed_groups(d["doc_id"]),
        }
        for d in all_documents
        if can_access(access_employee_id, d["doc_id"])
    ]

    return {
        "employee": employee,
        "authored_documents": authored_documents,
        "owned_documents": owned_documents,
        "projects": projects,
        "tickets": tickets,
        "threads": threads,
        "recurring_tasks": tasks,
        "related_clients": clients,
        "accessible_documents": accessible_documents,
        "summary": {
            "total_authored_documents": len(authored_documents),
            "total_owned_documents": len(owned_documents),
            "total_projects": len(projects),
            "total_tickets": len(tickets),
            "total_threads": len(threads),
            "total_recurring_tasks": len(tasks),
            "total_related_clients": len(clients),
            "total_accessible_documents": len(accessible_documents),
        },
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
    _require_view(employee_id)
    employee = find_employee(employee_id)
    return format_result(employee)


# --------------------------------------------------
# NARZĘDZIE 2 – ZGŁOSZENIA PRACOWNIKA
# --------------------------------------------------

@mcp.tool()
def get_employee_tickets(employee_id: str) -> str:
    """Pobiera zgłoszenia przypisane do pracownika."""
    _require_view(employee_id)
    return format_result(collect_footprint_data(employee_id)["tickets"])          # w get_employee_tickets


# --------------------------------------------------
# NARZĘDZIE 3 – WĄTKI KOMUNIKACYJNE
# --------------------------------------------------

@mcp.tool()
def get_employee_threads(employee_id: str) -> str:
    """Pobiera wątki komunikacyjne przypisane do pracownika."""
    _require_view(employee_id)
    return format_result(collect_footprint_data(employee_id)["threads"])          # w get_employee_threads


# --------------------------------------------------
# NARZĘDZIE 4 – ZADANIA CYKLICZNE
# --------------------------------------------------

@mcp.tool()
def get_employee_recurring_tasks(employee_id: str) -> str:
    """Pobiera zadania cykliczne przypisane do pracownika."""
    _require_view(employee_id)
    return format_result(collect_footprint_data(employee_id)["recurring_tasks"])  # w get_employee_recurring_tasks


# --------------------------------------------------
# NARZĘDZIE 5 – ZBIORCZY PRZEGLĄD HANDOVER
# --------------------------------------------------

@mcp.tool()
def get_handover_overview(
    from_employee_id: str,
    to_employee_id: str
) -> str:
    """Przygotowuje zbiorcze zestawienie danych do handover."""
    _require_view(from_employee_id)
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
        "organization": "Northway Ltd.",
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
    _require_view(employee_id)
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
    _require_view(employee_id)
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

    safe_from_id = re.sub(
        r"[^a-zA-Z0-9_-]", "_", from_employee_id
    )

    safe_to_id = re.sub(
        r"[^a-zA-Z0-9_-]", "_", to_employee_id
    )

    footprint = collect_footprint_data(
        from_employee_id,
        access_check_employee_id=to_employee_id
    )
    open_items = extract_open_items_data(from_employee_id)

    generated_at = datetime.now(timezone.utc).isoformat()
    
    
    # Tłumaczenie wartości na język polski.
    status_translations = {
        "in_progress": "W trakcie realizacji",
        "in progress": "W trakcie realizacji",
        "open": "Otwarte",
        "completed": "Zakończone",
        "pending": "Oczekujące",
        "active": "Aktywne",
    }

    priority_translations = {
        "high": "Wysoki",
        "medium": "Średni",
        "low": "Niski",
    }

    frequency_translations = {
        "daily": "Codziennie",
        "weekly": "Co tydzień",
        "monthly": "Co miesiąc",
    }

    def translate_status(value):
        return status_translations.get(
            str(value).lower(), value
        )

    def translate_priority(value):
        return priority_translations.get(
            str(value).lower(), value
        )

    def translate_frequency(value):
        return frequency_translations.get(
            str(value).lower(), value
        )

    # Dodaje identyfikator źródła do każdego rekordu.
    def add_source_reference(records, id_field):
        result = []

        for record in records:
            item = dict(record)
            item["source_reference"] = (
                f"{id_field}: {record.get(id_field, 'brak ID')}"
            )
            result.append(item)

        return result

    # Łączy dokumenty napisane i posiadane przez pracownika.
    # Dzięki temu ten sam dokument nie pojawi się dwa razy.
    documents_by_id = {}

    for document in footprint["authored_documents"]:
        doc_id = document["doc_id"]
        documents_by_id[doc_id] = dict(document)
        documents_by_id[doc_id]["relation_to_employee"] = "Autor"

    for document in footprint["owned_documents"]:
        doc_id = document["doc_id"]

        if doc_id in documents_by_id:
            documents_by_id[doc_id]["relation_to_employee"] = (
                "Autor i właściciel"
            )
        else:
            documents_by_id[doc_id] = dict(document)
            documents_by_id[doc_id]["relation_to_employee"] = "Właściciel"

    handover_documents = add_source_reference(
        list(documents_by_id.values()),
        "doc_id"
    )

    projects = add_source_reference(
        footprint["projects"],
        "project_id"
    )

    accessible_documents = add_source_reference(
        footprint["accessible_documents"],
        "doc_id"
    )

    open_tickets = add_source_reference(
        open_items["open_tickets"],
        "ticket_id"
    )

    completed_tickets = add_source_reference(
        open_items["completed_tickets"],
        "ticket_id"
    )

    threads = add_source_reference(
        open_items["threads_to_review"],
        "thread_id"
    )

    recurring_tasks = add_source_reference(
        open_items["recurring_tasks_to_continue"],
        "task_id"
    )

    clients = add_source_reference(
        footprint["related_clients"],
        "client_id"
    )

    # Zestawienie terminów otwartych zgłoszeń i zadań.
    deadlines = []

    for ticket in open_items["open_tickets"]:
        if ticket.get("due_date"):
            deadlines.append({
                "type": "Zgłoszenie",
                "ticket_id": ticket["ticket_id"],
                "source_reference": f"ticket_id: {ticket['ticket_id']}",
                "title": ticket.get("title", ""),
                "due_date": ticket["due_date"],
                "priority": ticket.get("priority", "")
            })

    for task in open_items["recurring_tasks_to_continue"]:
        if task.get("due_date"):
            deadlines.append({
                "type": "Zadanie cykliczne",
                "source_reference": f"task_id: {task['task_id']}",
                "title": task.get("title", ""),
                "due_date": task["due_date"],
                "priority": task.get("priority", "")
            })

    deadlines.sort(key=lambda item: item["due_date"])

    # Sygnały wymagające uwagi na podstawie danych systemowych.
    attention_items = []

    for ticket in open_items["open_tickets"]:
        if str(ticket.get("priority", "")).lower() == "high":
            attention_items.append({
                "type": "Zgłoszenie o wysokim priorytecie",
                "source_reference": f"ticket_id: {ticket['ticket_id']}",
                "description": ticket.get("title", ""),
                "status": ticket.get("status", ""),
                "due_date": ticket.get("due_date", "")
            })

    for project in footprint["projects"]:
        if str(project.get("status", "")).lower() in (
            "in_progress", "in progress"
        ):
            attention_items.append({
                "type": "Projekt w trakcie realizacji",
                "source_reference": f"project_id: {project['project_id']}",
                "description": project.get("name", ""),
                "status": project.get("status", "")
            })


    # Budowanie dokumentu zgodnego z szablonem handover.

    lines = [
        "# Dokument przekazania obowiązków",
        "",
        "## Nordwind Logistics",
        "",
        "**Wersja:** 1.0",
        "**Typ dokumentu:** Dokument przekazania obowiązków",
        "**Status:** Do weryfikacji",
        "",
        "## 1. Dane pracowników",
        "",
        "| Pole | Informacja |",
        "|---|---|",
        f"| Pracownik przekazujący | {source_employee['first_name']} {source_employee['last_name']} |",
        f"| Identyfikator | {from_employee_id} |",
        f"| Dział | {source_employee['department']} |",
        f"| Pracownik przejmujący | {target_employee['first_name']} {target_employee['last_name']} |",
        f"| Identyfikator | {to_employee_id} |",
        f"| Data przekazania | Do uzupełnienia |",
        f"| Data zakończenia pracy przez przekazującego | Do uzupełnienia |",
        "",
        "## 2. Zakres przekazywanych obowiązków",
        "",
        "| Obowiązek | Częstotliwość | Priorytet | Uwagi |",
        "|---|---|---|---|",
    ]

    for task in recurring_tasks:
        lines.append(
            f"| {task.get('title', '')} "
            f"| {translate_frequency(task.get('frequency', 'Do potwierdzenia'))} "
            f"| {translate_priority(task.get('priority', 'Do potwierdzenia'))} "
            f"| Źródło: {task.get('source_reference', '')} |"
        )

    lines.extend([
        "",
        "## 3. Sprawy w toku",
        "",
        "| ID zgłoszenia | Sprawa | Status | Termin | Zalecane następne działanie |",
        "|---|---|---|---|---|",
    ])

    for ticket in open_tickets:
        lines.append(
            f"| {ticket.get('ticket_id', '')} "
            f"| {ticket.get('title', '')} "
            f"| {translate_status(ticket.get('status', ''))} "
            f"| {ticket.get('due_date', 'Brak terminu')} "
            f"| Do ustalenia z przekazującym "
            f"({ticket.get('source_reference', '')}) |"
        )

    lines.extend([
        "",
        "## 4. Kontakty i relacje biznesowe",
        "",
        "| Klient | Osoba kontaktowa | Temat współpracy | Otwarte sprawy |",
        "|---|---|---|---|",
    ])

    for client in clients:
        client_id = client.get("client_id")
        client_tickets = [
            ticket.get("ticket_id", "")
            for ticket in open_tickets
            if ticket.get("client_id") == client_id
        ]
        lines.append(
            f"| {client.get('company_name', '')} "
            f"| {client.get('contact_person', 'Do uzupełnienia')} "
            f"| Do potwierdzenia "
            f"| {', '.join(client_tickets) or 'Brak zarejestrowanych'} |"
        )

    lines.extend([
        "",
        "### Wątki komunikacyjne do przejrzenia",
        "",
    ])

    if threads:
        lines.extend([
            "| ID wątku | ID zgłoszenia | Klient | Temat rozmowy | Podsumowanie | Ostatnia wiadomość | Status |",
            "|---|---|---|---|---|---|---|",
        ])

        for thread in threads:
            lines.append(
                f"| {thread.get('thread_id', '')} "
                f"| {thread.get('ticket_id', '')} "
                f"| {thread.get('client_id', '')} "
                f"| {thread.get('subject', '')} "
                f"| {thread.get('summary', '')} "
                f"| {thread.get('last_message_at', 'Brak daty')} "
                f"| {translate_status(thread.get('status', 'Do potwierdzenia'))} |"
            )
    else:
        lines.append("Brak wątków komunikacyjnych do przejrzenia.")

    lines.append("")

    lines.extend([
    "",
    "## 5. Dokumentacja i źródła wiedzy",
    "",
    "| ID dokumentu | Nazwa | Znaczenie | Relacja pracownika |",
    "|---|---|---|---|",
])

    for doc in handover_documents:
        lines.append(
            f"| {doc.get('doc_id', '')} "
            f"| {doc.get('title', '')} "
            f"| {doc.get('content', 'Brak opisu')} "
            f"| {doc.get('relation_to_employee', '')} |"
        )

    lines.extend([
        "",
        "### Dokumenty dostępne dla pracownika przejmującego",
        "",
    ])

    if accessible_documents:
        lines.extend([
            "| ID dokumentu | Nazwa | Dział |",
            "|---|---|---|",
        ])

        for doc in accessible_documents:
            lines.append(
                f"| {doc.get('doc_id', '')} "
                f"| {doc.get('title', '')} "
                f"| {doc.get('department', '')} |"
            )
    else:
        lines.append("Brak dokumentów dostępnych według roli.")

    lines.extend([
        "",
    ])

    lines.extend([
        "",
        "Pracownik przejmujący powinien zapoznać się z dokumentacją "
        "przed samodzielnym realizowaniem obowiązków.",
        "Uprawnienia pracownika przejmującego sprawdzono na podstawie jego roli i wpisów w pliku ACL.",
        "",
        "## 6. Zadania cykliczne i nadchodzące terminy",
        "",
    ])

    lines.extend([
        "",
        "| ID | Nazwa zadania lub sprawy | Rodzaj | Częstotliwość | Termin | Priorytet |",
        "|---|---|---|---|---|---|",
    ])

    for task in recurring_tasks:
        lines.append(
            f"| {task.get('task_id', '')} "
            f"| {task.get('title', '')} "
            f"| Zadanie cykliczne "
            f"| {translate_frequency(task.get('frequency', ''))} "
            f"| {task.get('due_date', 'Brak terminu')} "
            f"| {translate_priority(task.get('priority', ''))} |"
        )

    for deadline in deadlines:
        if deadline.get("type") == "Zadanie cykliczne":
            continue

        lines.append(
            f"| {deadline.get('ticket_id', '')} "
            f"| {deadline.get('title', '')} "
            f"| {deadline.get('type', '')} "
            f"| — "
            f"| {deadline.get('due_date', '')} "
            f"| {translate_priority(deadline.get('priority', ''))} |"
        )

    lines.append("")

    lines.extend([
        "",
        "## 7. Ryzyka i ważne informacje",
        "",
    ])

    lines.extend([
        "",
        "### Sygnały wymagające uwagi",
        "",
    ])

    if attention_items:
        lines.extend([
            "| Rodzaj | Opis | Status | Termin | Źródło |",
            "|---|---|---|---|---|",
        ])

        for item in attention_items:
            lines.append(
                f"| {item.get('type', '')} "
                f"| {item.get('description', '')} "
                f"| {translate_status(item.get('status', 'Do sprawdzenia'))} "
                f"| {item.get('due_date', 'Brak terminu')} "
                f"| {item.get('source_reference', '')} |"
            )
    else:
        lines.append("Brak zarejestrowanych sygnałów wymagających uwagi.")

    lines.extend([
        "",
        "### Projekty w toku",
        "",
    ])

    if projects:
        lines.extend([
            "| ID projektu | Nazwa | Właściciel | Status | Opis | Źródło |",
            "|---|---|---|---|---|---|",
        ])

        for project in projects:
            lines.append(
                f"| {project.get('project_id', '')} "
                f"| {project.get('name', '')} "
                f"| {project.get('owner_id', '')} "
                f"| {translate_status(project.get('status', ''))} "
                f"| {project.get('description', '')} "
                f"| {project.get('source_reference', '')} |"
            )
    else:
        lines.append("Brak zarejestrowanych projektów.")

    lines.extend([
        "",
        "### Historia zakończonych zgłoszeń",
        "",
    ])

    if completed_tickets:
        lines.extend([
            "| ID zgłoszenia | Sprawa | Status | Termin | Źródło |",
            "|---|---|---|---|---|",
        ])

        for ticket in completed_tickets:
            lines.append(
                f"| {ticket.get('ticket_id', '')} "
                f"| {ticket.get('title', '')} "
                f"| {translate_status(ticket.get('status', ''))} "
                f"| {ticket.get('due_date', 'Brak terminu')} "
                f"| {ticket.get('source_reference', '')} |"
            )
    else:
        lines.append("Brak zarejestrowanych zakończonych zgłoszeń.")

    lines.append("")

    lines.extend([
        "",
        "### Pułapki i nieoczywiste zasady",
        "",
        "- Przed zaksięgowaniem faktury należy sprawdzić jej zgodność "
        "z zamówieniem i potwierdzeniem wykonania usługi. "
        "W przypadku rozbieżności należy skontaktować się z dostawcą "
        "przed zaksięgowaniem (źródło: D002).",
        "",
        "- Proces zamknięcia miesiąca obejmuje uzgodnienie sald "
        "kontrahentów, weryfikację faktur i raport VAT "
        "(źródło: D003).",
        "",
        "- W sprawie T003 oczekiwane jest potwierdzenie wykonania "
        "usługi od klienta. Należy zweryfikować, czy dokument "
        "został już dostarczony (źródła: T003, TH003).",
        "",
        "- Pracownik przejmujący ma dostęp do D002 i D003 na "
        "podstawie przypisanej roli R_FINANCE oraz wpisów w ACL "
        "(źródło: acl.csv).",
        "",
        "## 8. Rekomendacje dla pracownika przejmującego",
        "",
        "1. W pierwszej kolejności przeanalizować zgłoszenia o wysokim priorytecie: T001, T002, T004 i T010.",
        "2. Sprawdzić zgłoszenie T002, którego termin przypada na 2026-11-23.",
        "3. W sprawie T003 zweryfikować, czy klient C003 przesłał brakujące potwierdzenie wykonania usługi (źródła: T003, TH003).",
        "4. W sprawie T001 sprawdzić zgodność faktury FV/2026/101 z zamówieniem i potwierdzeniem wykonania usługi (źródła: T001, TH001, D002).",
        "5. Zapoznać się z procedurą rozliczania faktur i instrukcją zamknięcia miesiąca (D002, D003).",
        "6. Ustalić aktualny stan projektu P001 oraz uzgodnić, kto będzie odpowiedzialny za jego dalszą realizację.",
        "7. Zweryfikować nadchodzące terminy zadań cyklicznych RT001–RT005.",
        "8. Potwierdzić z Anną nieformalne ustalenia, kontakty z klientami i decyzje, których nie zapisano w systemie.",
        "",
        "## 9. Potwierdzenie przekazania",
        "",
        "| Osoba | Imię i nazwisko | Data | Podpis |",
        "|---|---|---|---|",
        f"| Przekazujący | {source_employee['first_name']} {source_employee['last_name']} | | |",
        f"| Przejmujący | {target_employee['first_name']} {target_employee['last_name']} | | |",
        "| Przełożony | Do uzupełnienia | | |",
        "",
        "## 10. Informacja o wykorzystaniu AI",
        "",
        "Dokument został przygotowany przez agenta Knowledge Manager "
        "na podstawie dostępnych danych firmowych.",
        "",
        "Agent:",
        "- korzysta z danych dostępnych w źródłach systemowych;",
        "- wskazuje identyfikatory rekordów źródłowych;",
        "- oznacza informacje brakujące jako wymagające uzupełnienia;",
        "- nie traktuje symulowanych odpowiedzi z wywiadu jako faktów;",
        "- nie zmienia automatycznie przypisań zadań ani zgłoszeń;",
        "",
        "**Status dokumentu:** Wymaga weryfikacji i zatwierdzenia "
        "przez pracowników.",
        "",
        f"**Data wygenerowania (UTC):** {generated_at}",
    ])


    interview_file = (
        INTERVIEW_OUTPUT_DIR
        / f"interview_{safe_from_id}_to_{safe_to_id}.json"
    )

    if not interview_file.exists():
        raise ValueError(
            "Nie znaleziono wywiadu. "
            "Przed wygenerowaniem dokumentu należy przeprowadzić wywiad."
        )

    interview_state = json.loads(
        interview_file.read_text(encoding="utf-8")
    )

    if interview_state["status"] != "completed":
        raise ValueError(
            "Wywiad nie został zakończony. "
            f"Zapisano {len(interview_state['answers'])}/"
            f"{len(load_interview_questions())} odpowiedzi."
        )

    lines.extend([
        "",
        "## 11. Informacje z wywiadu",
        "",
        "Poniższe informacje pochodzą z odpowiedzi udzielonych "
        "przez pracownika przekazującego obowiązki.",
        "Nie zostały automatycznie zweryfikowane w systemach firmowych.",
        "",
    ])

    for interview_answer in interview_state["answers"]:
        lines.extend([
            f"### {interview_answer['section']} — "
            f"{interview_answer['question']}",
            "",
            f"**Odpowiedź pracownika:** "
            f"{interview_answer['answer']}",
            "",
            "**Źródło:** wywiad z pracownikiem przekazującym obowiązki.",
            "",
        ])


    document = "\n".join(lines)

    HANDOVER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
# NARZĘDZIE MCP – ZATWIERDZANIE DOKUMENTU
# --------------------------------------------------

@mcp.tool()
def approve_handover_doc(
    from_employee_id: str,
    to_employee_id: str,
    from_employee_confirmed: bool,
    to_employee_confirmed: bool,
    approved_by_employee_id: str
) -> str:
    """Rejestruje potwierdzenia stron i zatwierdzenie dokumentu."""

    source_employee = find_employee(from_employee_id)
    target_employee = find_employee(to_employee_id)
    approver = find_employee(approved_by_employee_id)

    if source_employee["department"] != target_employee["department"]:
        raise ValueError("Pracownicy należą do różnych działów.")

    if approver["department"] != source_employee["department"]:
        raise ValueError(
            "Osoba zatwierdzająca musi należeć do tego samego działu."
        )

    if not from_employee_confirmed or not to_employee_confirmed:
        raise ValueError(
            "Obie strony muszą potwierdzić zapoznanie się z dokumentem."
        )

    safe_from_id = re.sub(
        r"[^a-zA-Z0-9_-]", "_", from_employee_id
    )
    safe_to_id = re.sub(
        r"[^a-zA-Z0-9_-]", "_", to_employee_id
    )

    document_file = (
        HANDOVER_OUTPUT_DIR
        / f"handover_{safe_from_id}_to_{safe_to_id}.md"
    )

    if not document_file.exists():
        raise FileNotFoundError(
            "Nie znaleziono dokumentu przekazania obowiązków."
        )

    interview_file = (
        INTERVIEW_OUTPUT_DIR
        / f"interview_{safe_from_id}_to_{safe_to_id}.json"
    )

    if not interview_file.exists():
        raise ValueError(
            "Nie znaleziono wywiadu. Nie można zatwierdzić dokumentu."
        )

    interview_state = json.loads(
        interview_file.read_text(encoding="utf-8")
    )

    if interview_state["status"] != "completed":
        raise ValueError(
            "Nie można zatwierdzić dokumentu. Wywiad nie został zakończony."
        )
    
    status_file = (
        HANDOVER_OUTPUT_DIR
        / f"handover_{safe_from_id}_to_{safe_to_id}_status.json"
    )
    
    if status_file.exists():
        previous_status = json.loads(
            status_file.read_text(encoding="utf-8")
        )

        if previous_status["status"] == "published":
            raise ValueError(
                "Dokument został już opublikowany. "
                "Nie można go ponownie zatwierdzić."
            )
    
    approval_data = {
        "status": "approved",
        "from_employee": from_employee_id,
        "to_employee": to_employee_id,
        "from_employee_confirmed": True,
        "to_employee_confirmed": True,
        "approved_by": approved_by_employee_id,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "identity_verified": False
    }

    status_file.write_text(
        json.dumps(approval_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return format_result({
        "status": "approved",
        "message": "Dokument został zatwierdzony.",
        "approved_by": approved_by_employee_id,
        "status_file": str(status_file.relative_to(BASE_DIR))
    })


# --------------------------------------------------
# NARZĘDZIE MCP – PUBLIKOWANIE DOKUMENTU ONBOARDINGOWEGO
# --------------------------------------------------

@mcp.tool()
def publish_to_onboarding(
    from_employee_id: str,
    to_employee_id: str
) -> str:
    """Publikuje zatwierdzony dokument w bazie onboardingowej."""

    source_employee = find_employee(from_employee_id)
    target_employee = find_employee(to_employee_id)

    if source_employee["department"] != target_employee["department"]:
        raise ValueError("Pracownicy należą do różnych działów.")

    safe_from_id = re.sub(
        r"[^a-zA-Z0-9_-]", "_", from_employee_id
    )
    safe_to_id = re.sub(
        r"[^a-zA-Z0-9_-]", "_", to_employee_id
    )

    document_file = (
        HANDOVER_OUTPUT_DIR
        / f"handover_{safe_from_id}_to_{safe_to_id}.md"
    )

    status_file = (
        HANDOVER_OUTPUT_DIR
        / f"handover_{safe_from_id}_to_{safe_to_id}_status.json"
    )

    interview_file = (
        INTERVIEW_OUTPUT_DIR
        / f"interview_{safe_from_id}_to_{safe_to_id}.json"
    )

    if not document_file.exists():
        raise FileNotFoundError(
            "Nie znaleziono dokumentu przekazania obowiązków."
        )

    if not interview_file.exists():
        raise ValueError("Nie znaleziono wywiadu.")

    interview_state = json.loads(
        interview_file.read_text(encoding="utf-8")
    )

    if interview_state["status"] != "completed":
        raise ValueError(
            "Nie można opublikować dokumentu. Wywiad nie został zakończony."
        )

    if not status_file.exists():
        raise ValueError(
            "Dokument nie został zatwierdzony."
        )

    approval_data = json.loads(
        status_file.read_text(encoding="utf-8")
    )

    if approval_data["status"] != "approved":
        raise ValueError(
            "Dokument nie ma statusu zatwierdzonego."
        )

    document_text = document_file.read_text(encoding="utf-8")

    referenced_documents = list(dict.fromkeys(
        re.findall(r"\bD\d{3}\b", document_text)
    ))

    inaccessible_documents = [
        doc_id
        for doc_id in referenced_documents
        if not check_access(to_employee_id, doc_id)
    ]

    if inaccessible_documents:
        raise PermissionError(
            "Pracownik przejmujący nie ma dostępu do dokumentów: "
            + ", ".join(inaccessible_documents)
        )

    ONBOARDING_OUTPUT_DIR.mkdir(
        parents=True, exist_ok=True
    )

    published_file = (
        ONBOARDING_OUTPUT_DIR
        / document_file.name
    )

    published_file.write_text(
        document_text,
        encoding="utf-8"
    )

    approval_data["status"] = "published"
    approval_data["published_at"] = datetime.now(
        timezone.utc
    ).isoformat()
    approval_data["published_file"] = str(
        published_file.relative_to(BASE_DIR)
    )

    status_file.write_text(
        json.dumps(
            approval_data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return format_result({
        "status": "published",
        "message": "Dokument został opublikowany w bazie onboardingowej.",
        "from_employee": from_employee_id,
        "to_employee": to_employee_id,
        "file_path": str(published_file.relative_to(BASE_DIR)),
        "referenced_documents": referenced_documents
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
    11. Przedstaw dokument obu stronom do weryfikacji.
    12. Użyj approve_handover_doc po potwierdzeniu dokumentu przez obie strony.
    13. Użyj publish_to_onboarding, aby opublikować zatwierdzony dokument.
    14. Nie zmieniaj automatycznie przypisania zadań.

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
