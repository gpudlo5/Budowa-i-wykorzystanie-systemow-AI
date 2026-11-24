"""
ingest.py - budowa bazy wektorowej ChromaDB z danych Northway Ltd.


Co robi, krok po kroku:
  1. wczytuje dokumenty .md, zgloszenia (tickets.json) i watki (threads.json),
  2. tnie je na fragmenty wielkosci sekcji (ok. 150 slow),
  3. do kazdego fragmentu dolacza metadane, w tym flagi uprawnien acl_*,
  4. zamienia fragmenty na wektory (embeddingi),
  5. zapisuje wszystko do ChromaDB.


"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- konfiguracja
# Model, przedrostek pytania, nazwa kolekcji i sciezki sa w servers/common/config.py
# (wspolne dla ingest.py, search_engine.py i server.py).

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # .../knowledge-manager/servers

from common.config import (  # noqa: E402
     COLLECTION_NAME, DB_DIR, DEFAULT_GROUPS, MAX_SEQ_LENGTH,
    MODEL_NAME, QUERY_PREFIX, TICKET_THREAD_ACL, DATA_DIR as DEFAULT_DATA_DIR,
    acl_key,
)
from common.org import Org  # noqa: E402

# Wielkosc fragmentu: ok. 150 slow to ok. 250-300 tokenow.
DEFAULT_MAX_WORDS = 150

REQUIRED_FRONT_MATTER = [
    "doc_id", "title", "doc_type", "department_id", "owner_id",
    "author_id", "last_modified", "allowed_groups",
]

# ---------------------------------------------------------------- wczytywanie

def read_text(path):
    return Path(path).read_text(encoding="utf-8-sig")


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def find_file(data_dir, name):
    """Szuka pliku w data/ oraz data/documents/ (czesc plikow bywa w obu miejscach)."""
    for folder in (data_dir, data_dir / "documents"):
        candidate = folder / name
        if candidate.exists():
            return candidate
    return None


def parse_front_matter(text):
    """Prosty parser front-matter (bez PyYAML): linie 'klucz: wartosc', listy w [..]."""
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not match:
        raise ValueError("brak front-matter")
    meta = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            meta[key] = [x.strip().strip('"') for x in inner.split(",")] if inner else []
        else:
            meta[key] = value.strip('"')
    return meta, text[match.end():]


# ---------------------------------------------------------------- dzielenie tekstu

def split_long_block(block, max_words):
    """Dzieli zbyt dlugi blok na zdania, a w ostatecznosci na grupy slow."""
    if len(block.split()) <= max_words:
        return [block]
    parts, current = [], []
    for sentence in re.split(r"(?<=[.!?])\s+", block):
        words = sentence.split()
        if len(words) > max_words:                      # pojedyncze zdanie za dlugie
            if current:
                parts.append(" ".join(current))
                current = []
            for i in range(0, len(words), max_words):
                parts.append(" ".join(words[i:i + max_words]))
            continue
        if len(" ".join(current + [sentence]).split()) > max_words and current:
            parts.append(" ".join(current))
            current = []
        current.append(sentence)
    if current:
        parts.append(" ".join(current))
    return parts


def pack_blocks(blocks, max_words):
    """Sklada bloki w fragmenty o dlugosci do max_words slow."""
    chunks, current, count = [], [], 0
    for block in blocks:
        for piece in split_long_block(block, max_words):
            n = len(piece.split())
            if current and count + n > max_words:
                chunks.append("\n".join(current))
                current, count = [], 0
            current.append(piece)
            count += n
    if current:
        chunks.append("\n".join(current))
    return chunks


def markdown_to_sections(body):
    """
    Zwraca liste (naglowek_sekcji, [bloki]).
    Blok = akapit, pozycja listy albo wiersz tabeli zapisany jako 'kolumna: wartosc'.
    """
    sections, heading, blocks = [], "", []
    lines = body.splitlines()
    i = 0
    paragraph = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            blocks.append(" ".join(paragraph))
            paragraph = []

    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("# "):                       # tytul dokumentu - dodajemy osobno
            flush_paragraph()
        elif line.startswith("## "):
            flush_paragraph()
            if blocks:
                sections.append((heading, blocks))
            heading, blocks = line[3:].strip(), []
        elif line.startswith("|"):                      # tabela
            flush_paragraph()
            table = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    table.append(cells)
                i += 1
            if table:
                header, rows = table[0], table[1:]
                for row in rows:
                    blocks.append("; ".join(f"{h}: {c}" for h, c in zip(header, row)))
                if not rows:
                    blocks.append(" | ".join(header))
            continue
        elif re.match(r"(- |\d+\.\s)", line):           # pozycja listy
            flush_paragraph()
            blocks.append(line)
        elif not line.strip():
            flush_paragraph()
        else:
            paragraph.append(line.strip())
        i += 1
    flush_paragraph()
    if blocks:
        sections.append((heading, blocks))
    return sections


# ---------------------------------------------------------------- metadane i ACL

def acl_flags(allowed_groups, groups):
    """Chroma nie przyjmuje list w metadanych, wiec kazda grupa to osobna flaga True/False."""
    flags = {acl_key("all"): "all" in allowed_groups}
    for g in groups:
        flags[acl_key(g)] = g in allowed_groups
    return flags


def load_groups(data_dir):
    return Org(data_dir).groups or DEFAULT_GROUPS


def load_department_names(data_dir):
    return Org(data_dir).department_names()


def load_employee_names(data_dir):
    return {e_id: e["full_name"]for e_id, e in Org(data_dir).employees.items()}


# ---------------------------------------------------------------- budowa fragmentow

def chunk_documents(data_dir, max_words, groups, dept_names, problems):
    docs_dir = data_dir / "documents"
    files = sorted(docs_dir.glob("D*.md"))
    records = []
    seen = set()
    for path in files:
        try:
            meta, body = parse_front_matter(read_text(path))
        except ValueError as e:
            problems.append(f"{path.name}: {e}")
            continue
        missing = [k for k in REQUIRED_FRONT_MATTER if k not in meta]
        if missing:
            problems.append(f"{path.name}: brak pol front-matter: {missing}")
            continue
        doc_id = meta["doc_id"]
        if doc_id in seen:
            problems.append(f"{path.name}: powtorzony doc_id {doc_id}")
            continue
        seen.add(doc_id)
        allowed = meta["allowed_groups"]
        unknown = [g for g in allowed if g != "all" and g not in groups]
        if unknown:
            problems.append(f"{path.name}: nieznane grupy dostepu {unknown}")

        base_meta = {
            "doc_id": doc_id,
            "source_type": "document",
            "title": meta["title"],
            "department": dept_names.get(meta["department_id"], meta["department_id"]),
            "doc_type": meta["doc_type"],
            "status": "active",
            "owner_id": meta["owner_id"],
            "author_id": meta["author_id"],
            "last_modified": meta["last_modified"],
            "process_id": meta.get("process_id", ""),
            **acl_flags(allowed, groups),
        }
        index = 0
        for heading, blocks in markdown_to_sections(body):
            prefix = f'{meta["title"]} - {heading}' if heading else meta["title"]
            for piece in pack_blocks(blocks, max_words):
                records.append({
                    "id": f"{doc_id}#{index}",
                    "text": f"{prefix}\n{piece}",
                    "meta": {**base_meta, "section": heading, "chunk_index": index},
                })
                index += 1
    return records


def chunk_tickets(data_dir, groups, dept_names, names, problems):
    path = find_file(data_dir, "tickets.json")
    if not path:
        problems.append("brak tickets.json - zgloszenia pominiete")
        return []
    records = []
    for t in json.loads(read_text(path)):
        parts = [
            f'Zgloszenie {t["ticket_id"]}: {t["title"]}.',
            t["description"],
        ]
        if t.get("resolution"):
            parts.append(f'Rozwiazanie: {t["resolution"]}')
        if t.get("counterparty"):
            parts.append(f'Kontrahent: {t["counterparty"]}.')
        parts.append(f'Status: {t["status"]}. Zglosil: {names.get(t["reporter_id"], t["reporter_id"])}, '
                     f'realizuje: {names.get(t["assignee_id"], t["assignee_id"])}.')
        date = (t.get("resolved_at") or t["created_at"])[:10]
        records.append({
            "id": f'{t["ticket_id"]}#0',
            "text": "\n".join(parts),
            "meta": {
                "doc_id": t["ticket_id"], "source_type": "ticket",
                "title": t["title"], "department": t["category"],
                "doc_type": "ticket", "status": t["status"],
                "owner_id": t["assignee_id"], "author_id": t["reporter_id"],
                "last_modified": date, "process_id": t.get("process_id") or "",
                "section": "", "chunk_index": 0,
                **acl_flags(TICKET_THREAD_ACL, groups),
            },
        })
    return records


def chunk_threads(data_dir, max_words, groups, names, problems):
    path = find_file(data_dir, "threads.json")
    if not path:
        problems.append("brak threads.json - watki pominiete")
        return []
    records = []
    for th in json.loads(read_text(path)):
        lines = [f'{names.get(m["author_id"], m["author_id"])}: {m["text"]}' for m in th["messages"]]
        prefix = f'Watek {th["thread_id"]} na kanale {th["channel"]}: {th["topic"]}'
        for i, piece in enumerate(pack_blocks(lines, max_words)):
            records.append({
                "id": f'{th["thread_id"]}#{i}',
                "text": f"{prefix}\n{piece}",
                "meta": {
                    "doc_id": th["thread_id"], "source_type": "thread",
                    "title": th["topic"], "department": th["channel"],
                    "doc_type": "thread", "status": "active",
                    "owner_id": th["messages"][0]["author_id"],
                    "author_id": th["messages"][0]["author_id"],
                    "last_modified": th["started_at"][:10], "process_id": "",
                    "section": "", "chunk_index": i,
                    **acl_flags(TICKET_THREAD_ACL, groups),
                },
            })
    return records


def build_records(data_dir, max_words):
    problems = []
    groups = load_groups(data_dir)
    dept_names = load_department_names(data_dir)
    names = load_employee_names(data_dir)
    records = []
    records += chunk_documents(data_dir, max_words, groups, dept_names, problems)
    records += chunk_tickets(data_dir, groups, dept_names, names, problems)
    records += chunk_threads(data_dir, max_words, groups, names, problems)
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        problems.append("powtorzone identyfikatory fragmentow")
    return records, problems


# ---------------------------------------------------------------- zapis do ChromaDB

def write_to_chroma(records, batch_size=16):
    # Importy dopiero tutaj, zeby --dry-run dzialal bez zainstalowanych bibliotek.
    import chromadb
    from sentence_transformers import SentenceTransformer

    print(f"Ladowanie modelu {MODEL_NAME} (pierwsze uruchomienie pobiera kilka GB) ...")
    model = SentenceTransformer(MODEL_NAME)
    # Ograniczamy dlugosc, zeby nie zuzywac niepotrzebnie pamieci (nasze fragmenty sa krotkie).
    model.max_seq_length = min(getattr(model, "max_seq_length", None) or MAX_SEQ_LENGTH, MAX_SEQ_LENGTH)

    texts = [r["text"] for r in records]
    limit = model.max_seq_length
    lengths = [len(x) for x in model.tokenizer(texts, add_special_tokens=True)["input_ids"]]
    too_long = [(r["id"], n) for r, n in zip(records, lengths) if n > limit]
    print(f"Tokeny: srednio {sum(lengths)/len(lengths):.0f}, max {max(lengths)}, limit modelu {limit}.")
    if too_long:
        print(f"UWAGA: {len(too_long)} fragmentow przekracza limit i zostanie obcietych, np. {too_long[:5]}.")
        print("       Zmniejsz --max-words (np. 100) i uruchom ponownie.")

    DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)       # budujemy od zera, zeby nie zostawac ze starymi danymi
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        # Fragmenty (passages) koduje sie BEZ przedrostka - przedrostek jest tylko dla pytan.
        embeddings = model.encode(
            [r["text"] for r in batch], normalize_embeddings=True
        ).tolist()
        collection.upsert(
            ids=[r["id"] for r in batch],
            documents=[r["text"] for r in batch],
            embeddings=embeddings,
            metadatas=[r["meta"] for r in batch],
        )
        print(f"  zapisano {min(start + batch_size, len(records))}/{len(records)}")
    print(f"Gotowe: {collection.count()} fragmentow w kolekcji '{COLLECTION_NAME}' ({DB_DIR}).")


# ---------------------------------------------------------------- statystyki i uruchomienie

def print_stats(records, problems):
    by_type = {}
    for r in records:
        by_type.setdefault(r["meta"]["source_type"], []).append(r)
    print("Fragmenty wg zrodla:")
    for kind, items in by_type.items():
        docs = len({r["meta"]["doc_id"] for r in items})
        words = [len(r["text"].split()) for r in items]
        print(f"  {kind:9s} zrodel: {docs:3d}  fragmentow: {len(items):4d}  "
              f"slow/fragment: sr. {sum(words)/len(words):.0f}, max {max(words)}")
    restricted = [r for r in records if not r["meta"][acl_key("all")]]
    print(f"Fragmenty z ograniczonym dostepem (bez acl_all): {len(restricted)}")
    if problems:
        print("\nPROBLEMY:")
        for p in problems:
            print("  -", p)


def main():
    parser = argparse.ArgumentParser(description="Ingestia danych do ChromaDB")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    parser.add_argument("--dry-run", action="store_true", help="bez modelu i bazy")
    parser.add_argument("--show", metavar="ID", help="pokaz fragmenty dokumentu (np. D004) i zakoncz")
    args = parser.parse_args()

    records, problems = build_records(args.data_dir, args.max_words)

    if args.show:
        for r in records:
            if r["meta"]["doc_id"] == args.show:
                print(f'--- {r["id"]}  ({len(r["text"].split())} slow)  acl={[k for k,v in r["meta"].items() if k.startswith("acl_") and v]}')
                print(r["text"])
        return

    print_stats(records, problems)
    if not records:
        sys.exit("Brak danych do indeksowania.")
    if problems and any("front-matter" in p or "powtorzony" in p for p in problems):
        sys.exit("Popraw problemy z dokumentami przed ingestia.")
    if args.dry_run:
        print("\nTryb --dry-run: nic nie zapisano.")
        return
    write_to_chroma(records)


if __name__ == "__main__":
    main()
