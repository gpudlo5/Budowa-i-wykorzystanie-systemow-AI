"""
server.py - Search MCP (Knowledge Manager, Northway Ltd.).

Narzedzia:  check_access, search_documents, get_document, log_event.
Zasob: search://guidelines, org://me, org://processes, org://systems, search://catalog, doc://{doc_id}.
Prompty: ask_knowledge_base, compare_procedures, onboarding_brief.

Uwaga: w serwerze stdio nic nie moze pisac na stdout (to kanal protokolu MCP).
Komunikaty diagnostyczne ida na stderr.
"""

import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from servers.common.config import AUDIT_LOG, DEFAULT_TOP_K, MAX_TOP_K, CURRENT_USER_ID  # noqa: E402
from servers.search.search_engine import SearchEngine  # noqa: E402
from servers.common.access import can_access   # noqa: E402
from servers.common.data import load_csv       # noqa: E402

mcp = FastMCP("Northway Search")


# Tworzenie silnika jest tanie: model i baza laduja sie dopiero przy pierwszym pytaniu.
engine = SearchEngine()

# Model i baze laduje sie w tle od razu po starcie, zeby pierwsze pytanie nie czekalo.
threading.Thread(target=engine.warm_up, daemon=True).start()

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


def _current_user():
    if CURRENT_USER_ID is None:
        raise ValueError("Brak KM_USER_ID w konfiguracji serwera (claude_desktop_config.json, sekcja env).")
    return engine.get_employee(CURRENT_USER_ID)["employee_id"]


def _json(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2)



@mcp.tool()
def check_access( doc_id: str) -> str:
    """
    Sprawdza, czy biezacy uzytkownik ma dostep do dokumentu, zgloszenia lub watku doc_id
    (np. "D021", "T005", "W01"). Gdy dokument nie istnieje, wynik jest taki sam jak
    przy braku uprawnien.
    """
    if not doc_id.strip():
        raise ValueError("doc_id nie moze byc pusty.")
    employee_id = _current_user()

    has_access = engine.check_access(employee_id, doc_id.strip())

    write_audit_event(
        "access_check",
        actor_id=employee_id,
        details={"doc_id": doc_id, "access_granted": has_access},
    )

    return _json({
        "user_id": employee_id,
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
    employee_id = _current_user()
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
    employee_id = _current_user()

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
        event_type, actor_id=_current_user(), details={"description": details}
    )
    return _json({"status": "logged", "event": event})


@mcp.resource("search://guidelines")
def search_guidelines() -> str:
    return """
    WYSZUKIWANIE WIEDZY - NORTHWAY LTD.

    1. Serwer dziala w imieniu pracownika ustawionego w konfiguracji (KM_USER_ID).
       Nie da sie go zmienic w trakcie rozmowy - nie pros o podanie innego identyfikatora.
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
    8. Wyszukiwania, odczyty i sprawdzenia dostepu trafiaja do dziennika audytu.
    9. Liste dostepnych dokumentow zawiera zasob search://catalog.
    """

@mcp.resource("org://me")
def resource_me() -> str:
    """Profil biezacego uzytkownika."""
    e = engine.get_employee(_current_user())
    write_audit_event("resource_read", actor_id=e["employee_id"], details={"uri": "org://me"})
    keys = ["employee_id", "full_name", "role", "department", "access_group", "status"]
    return _json({k: e[k] for k in keys})


@mcp.resource("org://processes")
def resource_processes() -> str:
    """Lista procesow firmy."""
    return _json(load_csv("processes.csv"))


@mcp.resource("org://systems")
def resource_systems() -> str:
    """Lista systemow IT firmy."""
    return _json(load_csv("systems.csv"))


@mcp.resource("search://catalog")
def resource_catalog() -> str:
    """Dokumenty dostepne dla biezacego uzytkownika (bez tresci)."""
    user = _current_user()
    docs = [
        {k: r[k] for k in ("doc_id", "title", "doc_type", "last_modified")}
        for r in load_csv("documents_plan.csv")
        if can_access(user, r["doc_id"])
    ]
    write_audit_event("resource_read", actor_id=user,
                      details={"uri": "search://catalog", "count": len(docs)})
    return _json({"employee_id": user, "documents": docs})


@mcp.resource("doc://{doc_id}")
def resource_document(doc_id: str) -> str:
    """Pelna tresc dokumentu - te same uprawnienia i audyt co get_document."""
    return get_document(doc_id)

@mcp.prompt()
def ask_knowledge_base(question: str) -> str:
    """Odpowiedz na pytanie na podstawie bazy wiedzy, ze zrodlami."""
    return (
        f"Pytanie pracownika: {question}\n\n"
        "Odpowiedz wylacznie na podstawie narzedzi Northway Search:\n"
        "1. Uzyj search_documents (pelne zdanie po polsku).\n"
        "2. Gdy fragment nie wystarcza, pobierz calosc przez get_document.\n"
        "3. Przy kazdej informacji podaj doc_id i last_modified.\n"
        "4. Gdy nic nie pasuje albo distance jest duze, odpowiedz: "
        "'Nie znalazlem tego w bazie wiedzy'. Niczego nie zgaduj."
    )


@mcp.prompt()
def compare_procedures(topic: str) -> str:
    """Porownaj rozne wersje procedury na dany temat."""
    return (
        f"Temat: {topic}\n\n"
        "Znajdz przez search_documents wszystkie dokumenty opisujace ten temat "
        "(procedury, instrukcje, skrocone wersje). Pobierz je przez get_document. "
        "Wypisz roznice (terminy, limity, osoby zatwierdzajace), wskaz nowsza wersje "
        "wedlug last_modified i zaznacz, co trzeba potwierdzic z wlascicielem dokumentu."
    )


@mcp.prompt()
def onboarding_brief() -> str:
    """Wprowadzenie dla biezacego pracownika: procesy dzialu i dokumenty do przeczytania."""
    me = json.loads(resource_me())
    department_id = engine.get_employee(me["employee_id"])["department_id"]
    processes = [p for p in load_csv("processes.csv") if p["department_id"] == department_id]
    catalog = json.loads(resource_catalog())["documents"]

    return (
        "Przygotuj wprowadzenie dla nowego pracownika na podstawie danych ponizej.\n\n"
        f"PRACOWNIK:\n{_json(me)}\n\n"
        f"PROCESY JEGO DZIALU:\n{_json(processes)}\n\n"
        f"DOKUMENTY, DO KTORYCH MA DOSTEP:\n{_json(catalog)}\n\n"
        "Opisz: 1) za jakie procesy odpowiada dzial i ktore systemy sa w nich uzywane, "
        "2) 5 najwazniejszych dokumentow do przeczytania na poczatek (z doc_id i powodem). "
        "Szczegoly procedur sprawdzaj przez get_document i podawaj doc_id. "
        "Nie wymyslaj procesow ani dokumentow spoza tej listy."
    )

if __name__ == "__main__":
    mcp.run(transport="stdio")