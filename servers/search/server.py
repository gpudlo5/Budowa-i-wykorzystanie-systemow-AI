
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from servers.search.search_engine import SearchEngine

mcp = FastMCP("Nordwind Search")

# Inicjalizacja wyszukiwarki i indeksowanie dokumentow.
# Komunikaty diagnostyczne kierujemy do stderr,
# poniewaz stdout jest wykorzystywany przez protokol MCP.
with redirect_stdout(sys.stderr):
    engine = SearchEngine()
    engine.index_documents()


@mcp.tool()
def search_documents(question: str, employee_id: str, n_results: int = 3) -> str:
    """
    Wyszukuje dokumenty firmowe z uwzglednieniem uprawnien ACL pracownika.
    Zwraca tresc dokumentow, tytuly i identyfikatory zrodel.
    """
    if not question.strip():
        raise ValueError("Pytanie nie moze byc puste.")

    if n_results < 1 or n_results > 10:
        raise ValueError("Liczba wynikow musi wynosic od 1 do 10.")

    results = engine.search(
        question=question,
        employee_id=employee_id,
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

    return json.dumps(
        {
            "employee_id": employee_id,
            "question": question,
            "results_count": len(output),
            "results": output,
            "note": "Wyniki wyszukiwania uwzgledniaja uprawnienia ACL pracownika."
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.resource("search://guidelines")
def search_guidelines() -> str:
    return """
    WYSZUKIWANIE DOKUMENTOW – NORDWIND LOGISTICS

    1. Ustal identyfikator pracownika.
    2. Sprawdz role pracownika.
    3. Ogranicz wyszukiwanie do dokumentow dozwolonych przez ACL.
    4. Wyszukaj dokumenty semantycznie.
    5. Przedstaw tresc i identyfikatory znalezionych dokumentow.
    6. Nie ujawniaj tresci dokumentow niedostepnych dla pracownika.
    7. Jesli nie znaleziono odpowiedniego dokumentu, poinformuj o tym.
    """


if __name__ == "__main__":
    mcp.run(transport="stdio")
