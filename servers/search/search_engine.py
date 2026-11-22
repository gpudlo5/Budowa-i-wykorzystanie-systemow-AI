import csv
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "data" / "raw" / "documents.csv"
EMPLOYEES_FILE = BASE_DIR / "data" / "raw" / "employees.csv"
ACL_FILE = BASE_DIR / "data" / "raw" / "acl.csv"
DB_DIR = BASE_DIR / "data" / "processed" / "chroma_db"

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

    def load_csv(self, file_path):
        with open(file_path, "r", encoding="utf-8-sig") as file:
            return list(csv.DictReader(file))

    def load_documents(self):
        return self.load_csv(DATA_FILE)

    def get_employee(self, employee_id):
        employees = self.load_csv(EMPLOYEES_FILE)

        employee = next(
            (
                employee
                for employee in employees
                if employee["employee_id"] == employee_id
            ),
            None,
        )

        if employee is None:
            raise ValueError(
                f"Nie znaleziono pracownika: {employee_id}"
            )

        return employee

    def check_access(self, user_id, doc_id):
        """
        Sprawdza, czy pracownik ma dostęp do wskazanego dokumentu
        na podstawie roli i pliku ACL.
        """
        employee = self.get_employee(user_id)
        employee_role = employee["role_id"]

        acl_entries = self.load_csv(ACL_FILE)

        for entry in acl_entries:
            if entry["doc_id"] == doc_id:
                allowed_roles = [
                    role.strip()
                    for role in entry["allowed_roles"].split(";")
                ]

                return employee_role in allowed_roles

        return False

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
        # Najpierw sprawdzamy, czy pracownik istnieje.
        self.get_employee(employee_id)

        # Pobieramy dokumenty, do których pracownik ma dostęp.
        documents = self.load_documents()

        allowed_doc_ids = [
            doc["doc_id"]
            for doc in documents
            if self.check_access(employee_id, doc["doc_id"])
        ]

        if not allowed_doc_ids:
            return []

        query_embedding = self.model.encode([question]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where={
                "doc_id": {"$in": allowed_doc_ids}
            },
        )

        return results


if __name__ == "__main__":
    engine = SearchEngine()
    engine.index_documents()

    question = "Jak rozliczac faktury od dostawcow?"
    results = engine.search(question, employee_id="E002")

    print("\nWYNIKI WYSZUKIWANIA:\n")

    if results and results.get("documents") and results["documents"][0]:
        for document, metadata in zip(
            results["documents"][0],
            results["metadatas"][0],
        ):
            print(f"Tytul: {metadata['title']}")
            print(f"Tresc: {document}")
            print("-" * 50)