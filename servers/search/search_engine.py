
import csv
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# Sciezki projektu
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "data" / "raw" / "documents.csv"
DB_DIR = BASE_DIR / "data" / "processed" / "chroma_db"

# Model embeddingowy
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class SearchEngine:
    def __init__(self):
        print("Ladowanie modelu embeddingowego...")
        self.model = SentenceTransformer(MODEL_NAME)

        print("Uruchamianie bazy ChromaDB...")
        self.client = chromadb.PersistentClient(path=str(DB_DIR))

        self.collection = self.client.get_or_create_collection(
            name="company_documents"
        )

    def load_documents(self):
        with open(DATA_FILE, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            documents = list(reader)

        return documents

    def index_documents(self):
        documents = self.load_documents()

        if not documents:
            print("Brak dokumentow do indeksowania.")
            return

        ids = [doc["doc_id"] for doc in documents]
        texts = [doc["content"] for doc in documents]

        metadatas = [
            {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "department": doc["department"],
                "doc_type": doc["doc_type"],
                "status": doc["status"],
            }
            for doc in documents
        ]

        embeddings = self.model.encode(texts).tolist()

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        print(f"Zindeksowano dokumentow: {len(documents)}")


    def search(self, question, employee_id, n_results=3):
        # Wczytanie pracownikow
        employees_file = BASE_DIR / "data" / "raw" / "employees.csv"

        with open(employees_file, "r", encoding="utf-8-sig") as file:
            employees = list(csv.DictReader(file))

        employee = next(
            (e for e in employees if e["employee_id"] == employee_id),
            None
        )

        if employee is None:
            raise ValueError("Nie znaleziono pracownika.")

        employee_role = employee["role_id"]

        # Wczytanie uprawnien dokumentow
        acl_file = BASE_DIR / "data" / "raw" / "acl.csv"

        with open(acl_file, "r", encoding="utf-8-sig") as file:
            acl_entries = list(csv.DictReader(file))

        allowed_doc_ids = [
            entry["doc_id"]
            for entry in acl_entries
            if employee_role in entry["allowed_roles"].split(";")
        ]

        if not allowed_doc_ids:
            return []

        # Wyszukiwanie semantyczne tylko w dokumentach dostepnych dla pracownika
        query_embedding = self.model.encode([question]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where={
                "doc_id": {"$in": allowed_doc_ids}
            }
        )

        return results



if __name__ == "__main__":
    engine = SearchEngine()
    engine.index_documents()

    question = "Jak rozliczac faktury od dostawcow?"
    results = engine.search(question, employee_id="E002")

    print("\nWYNIKI WYSZUKIWANIA:\n")

    for document, metadata in zip(
        results["documents"][0],
        results["metadatas"][0],
    ):
        print(f"Tytul: {metadata['title']}")
        print(f"Tresc: {document}")
        print("-" * 50)
