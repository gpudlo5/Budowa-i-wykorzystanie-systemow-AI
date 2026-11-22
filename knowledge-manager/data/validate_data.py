
import csv
from pathlib import Path
from datetime import date

DATA_DIR = Path(__file__).parent / "raw"


def load_csv(filename):
    """Wczytuje plik CSV i zwraca listę rekordów."""
    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Brak pliku: {filename}")

    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def check_unique_ids(rows, field, filename, errors):
    """Sprawdza unikalność identyfikatorów."""
    ids = [row[field] for row in rows]

    if len(ids) != len(set(ids)):
        errors.append(
            f"{filename}: powtorzone identyfikatory w polu {field}"
        )


def check_date(value, field, record_id, errors):
    """Sprawdza poprawność daty w formacie RRRR-MM-DD."""
    try:
        date.fromisoformat(value)
    except (ValueError, TypeError):
        errors.append(
            f"{record_id}: niepoprawna data w polu {field}: {value}"
        )


def validate_data():
    errors = []

    # 1. Wczytanie wszystkich plikow
    employees = load_csv("employees.csv")
    projects = load_csv("projects.csv")
    documents = load_csv("documents.csv")
    acl = load_csv("acl.csv")
    clients = load_csv("clients.csv")
    tickets = load_csv("tickets.csv")
    threads = load_csv("threads.csv")
    recurring_tasks = load_csv("recurring_tasks.csv")

    # 2. Zbiory identyfikatorow
    employee_ids = {row["employee_id"] for row in employees}
    project_ids = {row["project_id"] for row in projects}
    document_ids = {row["doc_id"] for row in documents}
    client_ids = {row["client_id"] for row in clients}
    ticket_ids = {row["ticket_id"] for row in tickets}

    employee_roles = {row["role_id"] for row in employees}

    # 3. Unikalnosc identyfikatorow
    unique_checks = [
        (employees, "employee_id", "employees.csv"),
        (projects, "project_id", "projects.csv"),
        (documents, "doc_id", "documents.csv"),
        (clients, "client_id", "clients.csv"),
        (tickets, "ticket_id", "tickets.csv"),
        (threads, "thread_id", "threads.csv"),
        (recurring_tasks, "task_id", "recurring_tasks.csv"),
    ]

    for rows, field, filename in unique_checks:
        check_unique_ids(rows, field, filename, errors)

    # 4. Projekty
    for project in projects:
        if project["owner_id"] not in employee_ids:
            errors.append(
                f"Projekt {project['project_id']}: nieznany wlasciciel"
            )

    # 5. Dokumenty
    for document in documents:
        if document["author_id"] not in employee_ids:
            errors.append(
                f"Dokument {document['doc_id']}: nieznany autor"
            )

        if document["owner_id"] not in employee_ids:
            errors.append(
                f"Dokument {document['doc_id']}: nieznany wlasciciel"
            )

    # 6. Uprawnienia ACL
    acl_document_ids = {row["doc_id"] for row in acl}

    for doc_id in document_ids:
        if doc_id not in acl_document_ids:
            errors.append(
                f"Dokument {doc_id}: brak uprawnien ACL"
            )

    for row in acl:
        if row["doc_id"] not in document_ids:
            errors.append(
                f"ACL: nieistniejacy dokument {row['doc_id']}"
            )

        roles = row["allowed_roles"].split(";")

        for role in roles:
            if role not in employee_roles:
                errors.append(
                    f"ACL: nieznana rola {role} dla dokumentu {row['doc_id']}"
                )

    # 7. Klienci
    for client in clients:
        if not client["company_name"]:
            errors.append(
                f"Klient {client['client_id']}: brak nazwy firmy"
            )

    # 8. Zgloszenia
    for ticket in tickets:
        ticket_id = ticket["ticket_id"]

        if ticket["client_id"] not in client_ids:
            errors.append(
                f"Zgloszenie {ticket_id}: nieznany klient"
            )

        if ticket["assigned_to"] not in employee_ids:
            errors.append(
                f"Zgloszenie {ticket_id}: nieznany pracownik"
            )

        project_id = ticket["related_project_id"]

        if project_id and project_id not in project_ids:
            errors.append(
                f"Zgloszenie {ticket_id}: nieznany projekt {project_id}"
            )

        check_date(
            ticket["created_at"], "created_at", ticket_id, errors
        )
        check_date(
            ticket["due_date"], "due_date", ticket_id, errors
        )

    # 9. Watki korespondencji
    for thread in threads:
        thread_id = thread["thread_id"]

        if thread["ticket_id"] not in ticket_ids:
            errors.append(
                f"Watek {thread_id}: nieznane zgloszenie"
            )
        else:
            related_ticket = next(
                ticket for ticket in tickets
                if ticket["ticket_id"] == thread["ticket_id"]
            )

            if thread["client_id"] != related_ticket["client_id"]:
                errors.append(
                    f"Watek {thread_id}: klient nie zgadza sie ze zgloszeniem"
                )

        if thread["client_id"] not in client_ids:
            errors.append(
                f"Watek {thread_id}: nieznany klient"
            )

        if thread["assigned_to"] not in employee_ids:
            errors.append(
                f"Watek {thread_id}: nieznany pracownik"
            )

        check_date(
            thread["last_message_at"],
            "last_message_at",
            thread_id,
            errors
        )

    # 10. Zadania cykliczne
    allowed_frequencies = {"daily", "weekly", "monthly"}

    for task in recurring_tasks:
        task_id = task["task_id"]

        if task["assigned_to"] not in employee_ids:
            errors.append(
                f"Zadanie {task_id}: nieznany pracownik"
            )

        if task["department"] not in {
            employee["department"]
            for employee in employees
            if employee["employee_id"] == task["assigned_to"]
        }:
            errors.append(
                f"Zadanie {task_id}: dzial nie zgadza sie z pracownikiem"
            )

        if task["frequency"] not in allowed_frequencies:
            errors.append(
                f"Zadanie {task_id}: nieznana czestotliwosc"
            )

        if task["related_project_id"]:
            if task["related_project_id"] not in project_ids:
                errors.append(
                    f"Zadanie {task_id}: nieznany projekt"
                )

        check_date(
            task["next_run"], "next_run", task_id, errors
        )
        check_date(
            task["due_date"], "due_date", task_id, errors
        )

    # 11. Wynik walidacji
    if errors:
        print("\nWALIDACJA NIE POWIODLA SIE:\n")

        for error in errors:
            print(f"- {error}")

        print(f"\nLiczba bledow: {len(errors)}")
        return False

    print("\nWALIDACJA ZAKONCZONA SUKCESEM")
    print(f"Liczba pracownikow: {len(employees)}")
    print(f"Liczba projektow: {len(projects)}")
    print(f"Liczba dokumentow: {len(documents)}")
    print(f"Liczba wpisow ACL: {len(acl)}")
    print(f"Liczba klientow: {len(clients)}")
    print(f"Liczba zgloszen: {len(tickets)}")
    print(f"Liczba watkow: {len(threads)}")
    print(f"Liczba zadan cyklicznych: {len(recurring_tasks)}")

    return True


if __name__ == "__main__":
    validate_data()
