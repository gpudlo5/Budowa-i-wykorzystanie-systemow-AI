"""
search_engine.py - silnik wyszukiwania Knowledge Managera (Northway Ltd.).

Silnik tylko CZYTA baze zbudowana przez ingest.py. Niczego nie indeksuje.

Jak dziala wyszukiwanie:
  1. pytanie dostaje przedrostek QUERY_PREFIX i zamienia sie na wektor (ten sam model co w ingest.py),
  2. ChromaDB zwraca najblizsze fragmenty, ale tylko takie, do ktorych grupa dostepu
     pracownika ma uprawnienie (flagi acl_all / acl_<grupa> w metadanych),
  3. wynik to lista fragmentow z danymi do cytowania (doc_id, tytul, sekcja, data, odleglosc).

Model ladowany jest dopiero przy pierwszym pytaniu, zeby serwer MCP startowal szybko.
"""

import os
import sys
import threading
import time
from pathlib import Path

# Wylaczam telemetrie Chroma, zanim biblioteka zostanie zaimportowana.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from servers.common.config import (  # noqa: E402
    COLLECTION_NAME, DB_DIR, DEFAULT_TOP_K, MAX_TOP_K, MODEL_NAME,
    QUERY_PREFIX, acl_key,
)
from servers.common.org import Org  # noqa: E402

# Opcjonalny prog: wyniki z odlegloscia wieksza niz ta wartosc sa odrzucane
# (odleglosc kosinusowa: 0 = identyczne, im wiecej, tym mniej podobne).
# Domyslnie wylaczony - najpierw skalibruj go smoke_test.py.
_max_distance = os.environ.get("KM_MAX_DISTANCE", "").strip()
MAX_DISTANCE = float(_max_distance) if _max_distance else None


class SearchEngine:
    def __init__(self):
        self.org = Org()
        self._model = None
        self._collection = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------ zasoby (leniwie, bezpiecznie dla watkow)
    # Uwaga: w serwerze stdio nic nie moze trafic na stdout. Wszystkie nasze komunikaty
    # ida na stderr, a biblioteki (tqdm, logging) tez pisza na stderr.

    @property
    def model(self):
        with self._lock:
            if self._model is None:
                start = time.time()
                print(f"[search] ladowanie modelu {MODEL_NAME} ...", file=sys.stderr, flush=True)
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(MODEL_NAME)
                print(f"[search] model gotowy po {time.time() - start:.1f} s", file=sys.stderr, flush=True)
            return self._model

    @property
    def collection(self):
        with self._lock:
            if self._collection is None:
                import chromadb
                client = chromadb.PersistentClient(path=str(DB_DIR))
                try:
                    self._collection = client.get_collection(COLLECTION_NAME)
                except Exception as exc:
                    raise RuntimeError(
                        f"Brak kolekcji '{COLLECTION_NAME}' w {DB_DIR}. "
                        "Uruchom najpierw: python servers/search/ingest.py"
                    ) from exc
                print(f"[search] baza gotowa: {self._collection.count()} fragmentow",
                      file=sys.stderr, flush=True)
            return self._collection

    def warm_up(self):
        """Laduje baze i model z wyprzedzeniem (wolane w tle przy starcie serwera)."""
        try:
            self.collection
            self.model.encode([QUERY_PREFIX + "rozgrzewka"], normalize_embeddings=True)
            print("[search] rozgrzewka zakonczona", file=sys.stderr, flush=True)
        except Exception as exc:  # serwer ma dzialac nawet gdy rozgrzewka sie nie uda
            print(f"[search] rozgrzewka nieudana: {exc}", file=sys.stderr, flush=True)

    # ------------------------------------------------------------ pracownicy i uprawnienia

    def get_employee(self, employee_id):
        employee = self.org.get_employee(employee_id)
        if employee is None:
            raise ValueError(f"Nie znaleziono pracownika: {employee_id}")
        return employee

    def _acl_filter(self, employee):
        """Filtr Chroma: fragment jest widoczny, gdy jest dla wszystkich albo dla grupy pracownika."""
        return {"$or": [
            {acl_key("all"): True},
            {acl_key(employee["access_group"]): True},
        ]}

    def check_access(self, user_id, doc_id):
        """True, gdy dokument istnieje i pracownik ma do niego dostep."""
        employee = self.get_employee(user_id)
        found = self.collection.get(
            where={"$and": [{"doc_id": doc_id}, self._acl_filter(employee)]},
            limit=1,
            include=[],
        )
        return len(found["ids"]) > 0

    # ------------------------------------------------------------ wyszukiwanie

    def search(self, question, employee_id, n_results=DEFAULT_TOP_K):
        """Zwraca liste slownikow (od najlepszego dopasowania)."""
        employee = self.get_employee(employee_id)
        n_results = max(1, min(int(n_results), MAX_TOP_K))

        embedding = self.model.encode(
            [QUERY_PREFIX + question], normalize_embeddings=True
        ).tolist()

        raw = self.collection.query(
            query_embeddings=embedding,
            n_results=n_results,
            where=self._acl_filter(employee),
            include=["documents", "metadatas", "distances"],
        )

        results = []
        for chunk_id, text, meta, dist in zip(
            raw["ids"][0], raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
        ):
            if MAX_DISTANCE is not None and dist > MAX_DISTANCE:
                continue
            results.append({
                "doc_id": meta["doc_id"],
                "chunk_id": chunk_id,
                "title": meta["title"],
                "source_type": meta["source_type"],
                "section": meta.get("section", ""),
                "department": meta.get("department", ""),
                "doc_type": meta.get("doc_type", ""),
                "status": meta.get("status", ""),
                "last_modified": meta.get("last_modified", ""),
                "distance": round(dist, 4),
                "content": text,
            })
        return results

    # ------------------------------------------------------------ pelny dokument

    def get_document(self, doc_id, employee_id):
        """
        Sklada pelna tresc dokumentu (zgloszenia, watku) z fragmentow.
        Zwraca None, gdy dokument nie istnieje LUB pracownik nie ma dostepu
        (celowo nie rozrozniamy tych przypadkow, zeby nie ujawniac istnienia dokumentu).
        """
        employee = self.get_employee(employee_id)
        raw = self.collection.get(
            where={"$and": [{"doc_id": doc_id}, self._acl_filter(employee)]},
            include=["documents", "metadatas"],
        )
        if not raw["ids"]:
            return None

        chunks = sorted(
            zip(raw["metadatas"], raw["documents"]),
            key=lambda pair: pair[0].get("chunk_index", 0),
        )
        meta = chunks[0][0]
        return {
            "doc_id": meta["doc_id"],
            "title": meta["title"],
            "source_type": meta["source_type"],
            "department": meta.get("department", ""),
            "doc_type": meta.get("doc_type", ""),
            "status": meta.get("status", ""),
            "owner_id": meta.get("owner_id", ""),
            "last_modified": meta.get("last_modified", ""),
            "chunks": len(chunks),
            "content": "\n\n".join(text for _, text in chunks),
        }


if __name__ == "__main__":
    # Szybki test z terminala: python servers/search/search_engine.py "pytanie" E003
    question = sys.argv[1] if len(sys.argv) > 1 else "Jak rozliczac faktury od dostawcow?"
    user = sys.argv[2] if len(sys.argv) > 2 else "E003"
    engine = SearchEngine()
    print(f"\nPytanie: {question}   (uzytkownik: {engine.org.label(user)})\n")
    for r in engine.search(question, user):
        print(f'{r["doc_id"]:5s} d={r["distance"]:.3f}  {r["title"]}  [{r["section"]}]')