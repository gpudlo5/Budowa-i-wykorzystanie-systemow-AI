
import csv
from pathlib import Path

DATA_DIR = Path(__file__).parent / "raw"


def load_csv(filename):
    """Wczytuje plik CSV i zwraca listę rekordów."""
    file_path = DATA_DIR / filename

    with file_path.open(
        mode="r",
        encoding="utf-8",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def check_unique_ids(rows, field, filename, errors):
    """Sprawdza, czy identyfikatory się nie powtarzają."""
    ids = [row[field] for row in rows]

    if len(ids) != len(set(ids)):
        errors.append(
            f"{filename}: znaleziono powtorzone identyfikatory w {field}"
        )


def validate_data():
    errors = []

    employees = load_csv("employees.csv")
    projects = load_csv("projects.csv")
    documents = load_csv("documents.csv")
    acl = load_csv("acl.csv")

    # Tworzymy zbiory identyfikatorow pracownikow
    employee_ids = {
        employee["employee_id"]
        for employee in employees
    }

    # Zbior identyfikatorow dokumentow
    document_ids = {
        document["doc_id"]
        for document in documents
    }

    # 1. Unikalnosc identyfikatorow
    check_unique_ids(
        employees, "employee_id", "employees.csv", errors
    )

    check_unique_ids(
        projects, "project_id", "projects.csv", errors
    )

    check_unique_ids(
        documents, "doc_id", "documents.csv", errors
    )

    # 2. Sprawdzanie wlascicieli projektow
    for project in projects:
        if project["owner_id"] not in employee_ids:
            errors.append(
                f"Projekt {project['project_id']} ma nieznanego wlasciciela"
            )

    # 3. Sprawdzanie autorow i wlascicieli dokumentow
    for document in documents:
        if document["author_id"] not in employee_ids:
            errors.append(
                f"Dokument {document['doc_id']} ma nieznanego autora"
            )

        if document["owner_id"] not in employee_ids:
            errors.append(
                f"Dokument {document['doc_id']} ma nieznanego wlasciciela"
            )

    # 4. Sprawdzanie uprawnien
    acl_document_ids = {
        row["doc_id"] for row in acl
    }

    for doc_id in document_ids:
        if doc_id not in acl_document_ids:
            errors.append(
                f"Dokument {doc_id} nie ma zdefiniowanych uprawnien"
            )

    for row in acl:
        if row["doc_id"] not in document_ids:
            errors.append(
                f"Uprawnienia odnosza sie do nieistniejacego dokumentu: {row['doc_id']}"
            )

    # Wynik walidacji
    if errors:
        print("\nWALIDACJA NIE POWIODLA SIE:\n")

        for error in errors:
            print(f"- {error}")

        return False

    print("\nWALIDACJA ZAKONCZONA SUKCESEM")
    print(f"Liczba pracownikow: {len(employees)}")
    print(f"Liczba projektow: {len(projects)}")
    print(f"Liczba dokumentow: {len(documents)}")
    print(f"Liczba wpisow ACL: {len(acl)}")

    return True


if __name__ == "__main__":
    validate_data()
