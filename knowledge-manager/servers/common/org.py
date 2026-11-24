"""
org.py - wspolny loader danych o organizacji (pracownicy, dzialy, role, grupy).

Laczy employees.csv z departments.csv i roles.csv, zeby kazdy serwer dostawal
gotowy rekord pracownika: imie, nazwisko, dzial, stanowisko, przelozony, grupa
dostepu. Uzywaja go Search MCP (uprawnienia, audyt) i Handover MCP.

Tylko biblioteka standardowa.
"""

import csv
from pathlib import Path

from .config import DATA_DIR, DEFAULT_GROUPS


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class Org:
    """Wczytuje dane firmy raz i udostepnia proste zapytania."""

    def __init__(self, data_dir: Path | str = DATA_DIR):
        self.data_dir = Path(data_dir)
        self.departments = {r["department_id"]: r for r in _read_csv(self.data_dir / "departments.csv")}
        self.roles = {r["role_id"]: r for r in _read_csv(self.data_dir / "roles.csv")}
        groups = [r["access_group"] for r in _read_csv(self.data_dir / "access_groups.csv")]
        self.groups: list[str] = groups or list(DEFAULT_GROUPS)

        self.employees: dict[str, dict] = {}
        for r in _read_csv(self.data_dir / "employees.csv"):
            dept = self.departments.get(r["department_id"], {})
            role = self.roles.get(r["role_id"], {})
            self.employees[r["employee_id"]] = {
                "employee_id": r["employee_id"],
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "full_name": f'{r["first_name"]} {r["last_name"]}',
                "email": r["email"],
                "department_id": r["department_id"],
                "department": dept.get("name", ""),
                "role_id": r["role_id"],
                "role": role.get("role_name", ""),
                "manager_id": r["manager_id"] or None,
                "hire_date": r["hire_date"],
                "status": r["status"],
                "end_date": r["end_date"] or None,
                "access_group": r["access_group"],
            }

    # ----------------------------------------------------------- pracownicy

    def get_employee(self, employee_id: str) -> dict | None:
        return self.employees.get(employee_id)

    def find_employees(self, query: str) -> list[dict]:
        """Szukanie po fragmencie imienia, nazwiska, e-maila lub stanowiska."""
        q = query.strip().lower()
        return [
            e for e in self.employees.values()
            if q in e["full_name"].lower() or q in e["email"].lower() or q in e["role"].lower()
        ]

    def name_of(self, employee_id: str | None) -> str:
        """Imie i nazwisko do cytowania; dla nieznanego ID zwraca samo ID."""
        if not employee_id:
            return ""
        e = self.employees.get(employee_id)
        return e["full_name"] if e else employee_id

    def label(self, employee_id: str | None) -> str:
        """'Anna Kowalska (Glowna Ksiegowa, Ksiegowosc)' - czytelny podpis osoby."""
        e = self.employees.get(employee_id or "")
        if not e:
            return employee_id or ""
        return f'{e["full_name"]} ({e["role"]}, {e["department"]})'

    def departing(self) -> list[dict]:
        """Pracownicy ze statusem 'odchodzacy' (kandydaci do przekazania wiedzy)."""
        return [e for e in self.employees.values() if e["status"] == "odchodzący"]

    def reports_of(self, manager_id: str) -> list[dict]:
        return [e for e in self.employees.values() if e["manager_id"] == manager_id]

    # ----------------------------------------------------------- uprawnienia

    def access_group_of(self, employee_id: str) -> str | None:
        e = self.employees.get(employee_id)
        return e["access_group"] if e else None

    def department_names(self) -> dict[str, str]:
        return {d_id: d["name"] for d_id, d in self.departments.items()}
