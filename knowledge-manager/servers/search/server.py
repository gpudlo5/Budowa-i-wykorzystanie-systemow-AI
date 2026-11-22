import json
import sys
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from servers.search.search_engine import SearchEngine

mcp = FastMCP("Nordwind Search")

AUDIT_FILE = BASE_DIR / "data" / "processed" / "audit_log.jsonl"

# Stan demonstracyjnej sesji.
active_employee_id = None

# Inicjalizacja wyszukiwarki.
with redirect_stdout(sys.stderr):
    engine = SearchEngine()
    engine.index_documents()


def write_audit_event(event_type, actor_id=None, details=None):
    """
    Zapisuje zdarzenie do lokalnego dziennika audytu.
    Każde zdarzenie jest osobnym wierszem JSON.
    """
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "actor_id": actor_id,
        "details": details or {},
    }

    with open(AUDIT_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event


@mcp.tool()
def login_as(employee_id: str) -> str:
    """
    Ustawia pracownika jako aktywnego użytkownika demonstracyjnej sesji.
    """
    global active_employee_id

    if not employee_id.strip():
        raise ValueError("Identyfikator pracownika nie moze byc pusty.")

    employee = engine.get_employee(employee_id)

    active_employee_id = employee_id

    write_audit_event(
        event_type="login",
        actor_id=employee_id,
        details={
            "employee_name": (
                employee["first_name"] + " " + employee["last_name"]
            ),
            "department": employee["department"],
        },
    )

    return json.dumps(
        {
            "status": "success",
            "employee_id": employee_id,
            "employee_name": (
                employee["first_name"] + " " + employee["last_name"]
            ),
            "department": employee["department"],
            "message": "Pracownik zostal ustawiony jako aktywny uzytkownik sesji.",
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def check_access(user_id: str, doc_id: str) -> str:
    """
    Sprawdza, czy wskazany pracownik ma dostęp do dokumentu na podstawie ACL.
    """
    if not user_id.strip() or not doc_id.strip():
        raise ValueError("user_id i doc_id nie moga byc puste.")

    has_access = engine.check_access(user_id, doc_id)

    write_audit_event(
        event_type="access_check",
        actor_id=user_id,
        details={
            "doc_id": doc_id,
            "access_granted": has_access,
        },
    )

    return json.dumps(
        {
            "user_id": user_id,
            "doc_id": doc_id,
            "access_granted": has_access,
            "message": (
                "Dostep przyznany."
                if has_access
                else "Dostep zabroniony lub dokument nie istnieje."
            ),
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def log_event(event_type: str, details: str = "") -> str:
    """
    Zapisuje zdarzenie w dzienniku audytu.
    """
    if not event_type.strip():
        raise ValueError("Typ zdarzenia nie moze byc pusty.")

    event = write_audit_event(
        event_type=event_type,
        actor_id=active_employee_id,
        details={
            "description": details,
        },
    )

    return json.dumps(
        {
            "status": "logged",
            "event": event,
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def search_documents(question: str, n_results: int = 3) -> str:
    """
    Wyszukuje dokumenty firmowe dla aktywnego pracownika,
    z uwzglednieniem uprawnien ACL.
    """
    if not question.strip():
        raise ValueError("Pytanie nie moze byc puste.")

    if active_employee_id is None:
        raise ValueError(
            "Najpierw wywolaj login_as(employee_id)."
        )

    if n_results < 1 or n_results > 10:
        raise ValueError("Liczba wynikow musi wynosic od 1 do 10.")

    results = engine.search(
        question=question,
        employee_id=active_employee_id,
        n_results=n_results,
    )

    output = []

    if results and results.get("documents") and results["documents"][0]:
        for document, metadata in zip(
            results["documents"][0],
            results["metadatas"][0],
        ):
            output.append({
                "doc_id": metadata["doc_id"],
                "title": metadata["title"],
                "department": metadata["department"],
                "doc_type": metadata["doc_type"],
                "content": document,
            })

    write_audit_event(
        event_type="document_search",
        actor_id=active_employee_id,
        details={
            "question": question,
            "results_count": len(output),
        },
    )

    return json.dumps(
        {
            "employee_id": active_employee_id,
            "question": question,
            "results_count": len(output),
            "results": output,
            "note": "Wyniki uwzgledniaja uprawnienia ACL pracownika.",
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.resource("search://guidelines")
def search_guidelines() -> str:
    return """
    WYSZUKIWANIE DOKUMENTOW – NORDWIND LOGISTICS

    1. Najpierw wywolaj login_as(employee_id).
    2. Ustal aktywnego pracownika.
    3. W razie potrzeby sprawdz dostep przez check_access(user_id, doc_id).
    4. Wyszukuj dokumenty przez search_documents.
    5. Wyniki sa ograniczane przez mechanizm ACL.
    6. Nie ujawniaj tresci dokumentow niedostepnych dla pracownika.
    7. Jesli nie znaleziono odpowiedniego dokumentu, poinformuj o tym.
    8. Zdarzenia sa zapisywane w dzienniku audytu.
    """


if __name__ == "__main__":
    mcp.run(transport="stdio")