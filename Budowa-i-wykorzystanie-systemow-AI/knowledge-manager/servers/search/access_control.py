import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

EMPLOYEES_FILE = BASE_DIR / "data" / "raw" / "employees.csv"
ACL_FILE = BASE_DIR / "data" / "raw" / "acl.csv"


def get_employee(employee_id: str) -> dict:
    with open(EMPLOYEES_FILE, "r", encoding="utf-8-sig", newline="") as file:
        employees = csv.DictReader(file)

        for employee in employees:
            if employee["employee_id"] == employee_id:
                return employee

    raise ValueError(f"Nie znaleziono pracownika: {employee_id}")


def check_access(user_id: str, doc_id: str) -> bool:
    employee = get_employee(user_id)
    employee_role = employee["role_id"]

    with open(ACL_FILE, "r", encoding="utf-8-sig", newline="") as file:
        acl_entries = csv.DictReader(file)

        for entry in acl_entries:
            if entry["doc_id"] == doc_id:
                allowed_roles = [
                    role.strip()
                    for role in entry["allowed_roles"].split(";")
                ]

                return employee_role in allowed_roles

    return False