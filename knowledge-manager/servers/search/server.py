"""
server.py - Search MCP (Knowledge Manager, Northway Ltd.).

Narzedzia: login_as, check_access, search_documents, get_document, log_event.
Zasob: search://guidelines.

Uwaga: w serwerze stdio nic nie moze pisac na stdout (to kanal protokolu MCP).
Komunikaty diagnostyczne ida na stderr.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from servers.common.config import AUDIT_LOG, DEFAULT_TOP_K, MAX_TOP_K  # noqa: E402
from servers.search.search_engine import SearchEngine  # noqa: E402

mcp = FastMCP("Northway Search")

# Stan demonstracyjnej sesji.
active_employee_id = None

# Tworzenie silnika jest tanie: model i baza laduja sie dopiero przy pierwszym pytaniu.
engine = SearchEngine()


def write_audit_event(event_type, actor_id=None, details=None):
    """Zapisuje zdarzenie do dziennika audytu (jeden wiersz JSON na zdarzenie)."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "actor_id": actor_id,
        "details": details or {},
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def _require_login():
    if active_employee_id is None:
        raise ValueError("Najpierw wywolaj login_as(employee_id).")
    return active_employee_id


def _json(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
def login_as(employee_id: str) -> str:
    """
    Ustawia pracownika (np. "E003") jako aktywnego uzytkownika sesji.
    Wywolaj to jako pierwsze: od grupy dostepu pracownika zalezy,
    jakie dokumenty zobaczy w wynikach wyszukiwania.
    """
    global active_employee_id

    if not employee_id.strip():
        raise ValueError("Identyfikator pracownika nie moze byc pusty.")

    employee = engine.get_employee(employee_id.strip())
    active_employee_id = employee["employee_id"]

    write_audit_event(
        "login",
        actor_id=active_employee_id,
        details={
            "employee_name": employee["full_name"],
            "department": employee["department"],
            "access_group": employee["access_group"],
        },
    )

    return _json({
        "status": "success",
        "employee_id": employee["employee_id"],
        "employee_name": employee["full_name"],
        "role": employee["role"],
        "department": employee["department"],
        "access_group": employee["access_group"],
        "employment_status": employee["status"],
        "message": "Pracownik zostal ustawiony jako aktywny uzytkownik sesji.",
    })


@mcp.tool()
def check_access(user_id: str, doc_id: str) -> str:
    """
    Sprawdza, czy pracownik user_id ma dostep do dokumentu, zgloszenia lub watku doc_id
    (np. "D021", "T005", "W01"). Gdy dokument nie istnieje, wynik jest taki sam jak
    przy braku uprawnien.
    """
    if not user_id.strip() or not doc_id.strip():
        raise ValueError("user_id i doc_id nie moga byc puste.")

    has_access = engine.check_access(user_id.strip(), doc_id.strip())

    write_audit_event(
        "access_check",
        actor_id=user_id,
        details={"doc_id": doc_id, "access_granted": has_access},
    )

    return _json({
        "user_id": user_id,
        "doc_id": doc_id,
        "access_granted": has_access,
        "message": "Dostep przyznany." if has_access else "Dostep zabroniony lub dokument nie istnieje.",
    })


@mcp.tool()
def search_documents(question: str, n_results: int = DEFAULT_TOP_K) -> str:
    """
    Wyszukuje fragmenty dokumentow, zgloszen i watkow firmowych dla aktywnego pracownika
    (po znaczeniu pytania, nie po slowach kluczowych). Zwraca tylko to, do czego pracownik
    ma uprawnienia. Kazdy wynik ma doc_id, tytul, sekcje, date ostatniej zmiany
    i distance (im mniejsza, tym lepsze dopasowanie). Pytaj pelnym zdaniem po polsku.
    Gdy potrzebujesz calej tresci, wywolaj get_document(doc_id).
    """
    if not question.strip():
        raise ValueError("Pytanie nie moze byc puste.")
    employee_id = _require_login()
    if n_results < 1 or n_results > MAX_TOP_K:
        raise ValueError(f"Liczba wynikow musi wynosic od 1 do {MAX_TOP_K}.")

    results = engine.search(question=question, employee_id=employee_id, n_results=n_results)

    write_audit_event(
        "document_search",
        actor_id=employee_id,
        details={
            "question": question,
            "results_count": len(results),
            "doc_ids": [r["doc_id"] for r in results],
        },
    )

    return _json({
        "employee_id": employee_id,
        "question": question,
        "results_count": len(results),
        "results": results,
        "note": (
            "Wyniki uwzgledniaja uprawnienia pracownika. "
            "Przy duzych wartosciach distance dopasowanie jest slabe - nie traktuj go jako odpowiedzi."
        ),
    })


@mcp.tool()
def get_document(doc_id: str) -> str:
    """
    Zwraca pelna tresc dokumentu, zgloszenia lub watku (np. "D004", "T005", "W01")
    dla aktywnego pracownika, zlozona ze wszystkich fragmentow. Uzyj po search_documents,
    gdy fragment to za malo. Przy braku uprawnien lub nieistniejacym doc_id zwraca
    ten sam komunikat o braku dostepu.
    """
    if not doc_id.strip():
        raise ValueError("doc_id nie moze byc pusty.")
    employee_id = _require_login()

    document = engine.get_document(doc_id.strip(), employee_id)

    write_audit_event(
        "document_read",
        actor_id=employee_id,
        details={"doc_id": doc_id, "access_granted": document is not None},
    )

    if document is None:
        return _json({
            "doc_id": doc_id,
            "access_granted": False,
            "message": "Dostep zabroniony lub dokument nie istnieje.",
        })
    return _json({"access_granted": True, **document})


@mcp.tool()
def log_event(event_type: str, details: str = "") -> str:
    """Zapisuje wlasne zdarzenie (np. wynik rozmowy) w dzienniku audytu."""
    if not event_type.strip():
        raise ValueError("Typ zdarzenia nie moze byc pusty.")

    event = write_audit_event(
        event_type, actor_id=active_employee_id, details={"description": details}
    )
    return _json({"status": "logged", "event": event})


@mcp.resource("search://guidelines")
def search_guidelines() -> str:
    return """
    WYSZUKIWANIE WIEDZY - NORTHWAY LTD.

    1. Najpierw wywolaj login_as(employee_id). Bez tego wyszukiwanie nie dziala.
    2. Szukaj przez search_documents (pytanie pelnym zdaniem po polsku).
    3. Gdy fragment to za malo, pobierz calosc przez get_document(doc_id).
    4. Odpowiadaj wylacznie na podstawie znalezionych zrodel i podawaj doc_id
       oraz date ostatniej zmiany (last_modified) przy kazdej informacji.
    5. Jesli zrodla sie wykluczaja (np. stara i nowa wersja procedury), wskaz
       roznice, podaj ktore jest nowsze i zaznacz, ze trzeba to potwierdzic.
    6. Jesli nic nie pasuje albo distance jest duze, odpowiedz "nie znalazlem
       tego w bazie wiedzy". Niczego nie zgaduj.
    7. Nie ujawniaj tresci dokumentow niedostepnych dla pracownika. Brak wyniku
       moze oznaczac brak uprawnien - nie sugeruj, ze taki dokument istnieje.
    8. Zdarzenia (logowanie, wyszukiwania, odczyty) trafiaja do dziennika audytu.
    """


if __name__ == "__main__":
    mcp.run(transport="stdio")